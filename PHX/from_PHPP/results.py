# -*- Python Version: 3.10 -*-

"""Read the headline results of a closed PHPP into a typed record, or refuse by name.

'read_results(path)' sniffs the file, picks the results map for its version,
asserts each caption before reading its value, assesses the cached-value
freshness, and returns a 'ReadResult': a 'ResultsRecord' or a 'Refusal', plus a
'ReadReport' either way. Nothing here raises for a bad workbook.
"""

from __future__ import annotations

import enum
import pathlib
from dataclasses import dataclass, field
from typing import Any

from PHX.from_PHPP.report import ReadReport, Refusal, RefusalReason, UnreadItem
from PHX.from_PHPP.results_map import ResolvedMap, ResultCellSpec, ValueKind, resolve_map
from PHX.from_PHPP.sniff import Flavour, PhppIdentity, sniff_workbook
from PHX.from_PHPP.staleness import Freshness, FreshnessVerdict, assess
from PHX.from_PHPP.xl_openpyxl import OpenpyxlWorkbook


class ValueStatus(enum.Enum):
    """What happened when one results cell was read.

    Values:
        OK: Caption matched, value present and of the expected kind.
        NOT_APPLICABLE: Caption matched; PHPP shows '-' (ie: cooling demand without mechanical cooling).
        EMPTY: Caption matched; the cell has no cached value.
        LABEL_MISMATCH: The caption beside the cell is not the one expected — value not trusted, not returned.
        SHEET_MISSING: The worksheet is not in this workbook.
        TYPE_MISMATCH: A number was expected and something else was cached.
    """

    OK = "ok"
    NOT_APPLICABLE = "not_applicable"
    EMPTY = "empty"
    LABEL_MISMATCH = "label_mismatch"
    SHEET_MISSING = "sheet_missing"
    TYPE_MISMATCH = "type_mismatch"


@dataclass(frozen=True)
class ResultValue:
    """One headline value with its provenance.

    Attributes:
        key (str): The results-set key (ie: 'heating_demand').
        value (float | str | None): The value; None unless status is OK.
        unit (str | None): The unit as PHPP displays it (ie: 'kWh/(m²a)').
        ph_units_name (str | None): The ph_units name where one exists (ie: 'KWH/M2').
        sheet (str): Worksheet read.
        cell (str): Cell address read.
        label_as_read (str | None): The caption text found beside the value.
        status (ValueStatus): How the read went.
        note (str): Reader note (what the cell is / why it was not read).
    """

    key: str
    value: float | str | None
    unit: str | None
    ph_units_name: str | None
    sheet: str
    cell: str
    label_as_read: str | None
    status: ValueStatus
    note: str = ""

    @property
    def source(self) -> str:
        """'Sheet!cell' for display."""
        return f"{self.sheet}!{self.cell}"


@dataclass
class ResultsRecord:
    """The headline results of one PHPP save, every value with its source cell.

    Attributes:
        path (pathlib.Path): The workbook read.
        identity (PhppIdentity): Version, language, flavour.
        map_version_key (str): The results map used (ie: 'EN_10_6').
        map_verified (bool): True when the map was built by reading this exact version.
        values (dict[str, ResultValue]): Keyed by results-set key; includes non-OK statuses.
        freshness (Freshness): The stale-cache verdict and evidence.
    """

    path: pathlib.Path
    identity: PhppIdentity
    map_version_key: str
    map_verified: bool
    values: dict[str, ResultValue] = field(default_factory=dict)
    freshness: Freshness = field(default_factory=lambda: Freshness(FreshnessVerdict.FRESH))

    def get(self, key: str) -> float | str | None:
        """Return the value for a key, or None if it was not read OK."""
        rv = self.values.get(key)
        return rv.value if rv and rv.status is ValueStatus.OK else None

    @property
    def ok_keys(self) -> list[str]:
        """Keys read with status OK."""
        return [k for k, v in self.values.items() if v.status is ValueStatus.OK]


@dataclass
class ReadResult:
    """What 'read_results()' returns: a record or a refusal, and always a report.

    Attributes:
        record (ResultsRecord | None): The results, when the file was read.
        refusal (Refusal | None): The typed refusal, when it was not.
        report (ReadReport): Read / unread / notes, always.
        identity (PhppIdentity | None): Known even for some refusals (blank template, unsupported version).
    """

    record: ResultsRecord | None
    refusal: Refusal | None
    report: ReadReport
    identity: PhppIdentity | None = None

    @property
    def ok(self) -> bool:
        """True when a record was produced."""
        return self.record is not None


def _norm(s: Any) -> str:
    return " ".join(str(s or "").split()).upper()


