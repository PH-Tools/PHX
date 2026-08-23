# -*- Python Version: 3.10 -*-

"""Typed refusals and the per-file read report.

Two rules from the Pholio brief live here: *read tolerantly, refuse loudly* and
*report, don't guess*. A workbook the reader cannot handle yields a 'Refusal'
with a named reason, never a bare exception; and every read, read or not,
yields a 'ReadReport' listing what was read, what was not, and why.
"""

from __future__ import annotations

import enum
import pathlib
from dataclasses import dataclass, field


class RefusalReason(enum.Enum):
    """Why a workbook was refused outright (as opposed to read with gaps).

    Values:
        NOT_A_FILE: The path does not exist or is not a regular file.
        NOT_A_WORKBOOK: openpyxl could not open it as an .xlsx/.xlsm zip package.
        NOT_A_PHPP: No 'Data' + 'Verification' + 'PER' worksheets; not a PHPP.
        VERSION_UNREADABLE: A PHPP by its sheets, but the version cell could not be parsed.
        VERSION_UNSUPPORTED: A PHPP whose version/language has no results map (named in the detail).
        BLANK_TEMPLATE: A PHPP with no project content (TFA 0, no building name) — identity is known, results are not read.
        RESULTS_REGION_EMPTY: Sniffed as a project PHPP, but every results cell is empty (no cached values).
    """

    NOT_A_FILE = "not_a_file"
    NOT_A_WORKBOOK = "not_a_workbook"
    NOT_A_PHPP = "not_a_phpp"
    VERSION_UNREADABLE = "version_unreadable"
    VERSION_UNSUPPORTED = "version_unsupported"
    BLANK_TEMPLATE = "blank_template"
    RESULTS_REGION_EMPTY = "results_region_empty"


@dataclass(frozen=True)
class Refusal:
    """A typed, loud refusal to read a workbook.

    Attributes:
        reason (RefusalReason): The category.
        detail (str): The specific evidence in plain language (sheet names seen, version string, ...).
    """

    reason: RefusalReason
    detail: str

    def __str__(self) -> str:
        return f"Refused ({self.reason.value}): {self.detail}"


@dataclass(frozen=True)
class UnreadItem:
    """One thing the reader wanted and did not get.

    Attributes:
        name (str): The results-set key (ie: 'heating_demand') or sniff item.
        sheet (str | None): The worksheet it was expected on.
        cell (str | None): The cell address it was expected at.
        reason (str): Why it was not read (empty cell, label mismatch, sheet missing, ...).
    """

    name: str
    sheet: str | None
    cell: str | None
    reason: str


@dataclass
class ReadReport:
    """What one read of one file did: read, not read, and why.

    Attributes:
        path (pathlib.Path): The workbook read.
        refusal (Refusal | None): Set when the whole file was refused.
        read (list[str]): Keys that were read with a usable value.
        not_applicable (list[str]): Keys the workbook legitimately leaves blank ('-').
        unread (list[UnreadItem]): Keys that could not be read, each with a reason.
        notes (list[str]): Free-text observations (freshness evidence, map provenance, ...).
    """

    path: pathlib.Path
    refusal: Refusal | None = None
    read: list[str] = field(default_factory=list)
    not_applicable: list[str] = field(default_factory=list)
    unread: list[UnreadItem] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when the file was not refused."""
        return self.refusal is None

    def summary(self) -> str:
        """Return a one-paragraph plain-text summary of the report."""
        if self.refusal:
            return f"{self.path.name}: {self.refusal}"
        parts = [f"{self.path.name}: read {len(self.read)}"]
        if self.not_applicable:
            parts.append(f"n/a {len(self.not_applicable)} ({', '.join(self.not_applicable)})")
        if self.unread:
            parts.append("unread " + "; ".join(f"{u.name}@{u.sheet}!{u.cell}: {u.reason}" for u in self.unread))
        if self.notes:
            parts.append("notes: " + " | ".join(self.notes))
        return " · ".join(parts)
