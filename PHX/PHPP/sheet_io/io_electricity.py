# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP 'Electricity' worksheet."""

from __future__ import annotations
from typing import List

from PHX.xl import xl_data
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import electricity_item
from PHX.xl import xl_app


class Electricity:
    """IO Controller for PHPP "Electricity" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, shape: shape_model.Electricity):
        self.xl = _xl
        self.shape = shape

    def _turn_off_all_equipment(self):
        """Sets all the 'used' values to 0 to reset the sheet before writing new equipment."""
        for item in self.shape.input_rows:
            # Some items cannot be turned off....
            excluded = [
                "clothes_drying",
                "cooking",
                "consumer_elec",
                "lighting",
                "small_appliances",
            ]
            if item[0] in excluded:
                continue

            self.xl.write_xl_item(
                xl_data.XlItem(
                    self.shape.name, f"{self.shape.input_columns.used}{item[1].data}", 0
                )
            )

    def write_equipment(
        self, _equipment_inputs: List[electricity_item.ElectricityItem]
    ) -> None:
        """Write a list of equipment-input objects to the Worksheet."""
        self._turn_off_all_equipment()

        for equip_input in _equipment_inputs:
            for item in equip_input.create_xl_items(self.shape):
                self.xl.write_xl_item(item)
