# -*- Python Version: 3.10 -*-

"""Shared helpers for detecting and clearing stale PHPP list rows."""

from PHX.xl import xl_app
from PHX.xl.xl_data import xl_chr, xl_ord


def _cell_has_value(_value: object) -> bool:
    """Return True when an Excel cell value represents a filled user entry."""
    return _value is not None and _value != ""


def _format_stale_rows(_row_numbers: list[int]) -> str:
    """Return a compact row-number label for a stale-row warning."""
    if len(_row_numbers) == 1:
        return f"row {_row_numbers[0]}"
    if len(_row_numbers) > 10:
        return f"rows {_row_numbers[0]}-{_row_numbers[-1]} ({len(_row_numbers)})"
    return f"rows {', '.join(str(row) for row in _row_numbers)}"


def _contiguous_row_groups(_row_numbers: list[int]) -> list[tuple[int, int]]:
    """Return inclusive contiguous row spans from sorted worksheet row numbers."""
    if not _row_numbers:
        return []

    groups: list[tuple[int, int]] = []
    start = previous = _row_numbers[0]
    for row in _row_numbers[1:]:
        if row == previous + 1:
            previous = row
            continue
        groups.append((start, previous))
        start = previous = row
    groups.append((start, previous))
    return groups


def _contiguous_column_groups(_columns: list[str]) -> list[tuple[str, str]]:
    """Return inclusive contiguous column spans from Excel column letters."""
    if not _columns:
        return []

    column_numbers = sorted({xl_ord(col) for col in _columns})
    groups: list[tuple[str, str]] = []
    start = previous = column_numbers[0]
    for column in column_numbers[1:]:
        if column == previous + 1:
            previous = column
            continue
        groups.append((xl_chr(start), xl_chr(previous)))
        start = previous = column
    groups.append((xl_chr(start), xl_chr(previous)))
    return groups


def _range_address(_col_start: str, _col_end: str, _row_start: int, _row_end: int) -> str:
    """Return an Excel range address for a column span and row span."""
    start = f"{_col_start}{_row_start}"
    end = f"{_col_end}{_row_end}"
    if start == end:
        return start
    return f"{start}:{end}"


def _read_column_with_integrity_guard(
    _xl: xl_app.XLConnection,
    _sheet_name: str,
    _col: str,
    _row_start: int,
    _row_end: int,
) -> list[object]:
    """Read one column block, falling back per-cell if xlwings drops error cells."""
    data = _xl.get_single_column_data(
        _sheet_name=_sheet_name,
        _col=_col,
        _row_start=_row_start,
        _row_end=_row_end,
    )
    if not isinstance(data, list):
        data = [data]

    expected_len = _row_end - _row_start + 1
    if len(data) == expected_len:
        return list(data)

    return [_xl.get_data(_sheet_name, f"{_col}{row}") for row in range(_row_start, _row_end + 1)]
