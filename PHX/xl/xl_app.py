# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Class for managing the Excel Application Connection and common read/write operations."""

from typing import Optional, List, Set, Callable, Any
from contextlib import contextmanager
import os

import xlwings as xw

from PHX.xl import xl_data
from PHX.xl.xl_typing import (
    xl_Framework_Protocol,
    xl_Book_Protocol,
    xl_Sheet_Protocol,
    xl_Range_Protocol,
)

# -----------------------------------------------------------------------------
# -- Exceptions


class ReadRowsError(Exception):
    def __init__(self, row_start, row_end):
        self.msg = (
            f"Error: row_start should be less than "
            f"row_end. Got {row_start}, {row_end}"
        )
        super().__init__(self.msg)


class NoActiveExcelRunningError(Exception):
    def __init__(self):
        self.msg = (
            "\n\tError: No active instance of Excel running?"
            "\n\tPlease open Excel and try again."
        )
        super().__init__(self.msg)


class ReadMultipleColumnsError(Exception):
    def __init__(self, _c1, _c2):
        self.msg = (
            f'\n\tError: Cannot use "read_multiple_columns()" with _col_start={_c1}'
            f'and _col_end={_c2}. Please use "read_single_column()" instead.'
        )
        super().__init__(self.msg)


class WriteValueError(Exception):
    def __init__(self, _value, _range, _worksheet, _e):
        self.msg = (
            f"\n\n\tSomething went wrong trying to write the value: '{_value}' to the "
            f"cell: '{_range}' on worksheet: '{_worksheet}'. Please make sure that a "
            f"valid Excel file is open, and both the worksheet and workbook are "
            f"unprotected.\n\n{_e}"
        )
        super().__init__(self.msg)


# -----------------------------------------------------------------------------


def silent_print(_input: Any) -> None:
    """Default 'output' for XLConnection."""
    return


# -----------------------------------------------------------------------------


