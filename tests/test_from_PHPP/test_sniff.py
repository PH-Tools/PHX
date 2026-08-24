# -*- Python Version: 3.10 -*-

import pathlib

import pytest

from PHX.from_PHPP import Flavour, RefusalReason, sniff_path
from tests.test_from_PHPP import phpp_shaped


def test_sniff_project(tmp_path: pathlib.Path) -> None:
    p = phpp_shaped.write_project(tmp_path / "proj.xlsx")
    r = sniff_path(p)
    assert r.ok and r.identity is not None
    assert r.identity.version_key == "EN_10_6"
    assert r.identity.version_label == "PHPP 10.6 EN"
    assert r.identity.flavour is Flavour.PROJECT
    assert r.identity.language_cell_present
    assert r.evidence["version_row"] == 5


def test_sniff_blank_template(tmp_path: pathlib.Path) -> None:
    r = sniff_path(phpp_shaped.write_blank(tmp_path / "blank.xlsx"))
    assert r.ok and r.identity is not None
    assert r.identity.flavour is Flavour.BLANK_TEMPLATE
    assert r.evidence["tfa"] == 0
    assert r.evidence["climate_is_template_default"] is True


def test_sniff_project_by_inputs_only_when_tfa_uncached(tmp_path: pathlib.Path) -> None:
    # -- no cached TFA (None) but dwelling units + a chosen climate: still a project
    p = phpp_shaped.write_project(tmp_path / "proj.xlsx", values={"heating_demand": 1.0})
    r = sniff_path(p)
    assert r.identity is not None and r.identity.flavour is Flavour.PROJECT
    assert r.evidence["tfa"] is None


def test_sniff_not_a_phpp(tmp_path: pathlib.Path) -> None:
    r = sniff_path(phpp_shaped.write_not_a_phpp(tmp_path / "tool.xlsx"))
    assert not r.ok and r.refusal is not None
    assert r.refusal.reason is RefusalReason.NOT_A_PHPP
    assert "DATA" in r.refusal.detail


def test_sniff_not_a_workbook(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "renamed.xlsx"
    p.write_text("this is not a zip")
    r = sniff_path(p)
    assert r.refusal is not None and r.refusal.reason is RefusalReason.NOT_A_WORKBOOK


def test_sniff_not_a_file(tmp_path: pathlib.Path) -> None:
    r = sniff_path(tmp_path / "missing.xlsx")
    assert r.refusal is not None and r.refusal.reason is RefusalReason.NOT_A_FILE


def test_sniff_phpp9_layout_language_from_pe_factor_proxy(tmp_path: pathlib.Path) -> None:
    r = sniff_path(phpp_shaped.write_version(tmp_path / "v9.xlsx", "9.6a", None))
    assert r.identity is not None
    assert r.identity.version_key == "EN_9_6A" and not r.identity.language_cell_present
    assert r.evidence["language_from_pe_factor_proxy"] is True


def test_sniff_easyph_variant_normalises_to_the_base_version(tmp_path: pathlib.Path) -> None:
    r = sniff_path(phpp_shaped.write_version(tmp_path / "ez.xlsx", "10.6 easyPHv3", "EN "))
    assert r.identity is not None
    assert r.identity.version_key == "EN_10_6" and r.identity.variant == "easyPHv3"
    assert r.identity.version_label == "PHPP 10.6 EN (easyPHv3)"


def test_sniff_garbage_version_is_unreadable(tmp_path: pathlib.Path) -> None:
    r = sniff_path(phpp_shaped.write_version(tmp_path / "g.xlsx", "ten point six", "EN "))
    assert r.refusal is not None and r.refusal.reason is RefusalReason.VERSION_UNREADABLE


@pytest.mark.parametrize("version, key", [("10.4a", "EN_10_4A"), ("10.3", "EN_10_3"), ("9.7", "EN_9_7")])
def test_sniff_version_key_follows_phx_shape_naming(tmp_path: pathlib.Path, version: str, key: str) -> None:
    r = sniff_path(phpp_shaped.write_version(tmp_path / "v.xlsx", version, "EN "))
    assert r.identity is not None and r.identity.version_key == key
