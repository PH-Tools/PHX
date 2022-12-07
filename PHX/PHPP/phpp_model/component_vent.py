# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a PHPP Components/Window-Frame row."""

from dataclasses import dataclass
from typing import List, Tuple
from functools import partial

from PHX.model import hvac

from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


@dataclass
class VentilatorRow:
    """A single Ventilator Component entry row."""

    __slots__ = (
        "shape",
        "phx_vent_sys",
    )
    shape: shape_model.Components
    phx_vent_sys: hvac.AnyPhxVentilation

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.ventilators.inputs, _field_name).column
        return f"{col}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.ventilators.inputs, _field_name).unit

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> List[xl_data.XlItem]:
        """Returns a list of the XL Items to write for this Surface Entry

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to write to.
            * _row_num: (int) The row number to build the XlItems for
        Returns:
        --------
            * (List[XlItem]): The XlItems to write to the sheet.
        """

        def _frost(_reqd: bool) -> str:
            if _reqd:
                return "yes"
            return "no"

        create_range = partial(self._create_range, _row_num=_row_num)
        XLItemCompo = partial(xl_data.XlItem, _sheet_name)
        params = self.phx_vent_sys.params
        items: List[xl_data.XlItem] = [
            XLItemCompo(create_range("display_name"), self.phx_vent_sys.display_name),
            XLItemCompo(
                create_range("sensible_heat_recovery"), params.sensible_heat_recovery
            ),
            XLItemCompo(
                create_range("latent_heat_recovery"), params.latent_heat_recovery
            ),
            XLItemCompo(
                create_range("electric_efficiency"),
                params.electric_efficiency,
                "WH/M3",
                self._get_target_unit("electric_efficiency"),
            ),
            XLItemCompo(
                create_range("frost_protection_reqd"),
                _frost(params.frost_protection_reqd),
            ),
        ]

        return items
