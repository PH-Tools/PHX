# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a PHPP DHW Tank"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from functools import partial

from PHX.model.hvac import water

from PHX.to_PHPP import xl_data
from PHX.to_PHPP.phpp_localization import shape_model

@dataclass
class TankInput:
    """Model class for a single DHW Tank input."""

    __slots__ = ('shape', 'phx_tank', 'tank_number')
    shape: shape_model.Dhw
    phx_tank: water.PhxHotWaterTank
    tank_number: int

    @property
    def input_column(self) -> str:
        """Return the right input column based on the tank-number."""
        return getattr(self.shape.tanks.input_columns, f"tank_{self.tank_number}")

    def create_range(self, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        return f'{self.input_column}{_row_num}'
    
    def create_xl_items(self, _sheet_name: str, _row_num: int) -> List[xl_data.XlItem]:
        """Returns a list of the XL Items to write for this DHW Tank

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to write to.
            * _row_num: (int) The row number to build the XlItems for
        Returns:
        --------
            * (List[XlItem]): The XlItems to write to the sheet.
        """
        items = [
            (self.create_range(_row_num+0), self.shape.tanks.tank_type.options[str(self.phx_tank.params.tank_type.value)]),
            (self.create_range(_row_num+5), self.phx_tank.params.standby_losses),
            (self.create_range(_row_num+6), self.phx_tank.params.storage_capacity),
            (self.create_range(_row_num+7), self.phx_tank.params.standby_fraction),
            (self.create_range(_row_num+9), self.shape.tanks.tank_location.options[str(int(self.phx_tank.params.in_conditioned_space))]),
            (self.create_range(_row_num+12), self.phx_tank.params.water_temp),
        ]

        return [xl_data.XlItem(_sheet_name, *item) for item in items]
