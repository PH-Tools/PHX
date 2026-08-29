# -*- Python Version: 3.10 -*-

import pathlib
import re
import zipfile

from PHX.from_PHPP import FreshnessVerdict
from PHX.from_PHPP.results_map import RESULTS_MAP_EN_10_6
from PHX.from_PHPP.staleness import _has_cached_value, assess, read_package_signals
from tests.test_from_PHPP import phpp_shaped


def _rewrite_calcpr(src: pathlib.Path, dst: pathlib.Path, attrs: str) -> pathlib.Path:
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "xl/workbook.xml":
                s = data.decode("utf-8")
                s = re.sub(r"<calcPr[^>]*/>", f"<calcPr {attrs}/>", s)
                data = s.encode("utf-8")
            zout.writestr(item, data)
    return dst


def test_has_cached_value_rules() -> None:
    assert _has_cached_value(None, "<f>A1</f><v>12.5</v>")
    assert _has_cached_value("str", "<f>A1</f><v>-</v>")
    assert _has_cached_value("str", "<f>A1</f><v/>")  # Excel: formula returned ""
    assert not _has_cached_value(None, "<f>A1</f><v></v>")  # openpyxl: never calculated
    assert not _has_cached_value(None, "<f>A1</f>")  # no value element at all


def test_package_signals_from_openpyxl_written_file(tmp_path: pathlib.Path) -> None:
    p = phpp_shaped.write_project(tmp_path / "p.xlsx")
    sig = read_package_signals(p)
    assert "openpyxl" in str(sig["application"]).lower()
    assert sig["full_calc_on_load"] == "1"
    assert sig["calc_mode"] == "auto"


def test_assess_plain_values_is_suspect_writer_only(tmp_path: pathlib.Path) -> None:
    p = phpp_shaped.write_project(tmp_path / "p.xlsx")
    f = assess(p, RESULTS_MAP_EN_10_6)
    assert f.verdict is FreshnessVerdict.SUSPECT
    assert f.signals["n_formula"] == 0
    assert any("not Excel" in e for e in f.evidence) and any("fullCalcOnLoad" in e for e in f.evidence)


def test_assess_formulas_without_cache_is_empty(tmp_path: pathlib.Path) -> None:
    p = phpp_shaped.write_project(tmp_path / "f.xlsx", as_formulas=True)
    f = assess(p, RESULTS_MAP_EN_10_6)
    assert f.verdict is FreshnessVerdict.EMPTY
    assert f.signals["n_formula"] > 0 and f.signals["n_formula_cached"] == 0
    assert "heating_demand" in f.signals["formula_without_cache"]


def test_assess_calc_mode_manual_is_suspect(tmp_path: pathlib.Path) -> None:
    src = phpp_shaped.write_project(tmp_path / "p.xlsx")
    p = _rewrite_calcpr(src, tmp_path / "manual.xlsx", 'calcId="191029" calcMode="manual"')
    f = assess(p, RESULTS_MAP_EN_10_6)
    assert f.verdict is FreshnessVerdict.SUSPECT
    assert any("manual" in e for e in f.evidence)


def test_assess_missing_parts_do_not_raise(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "junk.xlsx"
    p.write_bytes(b"not a zip")
    sig = read_package_signals(p)
    assert sig["application"] is None and sig["calc_mode"] is None
