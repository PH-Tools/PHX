# -*- Python Version: 3.10 -*-

"""Stale-cache signals: can the cached values in a closed PHPP be trusted?

A closed .xlsx carries the values Excel last wrote next to each formula. If the
file was last saved by something that does not calculate (openpyxl, some
converters), or with calculation set to manual, or with a 'recalculate on load'
flag, those cached values may be absent or behind the inputs. The reader cannot
recalculate (no Excel), so it reports what it can observe and a verdict; values
from a 'suspect' workbook are still returned, flagged (Pholio ADR-017 §5).

Observable signals, from the package itself:
  * 'docProps/core.xml'  -> lastModifiedBy, modified            (openpyxl 'properties')
  * 'docProps/app.xml'   -> Application, AppVersion             (zip part, read directly)
  * 'xl/workbook.xml'    -> <calcPr calcMode= fullCalcOnLoad=>  (zip part, read directly)
  * the results cells    -> formula present but no '<v>' cached value (raw sheet XML)
"""

from __future__ import annotations

import datetime
import enum
import pathlib
import re
import zipfile
from dataclasses import dataclass, field
from typing import Any

from PHX.from_PHPP.results_map import ResultCellSpec
from PHX.from_PHPP.xl_openpyxl import OpenpyxlWorkbook


class FreshnessVerdict(enum.Enum):
    """The reader's verdict on the cached values.

    Values:
        FRESH: Last saved by Excel, automatic calculation, no recalc-on-load flag, results cached.
        SUSPECT: Something observable says the cache may be behind (manual calc, recalc flag, non-Excel writer).
        EMPTY: The results cells carry formulas but no cached values at all — nothing to read.
    """

    FRESH = "fresh"
    SUSPECT = "suspect"
    EMPTY = "empty"


@dataclass
class Freshness:
    """Verdict plus the evidence it rests on.

    Attributes:
        verdict (FreshnessVerdict): fresh / suspect / empty.
        evidence (list[str]): Human-readable observations, one per signal.
        signals (dict[str, Any]): The raw observations (application, calc_mode, ...), for tests and tables.
    """

    verdict: FreshnessVerdict
    evidence: list[str] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)


_CALC_PR = re.compile(r"<calcPr\b([^>]*)/?>")
# -- Excel's own Application strings. openpyxl writes 'Microsoft Excel Compatible / Openpyxl x.y'
# -- (which contains 'Excel' — hence a strict match, not a substring test).
_EXCEL_APP = re.compile(r"^Microsoft( Macintosh)? Excel( Online)?$")
_ATTR = re.compile(r'(\w+)="([^"]*)"')


def read_package_signals(path: pathlib.Path) -> dict[str, Any]:
    """Read the writer/calculation signals straight from the .xlsx zip parts.

    Arguments:
    ----------
        * path: (pathlib.Path) The workbook.

    Returns:
    --------
        * (dict[str, Any]): keys 'application', 'app_version', 'calc_mode', 'full_calc_on_load',
            'calc_id', 'file_mtime'. Missing parts yield None values, never an exception.
    """
    out: dict[str, Any] = {
        "application": None,
        "app_version": None,
        "calc_mode": None,
        "full_calc_on_load": None,
        "calc_id": None,
        "file_mtime": datetime.datetime.fromtimestamp(path.stat().st_mtime),
    }
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            if "docProps/app.xml" in names:
                app = z.read("docProps/app.xml").decode("utf-8", "replace")
                m = re.search(r"<Application>([^<]*)</Application>", app)
                out["application"] = m.group(1) if m else None
                m = re.search(r"<AppVersion>([^<]*)</AppVersion>", app)
                out["app_version"] = m.group(1) if m else None
            if "xl/workbook.xml" in names:
                wbxml = z.read("xl/workbook.xml").decode("utf-8", "replace")
                m = _CALC_PR.search(wbxml)
                if m:
                    attrs = dict(_ATTR.findall(m.group(1)))
                    out["calc_mode"] = attrs.get("calcMode", "auto")  # Excel omits it when automatic
                    out["full_calc_on_load"] = attrs.get("fullCalcOnLoad")
                    out["calc_id"] = attrs.get("calcId")
    except (zipfile.BadZipFile, KeyError, OSError):
        pass
    return out


