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
  * the results cells    -> formula present but no cached value (a second, formula-mode open)
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


def formula_cache_signals(
    path: pathlib.Path, specs: tuple[ResultCellSpec, ...], values_xl: OpenpyxlWorkbook | None = None
) -> dict[str, Any]:
    """Open the file a second time in formula mode and compare each results cell with its cached value.

    Arguments:
    ----------
        * path: (pathlib.Path) The workbook.
        * specs: (tuple[ResultCellSpec, ...]) The results cells to check.
        * values_xl: (OpenpyxlWorkbook | None) An already-open data_only workbook to reuse for the
            cached values (saves one open); opened here if None.

    Returns:
    --------
        * (dict[str, Any]): 'n_formula' cells carrying a formula, 'n_formula_cached' of those with a
            cached value, 'formula_without_cache' the keys lacking one, 'skipped_sheets' sheets absent.
    """
    n_formula = 0
    n_cached = 0
    missing: list[str] = []
    skipped: set[str] = set()
    own_vx = values_xl is None
    vx = OpenpyxlWorkbook(path, data_only=True) if values_xl is None else values_xl
    try:
        fx = OpenpyxlWorkbook(path, data_only=False)
    except Exception:
        if own_vx:
            vx.close()
        raise
    try:
        for spec in specs:
            if spec.sheet.upper() not in fx.worksheet_names:
                skipped.add(spec.sheet)
                continue
            raw = fx.get_single_data_item(spec.sheet, spec.cell)
            if isinstance(raw, str) and raw.startswith("="):
                n_formula += 1
                cached = vx.get_single_data_item(spec.sheet, spec.cell)
                if cached is None:
                    missing.append(spec.key)
                else:
                    n_cached += 1
    finally:
        fx.close()
        if own_vx:
            vx.close()
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
    if app is None or "excel" not in str(app).lower():
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
