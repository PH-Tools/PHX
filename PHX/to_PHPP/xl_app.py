# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Class for managing the XL-Connection and common read/write operations."""

from typing import Optional, List, Set, Callable, Any
from contextlib import contextmanager
import os

import xlwings as xw

from PHX.to_PHPP import xl_data

# -----------------------------------------------------------------------------

class SupportsString:
    """An object which can be stringified."""

    def __str__(self): ...

# -----------------------------------------------------------------------------


class ReadRowsError(Exception):
    def __init__(self, row_start, row_end):
        self.msg = f'Error: row_start should be less than row_end. Got {row_start}, {row_end}'
        super().__init__(self.msg)


class NoActiveExcelRunningError(Exception):
    def __init__(self):
        self.msg = '\n\tError: No active instance of Excel running? Please open a valid PHPP file and try again.'
        super().__init__(self.msg)


class ReadMultipleColumnsError(Exception):
    def __init__(self, _c1, _c2):
        self.msg = f'\n\tError: Cannot use "read_multiple_columns()" with _col_start={_c1}'\
            f'and _col_end={_c2}. Please use "read_single_column()" instead.'
        super().__init__(self.msg)


class WriteValueError(Exception):
    def __init__(self, _value, _range, _worksheet, _e):
        self.msg = "\n\n\tSomething went wrong trying to write the value: '{}' to the cell: '{}' on worksheet: '{}'. Please "\
                    "make sure that a valid PHPP file is open, and both the worksheet and workbook are unprotected.\n\n{}".format(
                         _value, _range, _worksheet, _e
                    )
        super().__init__(self.msg)


# -----------------------------------------------------------------------------


class XLConnection:

    def __init__(self, _output: Optional[Callable]=None):
        """Facade class for Excel Interop
            
        Arguments:
        ----------
            * _log: Optional[Callable]: The output functions to use. Input None for silent.
        """
    
        self._output = _output

    def output(self, _input: SupportsString):
        """Used to set the output method. Default is None (silent).
        
        Arguments:
        ----------
            * _input (SupportsString): The string to output.
        
        Returns:
        --------
            *
        """
        try:
            self._output(str(_input))
        except:
            pass

    @property
    def wb(self) -> xw.main.Book:
        try:
            return xw.books.active
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
            self.wb.app.calculation = 'manual'
            yield
        finally:
            self.wb.app.screen_updating = True
            self.wb.app.display_alerts = True
            self.wb.app.calculation = 'automatic'
            self.wb.app.calculate()

    def connection_is_open(self) -> bool:
        if not self.wb:
            return False
        return True

    def unprotect_all_sheets(self) -> None:
        """Walk through all the sheets and unprotect them all."""
        for sheet in self.wb.sheets:
            if os.name != 'nt':
                sheet.api.unprotect()
            else:
                sheet.api.Unprotect()

    def get_row_num_of_value_in_column(self, sheet_name: str, row_start: int,
                                       row_end: int,  col: str, find: str) -> Optional[int]:
        """Returns the row number of the first instance of a specific value found within a column, or None if not found.

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
        sh: xw.main.Sheet = self.get_sheet_by_name(sheet_name)

        while row <= row_end:
            if sh.range(f'{col}{row}').value != find:
                row += 1
            else:
                return row
        return None

    def get_worksheet_names(self) -> Set[str]:
        """Return a list of all the worksheet names in the workbook.
            
        Returns:
        --------
            * (List[str])
        """
        return {sh.name for sh in self.wb.sheets}

    def get_sheet_by_name(self, _sheet_name: str) -> xw.main.Sheet:
        """Returns an Excel Sheet with the specified name, or KeyError if not found.

        Arguments:
        ----------
            * _sheet_name: (str): The excel sheet name to locate.

        Returns:
        --------
            * (xw.main.Sheet): The excel sheet found.
        """
        return self.wb.sheets[_sheet_name]

    def get_single_column_data(self, _sheet_name: str, _col: str, _row_start: int = 1,
                               _row_end: int = 100, ) -> List[xl_data.xl_range_value]:
        """Return a list with the values read from a single column of the excel document.

        Arguments:
        ----------
            * _sheet_name: (str) The Excel Worksheet to read from.
            * _col: (str) The Column letter to read.
            * _row_start: (int) default=1
            * _row_end: (int) default=100
        Returns:
        --------
            (List[xl_range_value]): The data from Excel worksheet, as a list.
        """

        return self.get_sheet_by_name(_sheet_name).range(f'{_col}{_row_start}:{_col}{_row_end}').value

    def get_single_row_data(self, _sheet_name: str, _row_number: int) -> List[xl_data.xl_range_value]:
        """
        
        Arguments:
        ----------
            * _sheet_name (str): The name of the sheet to read
            * _row_number (int): The row to read
        
        Returns:
        --------
            * (List[xl_data.xl_range_value]) The data read from XL.
        """

        sht = self.get_sheet_by_name(_sheet_name)
        return sht.range((_row_number, 1),(_row_number, 500)).value

    def get_multiple_column_data(self, _sheet_name: str, _col_start: str, _col_end: str,
                                 _row_start: int = 1, _row_end: int = 100, ) -> List[List[xl_data.xl_range_value]]:
        """Return a list with the values read from a specified block of the xl document.

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

        # -- Use XW instead of ord() since ord('KL') and similar will fail
        rng = xw.Range(f'{_col_end}1:{_col_start}1')
        _ndim = len(rng.columns)

        return self.get_sheet_by_name(_sheet_name).range(
            f'{_col_start}{_row_start}:{_col_end}{_row_end}').options(ndim=_ndim).value

    def get_data(self, _sheet_name: str, _range: str) -> xl_data.xl_writable:
        """Return a value or values from Excel

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to read from.
            * _range: (str) The cell range to write to (ie: "A1") or a set of ranges (ie: "A1:B4")

        Returns:
        ---------
            * (xl_writable): The resultant value/values returned from excel.
        """
        self.output(f'Reading: {_sheet_name}:{_range}')
        return self.get_sheet_by_name(_sheet_name).range(_range).value

    def write_xl_item(self, _xl_item: xl_data.XlItem) -> None:
        """Writes a single XLItem to the worksheet

        Arguments:
        ---------
            * _xl_item: (XLItem) The XLItem with a sheet_name, range and value to write.
         """
        try:
            self.output(f'Writing {_xl_item.write_value} to {_xl_item.sheet_name}:{_xl_item.xl_range}')
            self.get_sheet_by_name(_xl_item.sheet_name).range(
                _xl_item.xl_range).value = _xl_item.write_value
        except Exception as e:
            raise WriteValueError(_xl_item.write_value, _xl_item.xl_range, _xl_item.sheet_name, e)

    def clear_data(self, _sheet_name: str, _range: str) -> None:
        """Sets the specified excel sheet's range to 'None'

        Arguments:
        ---------
            * _sheet_name: (str) The name of the sheet to write to
            * _range: (str) The cell range to write to (ie: "A1") or a set of ranges (ie: "A1:B4")
         """
        self.get_sheet_by_name(_sheet_name).range(_range).value = None
