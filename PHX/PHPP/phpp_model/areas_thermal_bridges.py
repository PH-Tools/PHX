# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a PHPP Areas / Thermal Bridges-Entry row"""

from dataclasses import dataclass
from typing import List, Tuple
from functools import partial

from PHX.model import components

from PHX.xl import xl_data
from PHX.PHPP.phpp_localization import shape_model


@dataclass
class ThermalBridgeRow:
    """A single Areas/Thermal Bridge entry row."""

    __slots__ = ("shape", "phx_tb")
    shape: shape_model.Areas
    phx_tb: components.PhxComponentThermalBridge

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        return f"{getattr(self.shape.thermal_bridge_rows.inputs, _field_name).column}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.thermal_bridge_rows.inputs, _field_name).unit

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> List[xl_data.XlItem]:
        """Returns a list of the XL Items to write for this Thermal Bridge Entry

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to write to.
            * _row_num: (int) The row number to build the XlItems for
        Returns:
        --------
            * (List[XlItem]): The XlItems to write to the sheet.
        """
        create_range = partial(self._create_range, _row_num=_row_num)
        XLItemAreas = partial(xl_data.XlItem, _sheet_name)
        return [
            XLItemAreas(create_range("description"), self.phx_tb.display_name),
            XLItemAreas(create_range("group_number"), self.phx_tb.group_number.value),
            XLItemAreas(create_range("quantity"), self.phx_tb.quantity),
            XLItemAreas(
                create_range("length"),
                self.phx_tb.length,
                "M",
                self._get_target_unit("length"),
            ),
            XLItemAreas(
                create_range("psi_value"),
                self.phx_tb.psi_value,
                "W/MK",
                self._get_target_unit("psi_value"),
            ),
            XLItemAreas(create_range("fRsi_value"), self.phx_tb.fRsi_value),
        ]
