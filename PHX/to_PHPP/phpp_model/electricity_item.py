# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a PHPP Electricity / Equipment row input."""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Any
from functools import partial

from PHX.model import elec_equip

from PHX.to_PHPP import xl_data
from PHX.to_PHPP.phpp_localization import shape_model


@dataclass
class ElectricityItem:
    """Model class for a single Electric-Equipment item entry row."""

    __slots__ = ('phx_equipment')
    phx_equipment: Any

    def create_xl_items(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        if isinstance(self.phx_equipment, elec_equip.PhxDeviceDishwasher):
            return self._dishwasher(_shape)
        else:
            return []
    
    def _dishwasher(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceDishwasher = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            ('F14', 1),
            ('H14', str(int(equip.in_conditioned_space))),
            ('J14', equip.energy_demand_per_use),
            ('D15', _shape.input_rows.dishwasher.selection_options[str(equip.water_connection)]),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]
    
    # def _create_range(self, _field_name: str, _row_num: int) -> str:
    #     """Return the XL Range ("P12",...) for the specific field name."""
    #     col = getattr(self.shape.window_rows.input_columns, _field_name)
    #     return f'{col}{_row_num}'

    # def create_xl_items(self, _sheet_name: str) -> List[xl_data.XlItem]:
    #     """Returns a list of the XL Items to write for this Surface Entry

    #     Arguments:
    #     ----------
    #         * _sheet_name: (str) The name of the worksheet to write to.
    #         * _row_num: (int) The row number to build the XlItems for
    #     Returns:
    #     --------
    #         * (List[XlItem]): The XlItems to write to the sheet.
    #     """
    #     if isinstance(self.phx_equipment, elec_equip.PhxDeviceDishwasher):
    #         return self.dishwasher(_sheet_name)
    #     else:
    #         return []


