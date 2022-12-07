# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a PHPP DHW Tank"""

from dataclasses import dataclass
from typing import List
from functools import partial

from PHX.model.hvac import water

from PHX.xl import xl_data
from PHX.PHPP.phpp_localization import shape_model


@dataclass
class TankInput:
    """Model class for a single DHW Tank input."""

    __slots__ = ("shape", "phx_tank", "tank_number")
    shape: shape_model.Dhw
    phx_tank: water.PhxHotWaterTank
    tank_number: int

    @property
    def input_column(self) -> str:
        """Return the right input column based on the tank-number."""
        return getattr(self.shape.tanks.input_columns, f"tank_{self.tank_number}")

    def create_range(self, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        return f"{self.input_column}{_row_num}"

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
        XLItemDHW = partial(xl_data.XlItem, _sheet_name)
        return [
            XLItemDHW(
                self.create_range(_row_num + self.shape.tanks.input_rows.tank_type.row),
                self.shape.tanks.tank_type.options[
                    str(self.phx_tank.params.tank_type.value)
                ],
            ),
            XLItemDHW(
                self.create_range(
                    _row_num + self.shape.tanks.input_rows.standby_losses.row
                ),
                self.phx_tank.params.standby_losses * self.phx_tank.quantity,
                "W/K",
                self.shape.tanks.input_rows.standby_losses.unit,
            ),
            XLItemDHW(
                self.create_range(
                    _row_num + self.shape.tanks.input_rows.storage_capacity.row
                ),
                self.phx_tank.params.storage_capacity * self.phx_tank.quantity,
                "LITER",
                self.shape.tanks.input_rows.storage_capacity.unit,
            ),
            XLItemDHW(
                self.create_range(
                    _row_num + self.shape.tanks.input_rows.standby_fraction.row
                ),
                self.phx_tank.params.standby_fraction,
            ),
            XLItemDHW(
                self.create_range(
                    _row_num + self.shape.tanks.input_rows.tank_location.row
                ),
                self.shape.tanks.tank_location.options[
                    str(int(self.phx_tank.params.in_conditioned_space))
                ],
            ),
            XLItemDHW(
                self.create_range(_row_num + self.shape.tanks.input_rows.water_temp.row),
                self.phx_tank.params.water_temp,
                "C",
                self.shape.tanks.input_rows.water_temp.unit,
            ),
        ]