def _read_one(xl: OpenpyxlWorkbook, spec: ResultCellSpec) -> ResultValue:
    """Read one spec: assert the caption, then the value."""
    base: dict[str, Any] = {
        "key": spec.key,
        "unit": spec.unit,
        "ph_units_name": spec.ph_units_name,
        "sheet": spec.sheet,
        "cell": spec.cell,
    }
    if spec.sheet.upper() not in xl.worksheet_names:
        return ResultValue(
            value=None, label_as_read=None, status=ValueStatus.SHEET_MISSING, note="worksheet absent", **base
        )

    label = xl.get_single_data_item(spec.sheet, spec.label_cell)
    label_txt = None if label is None else str(label)
    if _norm(spec.label_expected) not in _norm(label):
        return ResultValue(
            value=None,
            label_as_read=label_txt,
            status=ValueStatus.LABEL_MISMATCH,
            note=f"expected caption containing {spec.label_expected!r} at {spec.sheet}!{spec.label_cell}, found {label_txt!r}",
            **base,
        )

    unit = spec.unit
    if spec.unit_cell:
        unit_read = xl.get_single_data_item(spec.sheet, spec.unit_cell)
        if unit_read is not None and str(unit_read).strip():
            unit = str(unit_read).strip()
    base["unit"] = unit

    raw = xl.get_single_data_item(spec.sheet, spec.cell)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return ResultValue(
            value=None, label_as_read=label_txt, status=ValueStatus.EMPTY, note="no cached value", **base
        )

    if spec.kind is ValueKind.TEXT:
        return ResultValue(
            value=str(raw).strip(), label_as_read=label_txt, status=ValueStatus.OK, note=spec.note, **base
        )

    if isinstance(raw, bool):
        return ResultValue(
            value=None, label_as_read=label_txt, status=ValueStatus.TYPE_MISMATCH, note=f"boolean {raw!r}", **base
        )
    if isinstance(raw, (int, float)):
        return ResultValue(value=float(raw), label_as_read=label_txt, status=ValueStatus.OK, note=spec.note, **base)
    if isinstance(raw, str) and raw.strip() in ("-", "–", "—"):
        return ResultValue(
            value=None,
            label_as_read=label_txt,
            status=ValueStatus.NOT_APPLICABLE,
            note=f"PHPP shows {raw.strip()!r}",
            **base,
        )
    return ResultValue(
        value=None,
        label_as_read=label_txt,
        status=ValueStatus.TYPE_MISMATCH,
        note=f"expected a number, cached {raw!r}",
        **base,
    )


def read_results(_path: pathlib.Path | str) -> ReadResult:
    """Read the headline results of a closed PHPP workbook.

    Arguments:
    ----------
        * _path: (pathlib.Path | str) The workbook on disk. Opened read-only; never recalculated or saved.

    Returns:
    --------
        * (ReadResult): record or refusal, plus the report. Refusals are typed
            (not a file / not a workbook / not a PHPP / version unreadable / version
            unsupported / blank template / results region empty / read error); nothing raises.
    """
    path = pathlib.Path(_path)
    report = ReadReport(path=path)
    try:
        return _read_results(path, report)
    except Exception as e:  # hard rule: a workbook we cannot read yields a refusal, never a traceback
        report.refusal = Refusal(RefusalReason.READ_ERROR, f"{type(e).__name__} while reading: {e}")
        return ReadResult(None, report.refusal, report)


def _read_results(path: pathlib.Path, report: ReadReport) -> ReadResult:
    """The read proper; 'read_results' wraps it so stray exceptions become typed refusals."""

    if not path.is_file():
        report.refusal = Refusal(RefusalReason.NOT_A_FILE, f"{path} is not a file")
        return ReadResult(None, report.refusal, report)
    try:
        xl = OpenpyxlWorkbook(path)
    except Exception as e:  # openpyxl raises a zoo of types for non-workbooks
        report.refusal = Refusal(RefusalReason.NOT_A_WORKBOOK, f"openpyxl could not open it: {type(e).__name__}: {e}")
        return ReadResult(None, report.refusal, report)

    with xl:
        sniff = sniff_workbook(xl)
        report.notes.append(f"sniff evidence: {sniff.evidence}")
        if sniff.refusal or sniff.identity is None:
            report.refusal = sniff.refusal or Refusal(RefusalReason.NOT_A_PHPP, "sniff produced no identity")
            return ReadResult(None, report.refusal, report)
        identity = sniff.identity
        report.notes.append(f"identity: {identity.version_label}, {identity.flavour.value}")

        resolved: ResolvedMap | None = resolve_map(identity.version_key)
        if resolved is None:
            report.refusal = Refusal(
                RefusalReason.VERSION_UNSUPPORTED,
                f"{identity.version_label} (key {identity.version_key}) has no results map; supported: EN 10.x",
            )
            return ReadResult(None, report.refusal, report, identity)
        if not resolved.verified:
            report.notes.append(
                f"results map for {resolved.version_key} is assumed from the 10.6 EN map (phi-rules: 10.x addresses are one thing); captions are asserted per cell"
            )

        if identity.flavour is Flavour.BLANK_TEMPLATE:
            report.refusal = Refusal(
                RefusalReason.BLANK_TEMPLATE,
                f"{identity.version_label} with TFA {sniff.evidence.get('tfa')!r}, no building name, no dwelling units, "
                f"template climate — a blank template, not project results",
            )
            return ReadResult(None, report.refusal, report, identity)

        record = ResultsRecord(
            path=path, identity=identity, map_version_key=resolved.version_key, map_verified=resolved.verified
        )
        for spec in resolved.specs:
            rv = _read_one(xl, spec)
            record.values[spec.key] = rv
            if rv.status is ValueStatus.OK:
                report.read.append(spec.key)
            elif rv.status is ValueStatus.NOT_APPLICABLE:
                report.not_applicable.append(spec.key)
            else:
                report.unread.append(UnreadItem(spec.key, spec.sheet, spec.cell, f"{rv.status.value}: {rv.note}"))

        record.freshness = assess(path, resolved.specs, xl.properties, values_xl=xl)
        report.notes.extend(f"freshness: {e}" for e in record.freshness.evidence)

    if record.freshness.verdict is FreshnessVerdict.EMPTY:
        report.refusal = Refusal(
            RefusalReason.RESULTS_REGION_EMPTY,
            f"{identity.version_label}: results cells carry formulas but no cached values "
            f"(last writer {record.freshness.signals.get('application')!r})",
        )
        return ReadResult(None, report.refusal, report, identity)

    return ReadResult(record, None, report, identity)
