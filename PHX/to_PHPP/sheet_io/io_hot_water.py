# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP "DHW+Distribution" worksheet."""

from __future__ import annotations
from typing import List

from PHX.to_PHPP import xl_app
from PHX.to_PHPP.phpp_localization import shape_model
from PHX.to_PHPP.phpp_model import hot_water_tank

class Tank:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape

class Tanks:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape 
        self.entry_start_row = 186

        self.tank_1 = Tank(self.xl, self.shape)
        self.tank_2 = Tank(self.xl, self.shape)

class HotWater:
    """IO Controller for the PHPP 'DHW+Distribution' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape
        self.tanks = Tanks(self.xl, self.shape)

    def write_tanks(self, _phpp_hw_tanks: List[hot_water_tank.TankInput]) -> None:
        for phpp_Tank_input in _phpp_hw_tanks:
            for item in phpp_Tank_input.create_xl_items(self.shape.name, self.tanks.entry_start_row):
                self.xl.write_xl_item(item)