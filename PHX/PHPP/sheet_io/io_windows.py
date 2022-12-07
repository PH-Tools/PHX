# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP Windows worksheet."""

from __future__ import annotations
from typing import List, Optional

from PHX.xl import xl_data
from PHX.xl.xl_data import col_offset
from PHX.PHPP.phpp_model import windows_rows
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_app


class Windows:
    """IO Controller Class for PHPP "Windows" worksheet."""

    _header_row: Optional[int] = None
    _entry_row_start: Optional[int] = None
    _entry_row_end: Optional[int] = None

    def __init__(self, _xl: xl_app.XLConnection, shape: shape_model.Windows):
        self.xl = _xl
        self.shape = shape

    @property
    def header_row(self) -> int:
        """The row number for the Window entry 'Header'."""
        if not self._header_row:
            self._header_row = self.find_header_row()
        return self._header_row

    @property
    def entry_row_start(self) -> int:
        if not self._entry_row_start:
            self._entry_row_start = self.find_entry_block_start()
        return self._entry_row_start

    @property
    def entry_row_end(self) -> int:
        if not self._entry_row_end:
            self._entry_row_end = self.find_entry_block_end()
        return self._entry_row_end

    def find_header_row(self, _row_start: int = 1, _read_length: int = 100) -> int:
        """Return the row number for the Window entry section 'Header'"""

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.window_rows.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_start + _read_length,
        )

        for i, val in enumerate(xl_data):
            if self.shape.window_rows.locator_string_header == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.window_rows.locator_string_header}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.window_rows.locator_string_header}?"
        )

    def find_entry_block_start(self, _start_row: int = 1, _read_length: int = 100) -> int:
        """Return the starting row for the window data entry block."""

        end_row = _start_row + _read_length
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.window_rows.locator_col_entry,
            _row_start=_start_row,
            _row_end=end_row,
        )

        for i, val in enumerate(xl_data, start=_start_row):
            if self.shape.window_rows.locator_string_entry in str(val):
                return i + 2

        if end_row < 10_000:
            return self.find_entry_block_start(_start_row=end_row, _read_length=1_000)

        raise Exception(
            f"Error: Cannot find the '{self.shape.window_rows.locator_string_entry}' "
            f"marker on the '{self.shape.name}' sheet, column {self.shape.window_rows.locator_col_entry}?"
        )

    def find_entry_block_end(self, _start_row: int = 1, _read_length: int = 100) -> int:
        """Return the ending row for the window data entry block."""

        end_row = _start_row + _read_length
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.window_rows.locator_col_entry,
            _row_start=_start_row,
            _row_end=end_row,
        )

        for i, val in enumerate(xl_data, start=_start_row):
            if self.shape.window_rows_end.locator_string_entry in str(val):
                return i + 2

        if end_row < 10_000:
            return self.find_entry_block_end(_start_row=end_row, _read_length=1_000)

        raise Exception(
            f"Error: Cannot find the '{self.shape.window_rows_end.locator_string_entry}' "
            f"marker on the '{self.shape.name}' sheet, column {self.shape.window_rows_end.locator_col_entry}?"
        )

    def write_windows(self, _window_rows: List[windows_rows.WindowRow]) -> None:
        """Write a list of WindowRow objects to the Windows worksheet."""
        for i, window_row in enumerate(_window_rows, start=self.entry_row_start):
            for item in window_row.create_xl_items(self.shape.name, _row_num=i):
                self.xl.write_xl_item(item)

    def get_all_window_names(self) -> List[str]:
        """Return a list of all the window names found in the worksheet."""

        # -- Get all the window names from the description row
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.window_rows.inputs.description.column,  # type: ignore
            _row_start=self.entry_row_start,
            _row_end=self.entry_row_end,
        )

        return [str(_) for _ in xl_data if _]

    def activate_variants(self):
        """Set the frame and glass values to link to the Variants worksheet."""

        for row_num in range(self.entry_row_start, self.entry_row_end):
            # -- Link Glazing to the variants type
            self.xl.write_xl_item(
                xl_data.XlItem(
                    self.shape.name,
                    f"{self.shape.window_rows.inputs.glazing_id.column}{row_num}",
                    f"={col_offset(str(self.shape.window_rows.inputs.variant_input.column), 1)}{row_num}",
                )
            )

            # -- Link Frame to the variants type
            self.xl.write_xl_item(
                xl_data.XlItem(
                    self.shape.name,
                    f"{self.shape.window_rows.inputs.frame_id.column}{row_num}",
                    f"={col_offset(str(self.shape.window_rows.inputs.variant_input.column), 2)}{row_num}",
                )
            )
