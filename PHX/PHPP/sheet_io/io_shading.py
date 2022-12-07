# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP Shading worksheet."""

from __future__ import annotations
from typing import Optional, List

from PHX.xl import xl_app
from PHX.PHPP.phpp_model import shading_rows
from PHX.PHPP.phpp_localization import shape_model


class Shading:
    """IO Controller Class for PHPP "Shading" worksheet."""

    _header_row: Optional[int] = None
    _entry_row_start: Optional[int] = None
    _entry_row_end: Optional[int] = None

    def __init__(self, _xl: xl_app.XLConnection, shape: shape_model.Shading):
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

    def find_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.shading_rows.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data):
            if self.shape.shading_rows.locator_string_header == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.shading_rows.locator_string_header}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.shading_rows.locator_string_header}?"
        )

    def find_entry_block_start(self, _start_row: int = 1, _read_length: int = 100) -> int:
        """Return the starting row for the window data entry block."""

        end_row = _start_row + _read_length
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.shading_rows.locator_col_entry,
            _row_start=_start_row,
            _row_end=end_row,
        )

        for i, val in enumerate(xl_data, start=_start_row):
            if self.shape.shading_rows.locator_string_entry in str(val):
                return i + 2

        if end_row < 10_000:
            return self.find_entry_block_start(_start_row=end_row, _read_length=1_000)

        raise Exception(
            f"Error: Cannot find the '{self.shape.shading_rows.locator_string_entry}' "
            f"marker on the '{self.shape.name}' sheet, column {self.shape.shading_rows.locator_col_entry}?"
        )

    def find_entry_block_end(self, _start_row: int = 1, _read_length: int = 100) -> int:
        """Return the ending row for the window data entry block."""

        end_row = _start_row + _read_length
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.shading_rows_end.locator_col_entry,
            _row_start=_start_row,
            _row_end=end_row,
        )

        for i, val in enumerate(xl_data, start=_start_row):
            if self.shape.shading_rows_end.locator_string_entry in str(val):
                return i + 2

        if end_row < 10_000:
            return self.find_entry_block_end(_start_row=end_row, _read_length=1_000)

        raise Exception(
            f"Error: Cannot find the '{self.shape.shading_rows_end.locator_string_entry}' "
            f"marker on the '{self.shape.name}' sheet, column {self.shape.shading_rows_end.locator_col_entry}?"
        )

    def write_shading(self, _shading_rows: List[shading_rows.ShadingRow]) -> None:
        """Write a list of ShadingRow objects to the Shading worksheet."""

        for i, shading_row in enumerate(_shading_rows, start=self.entry_row_start):
            for item in shading_row.create_xl_items(self.shape.name, _row_num=i):
                self.xl.write_xl_item(item)
