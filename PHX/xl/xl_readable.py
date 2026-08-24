# -*- Python Version: 3.10 -*-

"""Read-side Protocol for the Excel-interop layer.

'XLConnection' (xlwings, an open workbook) already satisfies this Protocol
unchanged; 'PHX.from_PHPP.xl_openpyxl.OpenpyxlWorkbook' implements it for a
closed file. Readers that only need cell values should type against this
Protocol rather than 'XLConnection' so either backend can be used.
"""

from typing import Protocol, runtime_checkable

from PHX.xl import xl_data


@runtime_checkable
class XLReadable(Protocol):
    """The minimal read-only surface shared by the xlwings and openpyxl backends.

    Attributes:
        worksheet_names (set[str]): The workbook's worksheet names, upper-cased.
    """

    @property
    def worksheet_names(self) -> set[str]:
        """Cached set of the Workbook's worksheet names, upper-cased."""
        ...

    def get_data(self, _sheet_name: str, _range: str) -> xl_data.xl_writable:
        """Return a value (single cell) or nested lists (multi-cell range).

        Arguments:
        ----------
            * _sheet_name: (str) The worksheet name (case-insensitive).
            * _range: (str) A cell ("A1") or range ("A1:B4") address.

        Returns:
        --------
            * (xl_writable): scalar for one cell; list for a 1-D range; list of lists for 2-D.
        """
        ...

    def get_single_data_item(self, _sheet_name: str, _range: str) -> xl_data.xl_range_single_value:
        """Return the value of a single cell.

        Arguments:
        ----------
            * _sheet_name: (str) The worksheet name (case-insensitive).
            * _range: (str) A single-cell address ("A1").

        Returns:
        --------
            * (xl_range_single_value): The cell's value (str | float | int | None).
        """
        ...

    def get_single_column_data(
        self,
        _sheet_name: str,
        _col: str,
        _row_start: int | None = None,
        _row_end: int | None = None,
    ) -> list[xl_data.xl_range_single_value]:
        """Return the values of one column between two rows (inclusive).

        Arguments:
        ----------
            * _sheet_name: (str) The worksheet name (case-insensitive).
            * _col: (str) The column letter.
            * _row_start: (int | None) First row (default 1).
            * _row_end: (int | None) Last row (default: last used row).

        Returns:
        --------
            * (list[xl_range_single_value]): One entry per row, None for empty cells.
        """
        ...

    def get_single_row_data(self, _sheet_name: str, _row_number: int) -> list[xl_data.xl_range_single_value]:
        """Return all the values of one row, from column A to the last used column.

        Arguments:
        ----------
            * _sheet_name: (str) The worksheet name (case-insensitive).
            * _row_number: (int) The row number.

        Returns:
        --------
            * (list[xl_range_single_value]): One entry per column.
        """
        ...
