# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP 'Electricity' worksheet."""

from __future__ import annotations
from typing import List

from PHX.to_PHPP import xl_app
from PHX.to_PHPP.phpp_localization import shape_model
from PHX.to_PHPP.phpp_model import electricity_item

class Electricity:
    """IO Controller for PHPP "Electricity" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, shape: shape_model.Electricity):
        self.xl = _xl
        self.shape = shape

    def write_equipment(self, _equipment_inputs: List[electricity_item.ElectricityItem]) -> None:
        """Write a list of equipment-input objects to the Worksheet."""
        for equip_input in _equipment_inputs:
            print(equip_input.create_xl_items(self.shape))
        
        return None