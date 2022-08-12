# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Data-entry constructor for the U-Values Worksheet."""

from dataclasses import dataclass
from typing import List, Optional
from functools import partial

from PHX.model import constructions

from PHX.to_PHPP import xl_data
from PHX.to_PHPP.phpp_localization import shape_model


@dataclass
class ConstructorBlock:
    """A single U-Value/Constructor entry block."""

    __slots__ = ("shape", "phx_construction")
    shape: shape_model.UValues
    phx_construction: constructions.PhxConstructionOpaque

    def _create_range(self, _field_name: str, _row_offset: int, _start_row: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.constructor.inputs, _field_name).column
        return f'{col}{_start_row + _row_offset}'
    
    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.constructor.inputs, _field_name).unit

    def create_xl_items(self, _sheet_name: str, _start_row: int) -> List[xl_data.XlItem]:
        """Convert the PHX-Construction into a list of XLItems for writing to the PHPP."""
                
        create_range = partial(self._create_range, _start_row=_start_row)
        XLItemUValues = partial(xl_data.XlItem, _sheet_name)

        # -- Build the basic assembly attributes
        xl_items_list: List[xl_data.XlItem] = [
            XLItemUValues(create_range('display_name', 2), self.phx_construction.display_name),
            XLItemUValues(create_range('r_si', 4), 0.0, "M2K/W", self._get_target_unit('r_si')),
            XLItemUValues(create_range('r_se', 5), 0.0, "M2K/W", self._get_target_unit('r_se')),
        ]

        # -- Build all the layers of the assembly
        for i, layer in enumerate(self.phx_construction.layers, start=8):
            layer_items: List[xl_data.XlItem] = [
                XLItemUValues(create_range('sec_1_description', i),
                    layer.material.display_name),
                XLItemUValues(create_range('sec_1_conductivity', i),
                    layer.material.conductivity,
                    "W/MK",
                    self._get_target_unit('sec_1_conductivity')
                ),
                XLItemUValues(create_range(
                    'thickness', i),
                    layer.thickness_mm,
                    "MM",
                    self._get_target_unit('thickness')
                ),
            ]
            xl_items_list.extend(layer_items)

        return xl_items_list

