# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP Shading worksheet."""

from __future__ import annotations
from typing import Optional, Tuple, List

from PHX.to_PHPP import xl_app
from PHX.to_PHPP.phpp_model import shading_rows
from PHX.to_PHPP.phpp_localization import shape_model

class Shading:
    """IO Controller Class for PHPP "Shading" worksheet."""

    header_row: Optional[int] = None
    first_entry_row: Optional[int] = None
    end_entry_row: Optional[int] = None

    def __init__(self, _xl: xl_app.XLConnection, shape: shape_model.Shading):
        self.xl = _xl
        self.shape = shape

    def find_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.shading_rows.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end
        )

        for i,  val in enumerate(xl_data):
            if self.shape.shading_rows.locator_string_header == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.shading_rows.locator_string_header}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.shading_rows.locator_string_header}?"
        )

    def find_entry_row_start_end(self, _length:int=500) -> Tuple[int, int]:
        """Return the starting and ending rows for the shading data entry."""
        start_row = 17
        end_row = 168
        
        if not self.header_row:
            self.header_row = self.find_header_row()

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.shading_rows.locator_col_entry,
            _row_start=self.header_row,
            _row_end=self.header_row + _length
        )

        for i, val in enumerate(xl_data, start=self.header_row):
            if self.shape.shading_rows.locator_string_entry in str(val):
                start_row = i + 2
                break
        else:
            raise Exception(
                f"Error: Cannot find the '{self.shape.shading_rows.locator_string_entry}' "
                f"marker on the '{self.shape.name}' sheet, column {self.shape.shading_rows.locator_col_entry}?"
            )

        for i, val in enumerate(xl_data, start=self.header_row):
            if self.shape.shading_rows_end.locator_string_entry in str(val):
                end_row = i - 3
                break
        else:
            raise Exception(
                f"Error: Cannot find the '{self.shape.shading_rows_end.locator_string_entry}' "
                f"marker on the '{self.shape.name}' sheet, column {self.shape.shading_rows.locator_col_entry}?"
            )

        return (start_row, end_row)

    def find_section_shape(self) -> None:
        """Find the 'shape' of the Shading worksheet and set the instance attributes."""
        self.header_row = self.find_header_row()
        self.first_entry_row, self.end_entry_row = self.find_entry_row_start_end()
    
    def write_shading(self, _shading_rows: List[shading_rows.ShadingRow]) -> None:
        """Write a list of ShadingRow objects to the Shading worksheet."""
        if not self.first_entry_row or not self.end_entry_row:
            self.first_entry_row, self.end_entry_row = self.find_entry_row_start_end()

        for i, shading_row in enumerate(_shading_rows, start=self.first_entry_row):
            for item in shading_row.create_xl_items(self.shape.name, _row_num=i):
                self.xl.write_xl_item(item)