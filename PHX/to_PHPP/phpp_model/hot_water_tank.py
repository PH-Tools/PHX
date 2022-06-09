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

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        return
        col = getattr(self.shape.window_rows.input_columns, _field_name)
        return f'{col}{_row_num}'
    
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
        print('>>', self.phx_tank.params.storage_loss_rate)
        items = [
            ('J191', self.phx_tank.params.storage_loss_rate),
        ]

        return [xl_data.XlItem(_sheet_name, *item) for item in items]

        create_range = partial(self._create_range, _row_num=_row_num)
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (create_range('psi_i_left'), self.phx_construction.frame_left.psi_install),
        ]

