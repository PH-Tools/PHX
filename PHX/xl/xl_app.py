# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Class for managing the Excel Application Connection and common read/write operations."""

from typing import Optional, List, Set, Callable, Any, Union, Dict
from contextlib import contextmanager
import os
import pathlib

from PHX.xl import xl_data
from PHX.xl.xl_typing import (
    xl_Framework_Protocol,
    xl_Book_Protocol,
    xl_Books_Protocol,
    xl_Sheets_Protocol,
    xl_Sheet_Protocol,
    xl_Range_Protocol,
    xl_app_Protocol,
    xl_apps_Protocol,
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


class XlReadException(Exception):
    def __init__(self, _range: str):
        self.msg = (
            f"\n\tError: 'get_single_data_item()' can only be used on a"
            f"single range. Got range: '{_range}'. Please use 'get_data()' instead."
        )
        super().__init__(self.msg)


class NoSuchFileError(Exception):
    def __init__(self, _file: pathlib.Path):
        self.msg = f"\n\tError: Cannot locate the file \n{_file}?"
        super().__init__(self.msg)


# -----------------------------------------------------------------------------


def silent_print(_input: Any) -> None:
    """Default 'output' for XLConnection."""
    return


# -----------------------------------------------------------------------------


class XLConnection:
    """An Excel connection Facade / Interface."""

    def __init__(
        self,
        xl_framework,
        output: Callable[[str], Any] = silent_print,
        xl_file_path: Optional[pathlib.Path] = None,
    ) -> None:
        """Facade class for Excel Interop

        Arguments:
        ----------
            * xl (xl_Framework_Protocol): The Excel framework to use to interact with XL.

            * output (Callable[[str], Any]): The output function to use. Default is silent
                (no output), or provide the standard python 'print' for standard-out, etc.

            * xl_file_path (Optional[pathlib.Path]): The full path to an XL file to use. If none,
                will default to the 'active' xl workbook.
        """
        # -- Note: can not type-hint xl_framework in the Class argument line
        # -- cus' Python-3.7 doesn't have Protocols yet. It does see to work
        # -- when type-hinting the actual attribute though.
        self.xl: xl_Framework_Protocol = xl_framework
        self._output: Callable[[str], Any] = output
        self.xl_file_path: Optional[pathlib.Path] = xl_file_path

        self._wb: Optional[xl_Book_Protocol] = None
        self.output(f"> connected to excel doc: '{self.wb.fullname}'")

    def activate_new_workbook(self) -> xl_Book_Protocol:
        """Create a new blank workbook and set as the 'Active' book. Returns the new book."""
        new_book = self.books.add()
        self._wb = new_book
        return new_book

    @property
    def excel_running(self) -> bool:
        """Returns True if Excel is currently running, False if not"""
        return self.apps.count > 0

    def start_excel_app(self) -> Optional[xl_app_Protocol]:
        """Starts Excel Application, if it is not currently running."""
        if self.excel_running:
            return None

        print("adding a new app to the self.apps....")
        new_ap = self.apps.add()
        new_ap.visible = True

        if os.name == "nt":
            # Need to add a default workbook on Windows
            new_ap.books.add()

        return new_ap

    @property
    def apps(self) -> xl_apps_Protocol:
        """Return the xl framework 'apps' object."""
        return self.xl.apps

    @property
    def books(self) -> xl_Books_Protocol:
        """Return the xl framework 'books' object."""
        return self.xl.books

    @property
    def os_is_windows(self) -> bool:
        """Return True if the current OS is Windows. False if it is Mac/Linux"""
        return os.name == "nt"

    def get_workbook(self) -> xl_Book_Protocol:
        """Return the right Workbook, depending on the App state and user inputs."""
        if not self.excel_running:
            print("no Excel running, staring a new Application instance.")
            self.start_excel_app()

        # -- If a specific file path is provided, open that one
        if self.xl_file_path:
            if not self.xl_file_path.exists():
                raise NoSuchFileError(self.xl_file_path)
            return self.books.open(self.xl_file_path)

        # -- If no books are open yet, create a new one and return it
        if self.books.count == 0:
            return self.books.add()

        # -- Otherwise, just return the Active workbook
        return self.books.active

    @property
    def wb(self) -> xl_Book_Protocol:
        """Returns the Workbook of the active Excel Instance."""
        if self._wb is not None:  # -- Cache
            return self._wb
        else:
            self._wb = self.get_workbook()
            return self._wb

    def autofit_columns(self, _sheet_name: str) -> None:
        """Runs autofit on all the columns in a sheet."""
        sht = self.get_sheet_by_name(_sheet_name)
        sht.autofit(axis="c")  # by-columns

    def autofit_rows(self, _sheet_name: str) -> None:
        """Runs autofit on the rows in a sheet."""
        sht = self.get_sheet_by_name(_sheet_name)
        # sht.activate()
        sht.autofit(axis="r")  # by-rows

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

    def create_new_worksheet(
        self, _sheet_name: str, before: Optional[str] = None, after: Optional[str] = None
    ) -> None:
        """Try and add a new Worksheet to the Workbook."""
        try:
            self.wb.sheets.add(_sheet_name, before, after)
            self.output(f"Adding '{_sheet_name}' to Workbook")
        except ValueError:
            self.output(f"Worksheet '{_sheet_name}' already in Workbook.")

        self.get_sheet_by_name(_sheet_name).clear()

    def find_row(
        self,
        _search_item: xl_data.xl_range_single_value,
        _data: List[xl_data.xl_range_single_value],
        _start: int = 0,
    ) -> Optional[int]:
        for i, _ in enumerate(_data, start=_start):
            if _search_item == _:
                return i
        return None

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
        return {sh.name.upper() for sh in self.wb.sheets}

    def get_sheet_by_name(self, _sheet_name: Union[str, int]) -> xl_Sheet_Protocol:
        """Returns an Excel Sheet with the specified name, or KeyError if not found.

        Arguments:
        ----------
            * _sheet_name: (Union[str, int]): The excel sheet name or index num. to locate.

        Returns:
        --------
            * (xw.main.Sheet): The excel sheet found.
        """
        if str(_sheet_name).upper() not in self.get_worksheet_names():
            msg = f"Error: Key '{_sheet_name}' was not found in the Workbook '{self.wb.name}' Sheets?"
            raise KeyError(msg)

        return self.wb.sheets[_sheet_name]

    def get_last_sheet(self) -> xl_Sheet_Protocol:
        """Return the last Worksheet in the Workbook.

        Returns:
        --------
            * (xl_Sheet_Protocol) The last Worksheet in the Workbook.
        """
        return self.wb.sheets[-1]

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
        # sheet.activate()
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
    ) -> List[xl_data.xl_range_single_value]:
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

        if not _row_start:
            _row_start = 1
        if not _row_end:
            _row_end = self.get_last_used_row_num_in_column(_sheet_name, _col)

        address = f"{_col}{_row_start}:{_col}{_row_end}"
        self.output(f"Reading: '{address}' data on sheet: '{_sheet_name}'")

        sheet = self.get_sheet_by_name(_sheet_name)
        # sheet.activate()
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
        # sheet.activate()
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
        # sheet.activate()
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
    ) -> xl_data.xl_range_list2D_value:
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
            * _range: (str) The cell range to read from (ie: "A1") or a set of ranges (ie: "A1:B4")

        Returns:
        ---------
            * (xl_writable): The resultant value/values returned from excel.
        """
        self.output(f"Reading: {_sheet_name}:{_range}")
        return self.get_sheet_by_name(_sheet_name).range(_range).value

    def get_single_data_item(
        self, _sheet_name: str, _range: str
    ) -> xl_data.xl_range_single_value:
        """Return a single value from the Excel document.

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to read from.
            * _range: (str) The cell range to read from to (ie: "A1")

        Returns:
        ---------
            * (xl_writable): The resultant value returned from excel.
        """

        if ":" in _range:
            raise XlReadException(_range)
        self.output(f"Reading: {_sheet_name}:{_range}")
        return self.get_sheet_by_name(_sheet_name).range(_range).value  # type: ignore

    def get_data_by_columns(
        self, _sheet_name: str, _range_address: str
    ) -> List[List[xl_data.xl_range_single_value]]:
        """Returns a List of column data, each column in a list.
        ie: "A1:D12" -> [[A1, A2, ... A12], [B1, B2, ... B12], ... [D1, D2, ... D12]]

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to read from
            * _range_address: (str) The range read. ie: "A1:D56"

        Returns:
        --------
            * (List[List[xl_data.xl_range_single_value]])
        """
        sheet = self.get_sheet_by_name(_sheet_name)
        rng = sheet.range(_range_address).options(transpose=True)
        return rng.value  # type: ignore

    def get_data_with_column_letters(
        self, _sheet_name: str, _range_address: str
    ) -> Dict[str, List[xl_data.xl_range_single_value]]:
        """Returns a Dict of column data, key'd by the Column Letter.
        ie: "A1:D12"->{"A":[A1, A2,...A12], "B":[...], ..."D":[D1., D2,...D12]}

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to read from
            * _range_address: (str) The range read. ie: "A1:D56"

        Returns:
        --------
            * (Dict[str, List[xl_data.xl_range_single_value]])
        """

        raw_data = self.get_data_by_columns(_sheet_name, _range_address)

        # -- Shape the data into a dict, key'd by Column Letter
        # -- ie: {"P":["some", ...], "Q":["data", ...], ...}
        rng = self.xl.Range(_range_address)
        start_col_letter = xl_data.xl_col_num_as_chr(rng.column)
        start_col_number = xl_data.xl_ord(start_col_letter)
        return {
            xl_data.xl_chr(i): data_list
            for i, data_list in enumerate(raw_data, start=start_col_number)
        }

    def group_rows(self, _sheet_name: str, _row_start: int, _row_end: int) -> None:
        """Group one or more rows."""
        sht = self.get_sheet_by_name(_sheet_name)
        # sht.activate()
        if self.os_is_windows:
            sht.api.Rows(f"{_row_start}:{_row_end}").Group()
        else:
            sht.api.rows[f"{_row_start}:{_row_end}"].group()
        return None

    def hide_group_details(self, _sheet_name: str) -> None:
        """Hide (collapse) all the 'Groups' on the specified worksheet."""
        sheet = self.get_sheet_by_name(_sheet_name)
        if self.os_is_windows:
            pass
        else:
            sheet.api.outline_object.show_levels(row_levels=1)

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
            self._output(str(_input))
        except:
            # If _input=None, ignore...
            pass

    def unprotect_all_sheets(self) -> None:
        """Walk through all the sheets and unprotect them all."""
        for sheet in self.wb.sheets:
            if self.os_is_windows:
                sheet.api.Unprotect()
            else:
                sheet.api.unprotect()

    def write_xl_item(
        self,
        _xl_item: Union[xl_data.XlItem, xl_data.XLItem_List],
        _transpose: bool = False,
    ) -> None:
        """Writes a single XLItem to the worksheet

        Arguments:
        ---------
            * _xl_item: (XLItem) The XLItem with a sheet_name, range and value to write.
            * _transpose: (bool) Transpose the data before writing. Default=False. Set
                to true if you are passing in a list of items and want them to be
                written as rows instead of as columns.
        """

        self.output(
            f"Writing: {_xl_item.sheet_name}:{_xl_item.xl_range}={_xl_item.write_value}"
        )

        try:
            xl_sheet = self.get_sheet_by_name(_xl_item.sheet_name)
            xl_range = xl_sheet.range(_xl_item.xl_range).options(transpose=_transpose)
            xl_range.value = _xl_item.write_value  # type: ignore

            if _xl_item.has_color:
                if _xl_item.value_is_iterable:
                    # -- color all the columns
                    for i in range(len(_xl_item.write_value)):  # type: ignore
                        _xl_range = xl_range.offset(column_offset=i)
                        _xl_range.color = _xl_item.range_color
                        _xl_range.font.color = _xl_item.font_color
                else:
                    xl_range.color = _xl_item.range_color
                    xl_range.font.color = _xl_item.font_color

        except AttributeError as e:
            raise AttributeError(e)
        except Exception as e:
            raise WriteValueError(
                _xl_item.write_value, _xl_item.xl_range, _xl_item.sheet_name, e
            )
