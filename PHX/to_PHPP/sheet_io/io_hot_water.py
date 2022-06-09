# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP "DHW+Distribution" worksheet."""

from __future__ import annotations
from typing import List, Optional

from PHX.to_PHPP import xl_app
from PHX.to_PHPP.phpp_localization import shape_model
from PHX.to_PHPP.phpp_model import hot_water_tank

class Tank:
    """ An individual tank entry item."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape

    def find_entry_row_start(self, _row_start, num_rows=10) -> int:
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.tanks.locator_col_entry,
            _row_start=_row_start,
            _row_end=_row_start+num_rows
        )

        for i,  val in enumerate(xl_data, start=_row_start):
            if self.shape.tanks.locator_string_entry == val:
                return i + 2

        raise Exception(
            f"Error: Cannot find the '{self.shape.tanks.locator_string_entry}' "
            f"entry on the '{self.shape.name}' sheet, column {self.shape.tanks.locator_string_entry}?"
        )


class Tanks:
    """The Tanks (Storage Heat Loss) Section Group"""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape 
        self.header_row: Optional[int] = None
        self.entry_start_row: Optional[int] = None

        self.tank_1 = Tank(self.xl, self.shape)
        self.tank_2 = Tank(self.xl, self.shape)

    def find_header_row(self, _row_start: int = 150, _row_end: int = 200) -> int:
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.tanks.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end
        )

        for i,  val in enumerate(xl_data, start=_row_start):
            if self.shape.tanks.locator_string_header == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.tanks.locator_string_header}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.tanks.locator_string_header}?"
        )

    def find_entry_row_start(self) -> int:
        if not self.header_row:
            self.header_row = self.find_header_row()
        return self.tank_1.find_entry_row_start(self.header_row)


class HotWater:
    """IO Controller for the PHPP 'DHW+Distribution' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape
        self.tanks = Tanks(self.xl, self.shape)

    def write_tanks(self, _phpp_hw_tanks: List[hot_water_tank.TankInput]) -> None:
        if not self.tanks.entry_start_row:
            self.tanks.entry_start_row = self.tanks.find_entry_row_start()
    
        for phpp_Tank_input in _phpp_hw_tanks:
            for item in phpp_Tank_input.create_xl_items(self.shape.name, self.tanks.entry_start_row):
                self.xl.write_xl_item(item)