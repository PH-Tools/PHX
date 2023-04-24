# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a PHPP Components/Glazing row."""

from dataclasses import dataclass
from typing import List
from functools import partial

from PHX.model.constructions import PhxConstructionWindow

from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


@dataclass
class GlazingRow:
    """A single Areas/Surface entry row."""

    __slots__ = (
        "shape",
        "phx_construction",
    )
    shape: shape_model.Components
    phx_construction: PhxConstructionWindow

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.glazings.inputs, _field_name).column
        return f"{col}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.glazings.inputs, _field_name).unit

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
        XLItemCompo = partial(xl_data.XlItem, _sheet_name)
        xl_item_list: List[xl_data.XlItem] = [
            XLItemCompo(
                create_range("description"),
                self.phx_construction.glazing_type_display_name,
            ),
            XLItemCompo(create_range("g_value"), self.phx_construction.glass_g_value),
            XLItemCompo(
                create_range("u_value"),
                self.phx_construction.u_value_glass,
                "W/M2K",
                self._get_target_unit("u_value"),
            ),
        ]

        return xl_item_list