_SHEET_TAG = re.compile(r'<sheet\b[^>]*\bname="([^"]+)"[^>]*\br:id="([^"]+)"')
_REL_TAG = re.compile(r"<Relationship\b[^>]*>")


def _sheet_parts(z: zipfile.ZipFile) -> dict[str, str]:
    """Map worksheet name (upper-cased) -> zip part name, via workbook.xml and its rels."""
    wbxml = z.read("xl/workbook.xml").decode("utf-8", "replace")
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8", "replace")
    rid_to_target: dict[str, str] = {}
    for rel in _REL_TAG.findall(rels):
        attrs = dict(_ATTR.findall(rel))
        if "Id" in attrs and "Target" in attrs:
            rid_to_target[attrs["Id"]] = attrs["Target"]
    out: dict[str, str] = {}
    for name, rid in _SHEET_TAG.findall(wbxml):
        target = rid_to_target.get(rid)
        if target:
            target = target.lstrip("/")
            out[name.upper()] = target if target.startswith("xl/") else "xl/" + target
    return out


def _has_cached_value(t_attr: str | None, inner_xml: str) -> bool:
    """True if a formula cell's XML carries a value Excel calculated.

    Excel writes '<v>number</v>', or 't="str"' + '<v>text</v>' / '<v/>' for a "" result,
    or 't="e"'/'t="b"' with a value. openpyxl writes an empty '<v></v>' with no 't' — that,
    or no '<v>' at all, is an uncalculated cell.
    """
    m = re.search(r"<v>([^<]*)</v>|<v/>", inner_xml)
    if m is None:
        return False
    text = (m.group(1) or "").strip()
    return bool(text) or t_attr == "str"


def formula_cache_signals(
    path: pathlib.Path, specs: tuple[ResultCellSpec, ...], values_xl: OpenpyxlWorkbook | None = None
) -> dict[str, Any]:
    """Inspect each results cell's raw XML: does it carry a formula, and does it carry a cached value?

    Excel always writes a cached value beside a formula it has calculated ('t="str"'
    with an empty '<v/>' for a "" result); a formula cell with no value, or openpyxl's
    bare '<v></v>', means the file was written by something that did not calculate.
    openpyxl's parsed value cannot tell those apart (both read as None) — hence the raw read.

    Arguments:
    ----------
        * path: (pathlib.Path) The workbook.
        * specs: (tuple[ResultCellSpec, ...]) The results cells to check.
        * values_xl: (OpenpyxlWorkbook | None) Unused; kept so callers may pass their open workbook.

    Returns:
    --------
        * (dict[str, Any]): 'n_formula' cells carrying a formula, 'n_formula_cached' of those with a
            '<v>' element, 'formula_without_cache' the keys lacking one, 'skipped_sheets' sheets absent.
    """
    n_formula = 0
    n_cached = 0
    missing: list[str] = []
    skipped: set[str] = set()
    by_sheet: dict[str, list[ResultCellSpec]] = {}
    for spec in specs:
        by_sheet.setdefault(spec.sheet.upper(), []).append(spec)
    try:
        with zipfile.ZipFile(path) as z:
            parts = _sheet_parts(z)
            for sheet_key, sheet_specs in by_sheet.items():
                part = parts.get(sheet_key)
                if part is None or part not in z.namelist():
                    skipped.add(sheet_specs[0].sheet)
                    continue
                xml = z.read(part).decode("utf-8", "replace")
                for spec in sheet_specs:
                    m = re.search(rf'<c r="{spec.cell}"((?:\s+[\w:]+="[^"]*")*)>(.*?)</c>', xml, re.S)
                    attrs = dict(_ATTR.findall(m.group(1))) if m else {}
                    inner = m.group(2) if m else ""
                    if "<f" not in inner:
                        continue
                    n_formula += 1
                    if _has_cached_value(attrs.get("t"), inner):
                        n_cached += 1
                    else:
                        missing.append(spec.key)
    except (zipfile.BadZipFile, KeyError, OSError):
        skipped.update(s.sheet for s in specs)
    return {
        "n_formula": n_formula,
        "n_formula_cached": n_cached,
        "formula_without_cache": missing,
        "skipped_sheets": sorted(skipped),
    }


