# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a single PHPP Addition Vent / Unit-Entry row."""

from dataclasses import dataclass
from typing import List
from functools import partial

from PHX.model import hvac
from PHX.xl import xl_data
from PHX.PHPP.phpp_localization import shape_model


@dataclass
class VentUnitRow:
    """Model class for a single Ventilation Unit entry row."""

    __slots__ = ("shape", "phx_vent_sys", "phpp_id_ventilator")
    shape: shape_model.AddnlVent
    phx_vent_sys: hvac.PhxDeviceVentilator
    phpp_id_ventilator: str

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.units.inputs, _field_name).column
        return f"{col}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.units.inputs, _field_name).unit

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

        create_range = partial(self._create_range, _row_num=_row_num)
        XLItemVentUnit = partial(xl_data.XlItem, _sheet_name)
        items: List[xl_data.XlItem] = [
            XLItemVentUnit(create_range("quantity"), self.phx_vent_sys.quantity),
            XLItemVentUnit(create_range("display_name"), self.phx_vent_sys.display_name),
            XLItemVentUnit(create_range("unit_selected"), self.phpp_id_ventilator),
            XLItemVentUnit(
                create_range("temperature_below_defrost_used"),
                self.phx_vent_sys.params.temperature_below_defrost_used,
                "C",
                self._get_target_unit("temperature_below_defrost_used"),
            ),
        ]
        return items
