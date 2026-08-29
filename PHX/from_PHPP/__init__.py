# -*- Python Version: 3.10 -*-

"""Read a closed PHPP workbook: identity (sniff), headline results, stale-cache signals.

This is the read-side counterpart to 'PHX.PHPP' (the xlwings write path). It opens the
file with openpyxl ('read_only=True, data_only=True'), never recalculates and never
saves. Everything it could not read is named in a 'ReadReport' (never a silent misread).

Entry points: 'sniff.sniff_path()', 'results.read_results()'.
"""

from PHX.from_PHPP.report import ReadReport, Refusal, RefusalReason
from PHX.from_PHPP.results import ReadResult, ResultsRecord, ResultValue, read_results
from PHX.from_PHPP.sniff import Flavour, PhppIdentity, SniffResult, sniff_path
from PHX.from_PHPP.staleness import Freshness, FreshnessVerdict

__all__ = [
    "Flavour",
    "Freshness",
    "FreshnessVerdict",
    "PhppIdentity",
    "ReadReport",
    "ReadResult",
    "Refusal",
    "RefusalReason",
    "ResultValue",
    "ResultsRecord",
    "SniffResult",
    "read_results",
    "sniff_path",
]