def assess(
    path: pathlib.Path,
    specs: tuple[ResultCellSpec, ...],
    properties: Any | None = None,
    values_xl: OpenpyxlWorkbook | None = None,
) -> Freshness:
    """Combine the package and formula-cache signals into a verdict with evidence.

    Arguments:
    ----------
        * path: (pathlib.Path) The workbook.
        * specs: (tuple[ResultCellSpec, ...]) The results cells to check for cached values.
        * properties: (DocumentProperties | None) openpyxl properties if already loaded (lastModifiedBy, modified).
        * values_xl: (OpenpyxlWorkbook | None) An already-open data_only workbook to reuse.

    Returns:
    --------
        * (Freshness): verdict + evidence + raw signals. Never refuses on its own.
    """
    sig = read_package_signals(path)
    if properties is not None:
        sig["last_modified_by"] = getattr(properties, "lastModifiedBy", None)
        sig["modified"] = getattr(properties, "modified", None)
    sig.update(formula_cache_signals(path, specs, values_xl))

    evidence: list[str] = []
    suspect_reasons: list[str] = []

    app = sig.get("application")
    evidence.append(
        f"writer: {app!r} v{sig.get('app_version')!r}, last-modified-by {sig.get('last_modified_by')!r} at {sig.get('modified')}"
    )
    if app is None or not _EXCEL_APP.match(str(app).strip()):
        suspect_reasons.append(f"last writer is not Excel ({app!r})")

    calc_mode = sig.get("calc_mode")
    evidence.append(
        f"calcPr: calcMode={calc_mode!r} fullCalcOnLoad={sig.get('full_calc_on_load')!r} calcId={sig.get('calc_id')!r}"
    )
    if calc_mode not in (None, "auto", "autoNoTable"):
        suspect_reasons.append(f"calculation mode is {calc_mode!r}")
    if str(sig.get("full_calc_on_load") or "0").lower() in ("1", "true"):
        suspect_reasons.append("workbook flagged fullCalcOnLoad (writer asked Excel to recalculate everything on open)")

    n_f, n_c = sig["n_formula"], sig["n_formula_cached"]
    evidence.append(
        f"results cells: {n_f} formula cells, {n_c} with a cached value; without: {sig['formula_without_cache']}"
    )
    if sig["skipped_sheets"]:
        evidence.append(f"sheets absent, not checked: {sig['skipped_sheets']}")
    if 0 < n_c < n_f:
        suspect_reasons.append(
            f"{n_f - n_c} of {n_f} results formula cells have no cached value (Excel always writes one)"
        )

    if n_f > 0 and n_c == 0:
        verdict = FreshnessVerdict.EMPTY
        evidence.append("verdict EMPTY: formulas present, no cached values at all")
    elif suspect_reasons:
        verdict = FreshnessVerdict.SUSPECT
        evidence.append("verdict SUSPECT: " + "; ".join(suspect_reasons))
    else:
        verdict = FreshnessVerdict.FRESH
        evidence.append("verdict FRESH: Excel writer, automatic calculation, no recalc flag, results cached")
    return Freshness(verdict=verdict, evidence=evidence, signals=sig)
