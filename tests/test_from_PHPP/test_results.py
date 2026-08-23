# -*- Python Version: 3.10 -*-

import pathlib

from PHX.from_PHPP import FreshnessVerdict, RefusalReason, read_results
from PHX.from_PHPP.results import ValueStatus
from PHX.from_PHPP.results_map import RESULTS_MAP_EN_10_6, resolve_map
from tests.test_from_PHPP import phpp_shaped


def test_map_keys_are_unique_and_cover_the_adr_set() -> None:
    keys = [s.key for s in RESULTS_MAP_EN_10_6]
    assert len(keys) == len(set(keys))
    for required in (
        "energy_standard",
        "class_pe_method",
        "tfa",
        "heating_demand",
        "heating_load",
        "cooling_demand",
        "cooling_load",
        "overheating_frequency",
        "n50",
        "pe_demand",
        "per_demand",
        "per_demand_without_bioenergy",
        "renewable_generation",
        "site_energy_demand",
    ):
        assert required in keys


def test_resolve_map_verified_assumed_unsupported() -> None:
    assert resolve_map("EN_10_6") is not None and resolve_map("EN_10_6").verified  # type: ignore[union-attr]
    assert resolve_map("EN_10_4A") is not None and not resolve_map("EN_10_4A").verified  # type: ignore[union-attr]
    assert resolve_map("EN_9_7") is None
    assert resolve_map("EN_10_6IP") is None


def test_read_project_every_value_carries_source_and_caption(tmp_path: pathlib.Path) -> None:
    r = read_results(phpp_shaped.write_project(tmp_path / "proj.xlsx"))
    assert r.ok and r.record is not None
    rec = r.record
    assert rec.map_version_key == "EN_10_6" and rec.map_verified
    assert rec.get("heating_demand") == 14.5
    assert rec.get("tfa") == 123.4
    assert rec.get("energy_standard") == "10-Passive House"
    hd = rec.values["heating_demand"]
    assert hd.source == "Verification!I36" and hd.unit == "kWh/(m²a)" and hd.label_as_read == "Heating demand"
    assert rec.values["cooling_load"].source == "Cooling load!Q67"
    assert rec.values["per_demand_without_bioenergy"].source == "PER!V65"
    # -- '-' is not-applicable, not empty
    assert rec.values["cooling_demand"].status is ValueStatus.NOT_APPLICABLE
    assert "cooling_demand" in r.report.not_applicable
    assert rec.get("cooling_demand") is None
    assert not r.report.unread
    # -- an openpyxl-written file is not an Excel-saved file: flagged, still returned
    assert rec.freshness.verdict is FreshnessVerdict.SUSPECT
    assert any("not Excel" in e for e in rec.freshness.evidence)


def test_read_blank_template_refuses_with_identity(tmp_path: pathlib.Path) -> None:
    r = read_results(phpp_shaped.write_blank(tmp_path / "blank.xlsx"))
    assert not r.ok and r.refusal is not None
    assert r.refusal.reason is RefusalReason.BLANK_TEMPLATE
    assert r.identity is not None and r.identity.version_key == "EN_10_6"
    assert r.report.summary().startswith("blank.xlsx: Refused (blank_template)")


def test_read_uncached_formulas_refuses_results_region_empty(tmp_path: pathlib.Path) -> None:
    r = read_results(phpp_shaped.write_project(tmp_path / "uncached.xlsx", as_formulas=True))
    assert not r.ok and r.refusal is not None
    assert r.refusal.reason is RefusalReason.RESULTS_REGION_EMPTY
    assert r.identity is not None
    assert any("verdict EMPTY" in n for n in r.report.notes)


def test_read_moved_caption_is_label_mismatch_not_a_value(tmp_path: pathlib.Path) -> None:
    r = read_results(phpp_shaped.write_project(tmp_path / "moved.xlsx", move_caption="heating_demand"))
    assert r.ok and r.record is not None
    hd = r.record.values["heating_demand"]
    assert hd.status is ValueStatus.LABEL_MISMATCH and hd.value is None
    assert hd.label_as_read == "Something else"
    assert [u.name for u in r.report.unread] == ["heating_demand"]
    assert r.record.get("heating_demand") is None
    assert r.record.get("heating_load") == 9.8


def test_read_missing_sheet_is_named(tmp_path: pathlib.Path) -> None:
    r = read_results(phpp_shaped.write_project(tmp_path / "nocl.xlsx", drop_sheet="Cooling load"))
    assert r.ok and r.record is not None
    assert r.record.values["cooling_load"].status is ValueStatus.SHEET_MISSING
    assert any(u.name == "cooling_load" and "sheet_missing" in u.reason for u in r.report.unread)


def test_read_unsupported_version_refuses_by_name(tmp_path: pathlib.Path) -> None:
    r = read_results(phpp_shaped.write_version(tmp_path / "v9.xlsx", "9.7", "EN "))
    assert r.refusal is not None and r.refusal.reason is RefusalReason.VERSION_UNSUPPORTED
    assert "EN_9_7" in r.refusal.detail and r.identity is not None


def test_read_assumed_version_is_noted(tmp_path: pathlib.Path) -> None:
    r = read_results(phpp_shaped.write_version(tmp_path / "v104.xlsx", "10.4a", "EN "))
    assert r.ok and r.record is not None and not r.record.map_verified
    assert any("assumed" in n for n in r.report.notes)


def test_read_not_a_phpp_and_not_a_workbook_and_not_a_file(tmp_path: pathlib.Path) -> None:
    assert read_results(phpp_shaped.write_not_a_phpp(tmp_path / "t.xlsx")).refusal.reason is RefusalReason.NOT_A_PHPP  # type: ignore[union-attr]
    junk = tmp_path / "junk.xlsx"
    junk.write_bytes(b"PK\x03\x04 not really")
    assert read_results(junk).refusal.reason is RefusalReason.NOT_A_WORKBOOK  # type: ignore[union-attr]
    assert read_results(tmp_path / "nope.xlsx").refusal.reason is RefusalReason.NOT_A_FILE  # type: ignore[union-attr]
