# -*- Python Version: 3.10 -*-

"""Value tests against the private corpus (client workbooks under '_private/', gitignored).

Skipped wholesale when the folder is absent. See '_private/MANIFEST.md' for what is there.
"""

import pathlib

import pytest

from PHX.from_PHPP import Flavour, FreshnessVerdict, RefusalReason, read_results, sniff_path
from PHX.from_PHPP.results import ValueStatus

PRIVATE = pathlib.Path(__file__).parent / "_private"
PROJECT_WORKBOOKS = sorted(p for p in PRIVATE.glob("*.xlsx") if not p.name.startswith(("PHPP_EN", "Heat_Pump", "derived_")))
pytestmark = pytest.mark.skipif(not PRIVATE.is_dir() or not PROJECT_WORKBOOKS, reason="private corpus not present")


@pytest.mark.parametrize("path", PROJECT_WORKBOOKS, ids=lambda p: p.name)
def test_project_workbook_reads_fresh_with_every_value_sourced(path: pathlib.Path) -> None:
    r = read_results(path)
    assert r.ok, r.report.summary()
    rec = r.record
    assert rec is not None
    assert rec.identity.version_key == "EN_10_6" and rec.identity.flavour is Flavour.PROJECT
    assert rec.freshness.verdict is FreshnessVerdict.FRESH, rec.freshness.evidence
    assert not r.report.unread, r.report.summary()
    for rv in rec.values.values():
        assert rv.status in (ValueStatus.OK, ValueStatus.NOT_APPLICABLE), rv
        assert rv.label_as_read
    # -- exactly one of cooling demand / overheating frequency applies per PHPP's AB30 switch
    statuses = {rec.values["cooling_demand"].status, rec.values["overheating_frequency"].status}
    assert statuses == {ValueStatus.OK, ValueStatus.NOT_APPLICABLE}
    assert float(rec.get("tfa")) > 0  # type: ignore[arg-type]
    assert rec.values["heating_demand"].unit == "kWh/(m²a)"
    assert rec.values["site_energy_demand"].unit == "MWh/a"


def test_blank_template_and_heat_pump_tool_refuse_by_name() -> None:
    blank = PRIVATE / "PHPP_EN_V10.6_Empty.xlsx"
    tool = PRIVATE / "Heat_Pump_Tool_PHPP_10_v24.04.xlsx"
    if blank.is_file():
        s = sniff_path(blank)
        assert s.identity is not None and s.identity.flavour is Flavour.BLANK_TEMPLATE
        assert read_results(blank).refusal.reason is RefusalReason.BLANK_TEMPLATE  # type: ignore[union-attr]
    if tool.is_file():
        assert read_results(tool).refusal.reason is RefusalReason.NOT_A_PHPP  # type: ignore[union-attr]


@pytest.mark.parametrize(
    "name, expected",
    [
        ("derived_260818_calcmode_manual.xlsx", FreshnessVerdict.SUSPECT),
        ("derived_260818_fullcalconload.xlsx", FreshnessVerdict.SUSPECT),
        ("derived_260818_per_cache_stripped.xlsx", FreshnessVerdict.SUSPECT),
    ],
)
def test_derived_stale_copies_flip_to_suspect_and_still_return_values(name: str, expected: FreshnessVerdict) -> None:
    p = PRIVATE / name
    if not p.is_file():
        pytest.skip(f"{name} not present")
    r = read_results(p)
    assert r.ok and r.record is not None
    assert r.record.freshness.verdict is expected, r.record.freshness.evidence
    assert r.record.get("heating_demand") is not None


@pytest.mark.parametrize("name", ["derived_260818_openpyxl_resave.xlsx", "derived_260818_results_cache_stripped.xlsx"])
def test_derived_uncached_copies_refuse_results_region_empty(name: str) -> None:
    p = PRIVATE / name
    if not p.is_file():
        pytest.skip(f"{name} not present")
    r = read_results(p)
    assert r.refusal is not None and r.refusal.reason is RefusalReason.RESULTS_REGION_EMPTY
    assert r.identity is not None and r.identity.flavour is Flavour.PROJECT