class XLConnection:
    def __init__(self, xl_framework, output: Optional[Callable] = silent_print):
        """Facade class for Excel Interop

        Arguments:
        ----------
            * xl (xl_Framework_Protocol): The Excel framework to use to interact with XL.
            * _output (Callable[[Any], None]): The output function to use.
                Default is silent (no output), or provide 'print' for standard-out, etc.
        """
        # -- Note: can not type-hint xl_framework in the Class argument line
        # -- cus' Python-3.7 doesn't have Protocols yet. It does see to work
        # -- when type-hinting the actual attribute though.
        self.xl: xl_Framework_Protocol = xl_framework
        self._output = output

    def output(self, _input):
        """Used to set the output method. Default is None (silent).

        Arguments:
        ----------
            * _input (SupportsString): The string to output.

        Returns:
        --------
            * (None)
        """
        try:
            self._output(str(_input))  # type: ignore
        except:
            # If _input=None, ignore...
            pass

    @property
    def wb(self) -> xl_Book_Protocol:
        try:
            return self.xl.books.active
        except:
            raise NoActiveExcelRunningError

    @contextmanager
    def in_silent_mode(self):
        """Context Manager which turns off screen-refresh and auto-calc in the
        Excel App in order to help speed up read/write. Turns back on screen-refresh
        and auto-calc in the Excel App when done or on any error.
        """
        try:
            self.wb.app.screen_updating = False
            self.wb.app.display_alerts = False
            self.wb.app.calculation = "manual"
            yield
        finally:
            self.wb.app.screen_updating = True
            self.wb.app.display_alerts = True
            self.wb.app.calculation = "automatic"
            self.wb.app.calculate()

    def unprotect_all_sheets(self) -> None:
        """Walk through all the sheets and unprotect them all."""
        for sheet in self.wb.sheets:
            if os.name != "nt":
                sheet.api.unprotect()
            else:
                sheet.api.Unprotect()

    def get_row_num_of_value_in_column(
        self, sheet_name: str, row_start: int, row_end: int, col: str, find: str
    ) -> Optional[int]:
        """Returns the row number of the first instance of a specific value
        found within a column, or None if not found.

        Arguments:
        ----------
            * sheet_name: (str) The name of the sheet to be looking in
            * row_start: (int) The row number to begin looking from
            * row_end: (int) The row number to stop looking on
            * col: (str) The column to look in
            * find: (Optional[str]) The string to search for (or 'None' for blank cell)

        Returns:
        --------
            * Optional[int]: The row number where the first instance of the specified
                value is found or None if no instances are found.
        """

        if row_start > row_end:
            raise ReadRowsError(row_start, row_end)

        row: int = row_start
        sh: xl_Sheet_Protocol = self.get_sheet_by_name(sheet_name)

        while row <= row_end:
            if sh.range(f"{col}{row}").value != find:
                row += 1
            else:
                return row
        return None

    def get_worksheet_names(self) -> Set[str]:
        """Return a set of all the worksheet names in the workbook.

        Returns:
        --------
            * (Set[str])
        """
        return {sh.name for sh in self.wb.sheets}

    def get_sheet_by_name(self, _sheet_name: str) -> xl_Sheet_Protocol:
        """Returns an Excel Sheet with the specified name, or KeyError if not found.

        Arguments:
        ----------
            * _sheet_name: (str): The excel sheet name to locate.

        Returns:
        --------
            * (xw.main.Sheet): The excel sheet found.
        """
        return self.wb.sheets[_sheet_name]

    def create_new_worksheet(self, _sheet_name: str) -> None:
        """Try and add a new Worksheet to the Workbook."""
        try:
            self.wb.sheets.add(_sheet_name)
            self.output(f"Adding '{_sheet_name}' to Workbook")
        except ValueError:
            self.output(f"Worksheet '{_sheet_name}' already in Workbook.")

        self.get_sheet_by_name(_sheet_name).clear()

    def get_last_used_row_num_in_column(self, _sheet_name: str, _col: str) -> int:
        """Return the row number of the last cell in a column with a value in it.

        Arguments:
        ----------
            * _sheet_name (str): The name of the Worksheet to read from.
            * _col (str): The Alpha character of the column to read.

        Returns:
        --------
            * (int): The number of the last row in the column with a value.
        """
        sheet = self.get_sheet_by_name(_sheet_name)
        sheet.activate()
        col_range = sheet.range(f"{_col}:{_col}")
        col_last_cell_range = sheet.range(col_range.last_cell.address)
        group_last_cell_range = col_last_cell_range.end("up")  # same as 'Ctrl-Up'
        return group_last_cell_range.row

    def get_single_column_data(
        self,
        _sheet_name: str,
        _col: str,
        _row_start: Optional[int] = None,
        _row_end: Optional[int] = None,
    ) -> List[xl_data.xl_range_value]:
        """Return a list with the values read from a single column of the excel document.

        Arguments:
        ----------
            * _sheet_name: (str) The Excel Worksheet to read from.
            * _col: (str) The Column letter to read.
            * _row_start: (Optional[int]) default=None
            * _row_end: (Optional[int]) default=None
        Returns:
        --------
            (List[xl_range_value]): The data from Excel worksheet, as a list.
        """

        if not _row_start or not _row_end:
            _row_start = 1
            _row_end = self.get_last_used_row_num_in_column(_sheet_name, _col)

        address = f"{_col}{_row_start}:{_col}{_row_end}"
        self.output(f"Reading: '{address}' data on sheet: '{_sheet_name}'")

        sheet = self.get_sheet_by_name(_sheet_name)
        sheet.activate()
        col_range = sheet.range(f"{address}")
        return col_range.value  # type: ignore

    def get_last_used_column_in_row(self, _sheet_name: str, _row: int) -> str:
        """Return the column letter of the last cell in a column with a value in it.

        Arguments:
        ----------
            * _sheet_name (str): The name of the Worksheet to read from.
            * _col (str): The Alpha character of the column to read.

        Returns:
        --------
            * (str): The Letter of the last column in the row with a value.
        """
        sheet = self.get_sheet_by_name(_sheet_name)
        sheet.activate()
        row_range = sheet.range(f"{_row}:{_row}")
        row_last_cell_range = sheet.range(row_range.last_cell.address)
        group_last_cell_range = row_last_cell_range.end("left")  # same as 'Ctrl-Left'
        return xl_data.xl_chr(xl_data.xl_ord("A") + group_last_cell_range.column - 1)

    def get_single_row_data(
        self, _sheet_name: str, _row_number: int
    ) -> List[xl_data.xl_range_single_value]:
        """Return all the data from a single Row in the Excel Workbook.

        Arguments:
        ----------
            * _sheet_name (str): The name of the sheet to read
            * _row_number (int): The row number to read

        Returns:
        --------
            * (List[xl_data.xl_range_single_value]) A List of the data read from XL.
        """

        self.output(f"Reading: Row-{_row_number} on sheet: '{_sheet_name}'")

        sheet = self.get_sheet_by_name(_sheet_name)
        sheet.activate()
        last_col_letter = self.get_last_used_column_in_row(_sheet_name, _row_number)
        row_range = sheet.range(f"A{_row_number}:{last_col_letter}{_row_number}")
        return row_range.value  # type: ignore

    def get_multiple_column_data(
        self,
        _sheet_name: str,
        _col_start: str,
        _col_end: str,
        _row_start: int = 1,
        _row_end: int = 100,
    ) -> xl_data.xl_range_value:
        """Return a list of lists with the values read from a specified block of the xl document.

        Arguments:
        ----------
            * _sheet_name: (str) The Worksheet to read from.
            * _col_start: (str) The Column letter to read from.
            * _col_end: (str) The Column letter to read to.
            * _row_start: (int) default=1
            * _row_end: (int) default=100

        Returns:
        --------
            (List[List[xl_range_value]]): The data from Excel worksheet, as a list of lists.
        """

        if _col_start == _col_end:
            raise ReadMultipleColumnsError(_col_start, _col_end)

        # -- Use xl.Range() instead of ord() since ord('KL') will fail
        rng: xl_Range_Protocol = self.xl.Range(f"{_col_end}1:{_col_start}1")
        _ndim = len(rng.columns)

        sheet = self.get_sheet_by_name(_sheet_name)
        rng = sheet.range(f"{_col_start}{_row_start}:{_col_end}{_row_end}")
        rng = rng.options(ndim=_ndim)
        return rng.value

    def get_data(self, _sheet_name: str, _range: str) -> xl_data.xl_writable:
        """Return a value or values from the Excel document.

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to read from.
            * _range: (str) The cell range to write to (ie: "A1") or a set of ranges (ie: "A1:B4")

        Returns:
        ---------
            * (xl_writable): The resultant value/values returned from excel.
        """
        self.output(f"Reading: {_sheet_name}:{_range}")
        return self.get_sheet_by_name(_sheet_name).range(_range).value

    def write_xl_item(self, _xl_item: xl_data.XlItem) -> None:
        """Writes a single XLItem to the worksheet

        Arguments:
        ---------
            * _xl_item: (XLItem) The XLItem with a sheet_name, range and value to write.
        """
        try:
            self.output(
                f"{_xl_item.sheet_name}:{_xl_item.xl_range}={_xl_item.write_value}"
            )
            xl_sheet = self.get_sheet_by_name(_xl_item.sheet_name)
            xl_range = xl_sheet.range(_xl_item.xl_range)
            xl_range.value = _xl_item.write_value  # type: ignore

            if _xl_item.font_color or _xl_item.range_color:
                xl_range.color = _xl_item.range_color
                xl_range.font.color = _xl_item.font_color

        except AttributeError as e:
            raise AttributeError(e)
        except Exception as e:
            raise WriteValueError(
                _xl_item.write_value, _xl_item.xl_range, _xl_item.sheet_name, e
            )

    def clear_range_data(self, _sheet_name: str, _range: str) -> None:
        """Sets the specified excel sheet's range to 'None'

        Arguments:
        ---------
            * _sheet_name: (str) The name of the worksheet
            * _range: (str) The cell range to write to (ie: "A1") or a set of ranges (ie: "A1:B4")
        """
        self.get_sheet_by_name(_sheet_name).range(_range).value = None

    def clear_sheet_contents(self, _sheet_name: str) -> None:
        """Clears the content of the whole sheet but leaves the formatting."""
        self.get_sheet_by_name(_sheet_name).clear_contents()

    def clear_sheet_formats(self, _sheet_name: str) -> None:
        """Clears the format of the whole sheet but leaves the content."""
        self.get_sheet_by_name(_sheet_name).clear_formats()

    def clear_sheet_all(self, _sheet_name: str) -> None:
        """Clears the content and formatting of the whole sheet."""
        self.get_sheet_by_name(_sheet_name).clear()
