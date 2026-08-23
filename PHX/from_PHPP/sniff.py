# -*- Python Version: 3.10 -*-

"""Is this file a PHPP? Which version, which language, project or blank template?

Reads only bounded header cells: the sheet list, 'Data!A1:D10' (version row),
and four project-content signals — 'Verification!I35' (TFA, a formula), 'K5'
(building name), 'F29' (dwelling units) and 'Climate!D12' (the climate data set
picked; the blank template ships with 'DE-9999-PHPP-Standard'). Siblings that
live next to a PHPP in a project folder — the blank PHI template, the Heat Pump
Tool, any renamed .xlsx — must classify as blank-template / not-a-PHPP without
the reader ever reaching into their cells as if they were results.
"""

from __future__ import annotations

import enum
import pathlib
import re
import zipfile
from dataclasses import dataclass, field
from typing import Any

from PHX.from_PHPP.report import Refusal, RefusalReason
from PHX.from_PHPP.xl_openpyxl import OpenpyxlWorkbook
from PHX.PHPP.phpp_model.version import PHPPVersion

# -- The three worksheets every PHPP (9.x, 10.x) carries and the reader needs.
REQUIRED_SHEETS: tuple[str, ...] = ("DATA", "VERIFICATION", "PER")

# -- Where the version row is looked for (PHX 'phpp_app.get_phpp_version' does the same scan).
DATA_VERSION_SEARCH_COL = "A"
DATA_VERSION_SEARCH_ROWS = (1, 10)

# -- 'Data!B<n>' forms seen: '10.6', '10.4a', '9.6a' (a number in some 9.x files), '10.6 easyPHv3'.
_VERSION_RE = re.compile(r"^(\d+)\.(\d+[a-z]?)(?:\s+(easyph\w*))?$", re.IGNORECASE)
# -- PHPP 9 'Data' has no language cell; PHX's write path uses the PE-factor set name as a proxy.
_LANGUAGE_PROXY = {"1-PE-FAKTOREN": "DE", "1-FACTORES EP": "ES", "1-PE-FACTORS": "EN"}

# -- Blank-template signals. TFA is a formula (no cached value in a never-calculated
# -- or cache-stripped file); the other three are inputs, so they survive a cache strip.
TFA_RESULT_CELL = "I35"
BUILDING_NAME_CELL = "K5"
DWELLING_UNITS_CELL = "F29"
CLIMATE_DATASET_CELL = ("Climate", "D12")
CLIMATE_TEMPLATE_DEFAULT = "DE-9999-PHPP-STANDARD"


class Flavour(enum.Enum):
    """What kind of PHPP-shaped file this is.

    Values:
        PROJECT: A PHPP with project content (TFA > 0, or a building name, dwelling units, or a chosen climate).
        BLANK_TEMPLATE: A PHPP with none of those (PHI's empty template, or a never-filled copy).
    """

    PROJECT = "project"
    BLANK_TEMPLATE = "blank_template"


@dataclass(frozen=True)
class PhppIdentity:
    """The identity of a PHPP workbook as read from its header cells.

    Attributes:
        version (PHPPVersion): Major/minor/language as PHX's write path models them.
        flavour (Flavour): Project or blank template.
        version_row (int): The 'Data' row the version label was found on.
        language_cell_present (bool): False for PHPP 9 files, whose 'Data' sheet has no 'Language' cell
            (the language then comes from the PE-factor set name, as PHX's write path does).
        variant (str): A flavour suffix on the version string, ie: 'easyPHv3'; '' for plain PHPP.
        raw_version (str): The version cell as read, ie: '10.6 easyPHv3'.
    """

    version: PHPPVersion
    flavour: Flavour
    version_row: int
    language_cell_present: bool
    variant: str = ""
    raw_version: str = ""

    @property
    def version_key(self) -> str:
        """The PHX shape-file key for this version, ie: 'EN_10_6' (language_major_minor)."""
        return f"{self.version.language}_{self.version.number_major}_{self.version.number_minor}"

    @property
    def version_label(self) -> str:
        """Human label, ie: 'PHPP 10.6 EN' or 'PHPP 10.6 EN (easyPHv3)'."""
        base = f"PHPP {self.version.number()} {self.version.language}"
        return f"{base} ({self.variant})" if self.variant else base


@dataclass
class SniffResult:
    """Outcome of sniffing one path: an identity or a refusal, plus the evidence either way.

    Attributes:
        path (pathlib.Path): The file sniffed.
        identity (PhppIdentity | None): Set when the file is a PHPP.
        refusal (Refusal | None): Set when it is not (not a file, not a workbook, not a PHPP, version unreadable).
        evidence (dict[str, Any]): What was seen: sheet count, the first sheet names, the raw version row, TFA, ...
    """

    path: pathlib.Path
    identity: PhppIdentity | None = None
    refusal: Refusal | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """True when an identity was established."""
        return self.identity is not None


def _find_version_row(xl: OpenpyxlWorkbook) -> tuple[int | None, list[Any]]:
    """Return (row_number, row_values) of the 'Data' row whose column-A text starts with 'PHPP'."""
    r1, r2 = DATA_VERSION_SEARCH_ROWS
    col = xl.get_single_column_data("Data", DATA_VERSION_SEARCH_COL, r1, r2)
    for i, val in enumerate(col, start=r1):
        if val is not None and str(val).upper().strip().replace(" ", "").startswith("PHPP"):
            row = xl.get_data("Data", f"A{i}:Z{i}")
            return i, list(row) if isinstance(row, list) else [row]
    return None, []


