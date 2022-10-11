# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP Windows worksheet."""

from __future__ import annotations
from typing import List, Optional, Tuple

from PHX.to_PHPP import xl_app, xl_data
from PHX.to_PHPP.xl_data import col_offset
from PHX.to_PHPP.phpp_model import windows_rows
from PHX.to_PHPP.phpp_localization import shape_model


class Windows:
    """IO Controller Class for PHPP "Windows" worksheet."""

    header_row: Optional[int] = None
    first_entry_row: Optional[int] = None
    end_entry_row: Optional[int] = None

    def __init__(self, _xl: xl_app.XLConnection, shape: shape_model.Windows):
        self.xl = _xl
        self.shape = shape

    def find_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.window_rows.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end
        )

        for i,  val in enumerate(xl_data):
            if self.shape.window_rows.locator_string_header == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.window_rows.locator_string_header}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.window_rows.locator_string_header}?"
        )

    def find_entry_row_start_end(self, _length:int=500) -> Tuple[int, int]:
        """Return the starting and ending rows for the window data entry."""
        start_row = 24
        end_row = 175
        
        if not self.header_row:
            self.header_row = self.find_header_row()

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.window_rows.locator_col_entry,
            _row_start=self.header_row,
            _row_end=self.header_row + _length
        )

        for i, val in enumerate(xl_data, start=self.header_row):
            if self.shape.window_rows.locator_string_entry in str(val):
                start_row = i + 2
                break
        else:
            raise Exception(
                f"Error: Cannot find the '{self.shape.window_rows.locator_string_entry}' "
                f"marker on the '{self.shape.name}' sheet, column {self.shape.window_rows.locator_col_entry}?"
            )

        for i, val in enumerate(xl_data, start=self.header_row):
            if self.shape.window_rows_end.locator_string_entry in str(val):
                end_row = i - 3
                break
        else:
            raise Exception(
                f"Error: Cannot find the '{self.shape.window_rows_end.locator_string_entry}' "
                f"marker on the '{self.shape.name}' sheet, column {self.shape.window_rows.locator_col_entry}?"
            )

        return (start_row, end_row)

    def find_section_shape(self) -> None:
        """Find the 'shape' of the Windows worksheet and set the instance attributes."""
        self.header_row = self.find_header_row()
        self.first_entry_row, self.end_entry_row = self.find_entry_row_start_end()

    def write_windows(self, _window_rows: List[windows_rows.WindowRow]) -> None:
        """Write a list of WindowRow objects to the Windows worksheet."""
        if not self.first_entry_row or not self.end_entry_row:
            self.first_entry_row, self.end_entry_row = self.find_entry_row_start_end()

        for i, window_row in enumerate(_window_rows, start=self.first_entry_row):
            for item in window_row.create_xl_items(self.shape.name, _row_num=i):
                self.xl.write_xl_item(item)

    def get_all_window_names(self) -> List[str]:
        """Return a list of all the window names found in the worksheet."""
        if not self.first_entry_row or not self.end_entry_row:
            self.first_entry_row, self.end_entry_row = self.find_entry_row_start_end()

        # Get all the window names from the description row
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.window_rows.inputs.description.column, # type: ignore
            _row_start=self.first_entry_row,
            _row_end=self.end_entry_row
        )

        return [str(_) for _ in xl_data if _]
    
    def activate_variants(self):
        """Set the frame and glass values to link to the Variants worksheet."""
        start_row, end_row = self.find_entry_row_start_end()
        
        for row_num in range(start_row, end_row):
            # -- Link Glazing to the variants type
            self.xl.write_xl_item(
                xl_data.XlItem(
                            self.shape.name,
                            f'{self.shape.window_rows.inputs.glazing_id.column}{row_num}',
                            f'={col_offset(str(self.shape.window_rows.inputs.variant_input.column), 1)}{row_num}',
                        )
            )

            # -- Link Frame to the variants type
            self.xl.write_xl_item(
                xl_data.XlItem(
                            self.shape.name,
                            f'{self.shape.window_rows.inputs.frame_id.column}{row_num}',
                            f'={col_offset(str(self.shape.window_rows.inputs.variant_input.column), 2)}{row_num}',
                        )
            )