def sniff_workbook(xl: OpenpyxlWorkbook) -> SniffResult:
    """Sniff an already-open 'OpenpyxlWorkbook'.

    Arguments:
    ----------
        * xl: (OpenpyxlWorkbook) The open workbook (read-only, data_only).

    Returns:
    --------
        * (SniffResult): identity or refusal, with evidence.
    """
    result = SniffResult(path=xl.path)
    names = xl.sheetnames
    result.evidence["sheet_count"] = len(names)
    result.evidence["first_sheets"] = names[:4]

    missing = [s for s in REQUIRED_SHEETS if s not in xl.worksheet_names]
    if missing:
        result.refusal = Refusal(
            RefusalReason.NOT_A_PHPP,
            f"missing worksheet(s) {missing}; {len(names)} sheets, first: {names[:4]}",
        )
        return result

    version_row, row_vals = _find_version_row(xl)
    result.evidence["version_row"] = version_row
    result.evidence["version_row_values"] = row_vals
    if version_row is None:
        result.refusal = Refusal(
            RefusalReason.VERSION_UNREADABLE,
            f"no cell starting 'PHPP' in Data!{DATA_VERSION_SEARCH_COL}{DATA_VERSION_SEARCH_ROWS[0]}:"
            f"{DATA_VERSION_SEARCH_COL}{DATA_VERSION_SEARCH_ROWS[1]}",
        )
        return result

    # -- Row layout in 10.x: A='PHPP Version', B='10.6', C='Language', D='EN ', E='1-PE-factors …'.
    # -- In 9.x: A='PHPP Version', B='9.6a', C='1-PE-factors …' — no language cells.
    raw_version = row_vals[1] if len(row_vals) > 1 else None
    m = _VERSION_RE.match(str(raw_version).strip()) if raw_version is not None else None
    if m is None:
        result.refusal = Refusal(
            RefusalReason.VERSION_UNREADABLE,
            f"Data!B{version_row} is {raw_version!r}, expected 'major.minor[letter] [easyPH…]'",
        )
        return result
    major, minor, variant = m.group(1), m.group(2), m.group(3) or ""

    language_cell_present = len(row_vals) > 3 and str(row_vals[2] or "").strip().upper() == "LANGUAGE"
    language = str(row_vals[3] or "").strip() if language_cell_present else ""
    if not language:
        for val in row_vals:
            for marker, lang in _LANGUAGE_PROXY.items():
                if marker in str(val or "").upper():
                    language = lang
        result.evidence["language_from_pe_factor_proxy"] = bool(language)
    if not language:
        result.refusal = Refusal(
            RefusalReason.VERSION_UNREADABLE,
            f"version {raw_version!r} found at Data!B{version_row} but no language cell and no PE-factor proxy",
        )
        return result

    version = PHPPVersion(major, minor, language)

    tfa = xl.get_single_data_item("Verification", TFA_RESULT_CELL)
    building_name = xl.get_single_data_item("Verification", BUILDING_NAME_CELL)
    dwelling_units = xl.get_single_data_item("Verification", DWELLING_UNITS_CELL)
    climate = None
    if CLIMATE_DATASET_CELL[0].upper() in xl.worksheet_names:
        climate = xl.get_single_data_item(*CLIMATE_DATASET_CELL)
    result.evidence["tfa"] = tfa
    result.evidence["building_name_present"] = bool(str(building_name or "").strip())
    result.evidence["dwelling_units"] = dwelling_units
    result.evidence["climate_is_template_default"] = (
        climate is None or str(climate).strip().upper() == CLIMATE_TEMPLATE_DEFAULT
    )
    has_tfa = isinstance(tfa, (int, float)) and not isinstance(tfa, bool) and tfa > 0
    has_units = isinstance(dwelling_units, (int, float)) and not isinstance(dwelling_units, bool) and dwelling_units > 0
    is_project = (
        has_tfa
        or result.evidence["building_name_present"]
        or has_units
        or not result.evidence["climate_is_template_default"]
    )
    flavour = Flavour.PROJECT if is_project else Flavour.BLANK_TEMPLATE

    result.identity = PhppIdentity(
        version=version,
        flavour=flavour,
        version_row=version_row,
        language_cell_present=language_cell_present,
        variant=variant,
        raw_version=str(raw_version).strip(),
    )
    return result


def sniff_path(_path: pathlib.Path | str) -> SniffResult:
    """Open a file read-only and sniff it.

    Arguments:
    ----------
        * _path: (pathlib.Path | str) The workbook on disk.

    Returns:
    --------
        * (SniffResult): identity or refusal, with evidence. Never raises for a bad file.
    """
    path = pathlib.Path(_path)
    if not path.is_file():
        return SniffResult(path=path, refusal=Refusal(RefusalReason.NOT_A_FILE, f"{path} is not a file"))
    try:
        xl = OpenpyxlWorkbook(path)
    except (zipfile.BadZipFile, KeyError, OSError, ValueError) as e:
        return SniffResult(
            path=path,
            refusal=Refusal(RefusalReason.NOT_A_WORKBOOK, f"openpyxl could not open it: {type(e).__name__}: {e}"),
        )
    with xl:
        return sniff_workbook(xl)
