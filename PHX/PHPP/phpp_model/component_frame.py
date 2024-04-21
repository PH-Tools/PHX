# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Model class for a PHPP Components/Window-Frame row."""

from dataclasses import dataclass
from functools import partial
from typing import List

from PHX.model import constructions
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


@dataclass
class FrameRow:
    """A single Areas/Surface entry row."""

    __slots__ = (
        "shape",
        "phx_construction",
    )
    shape: shape_model.Components
    phx_construction: constructions.PhxConstructionWindow

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.frames.inputs, _field_name).column
        return f"{col}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.frames.inputs, _field_name).unit

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
                f"'{self.phx_construction.frame_type_display_name}",
            ),
            XLItemCompo(
                create_range("u_value_left"),
                self.phx_construction.frame_left.u_value,
                "W/M2K",
                self._get_target_unit("u_value_left"),
            ),
            XLItemCompo(
                create_range("u_value_right"),
                self.phx_construction.frame_right.u_value,
                "W/M2K",
                self._get_target_unit("u_value_right"),
            ),
            XLItemCompo(
                create_range("u_value_bottom"),
                self.phx_construction.frame_bottom.u_value,
                "W/M2K",
                self._get_target_unit("u_value_bottom"),
            ),
            XLItemCompo(
                create_range("u_value_top"),
                self.phx_construction.frame_top.u_value,
                "W/M2K",
                self._get_target_unit("u_value_top"),
            ),
            XLItemCompo(
                create_range("width_left"),
                self.phx_construction.frame_left.width,
                "M",
                self._get_target_unit("width_left"),
            ),
            XLItemCompo(
                create_range("width_right"),
                self.phx_construction.frame_right.width,
                "M",
                self._get_target_unit("width_right"),
            ),
            XLItemCompo(
                create_range("width_bottom"),
                self.phx_construction.frame_bottom.width,
                "M",
                self._get_target_unit("width_bottom"),
            ),
            XLItemCompo(
                create_range("width_top"),
                self.phx_construction.frame_top.width,
                "M",
                self._get_target_unit("width_top"),
            ),
            XLItemCompo(
                create_range("psi_g_left"),
                self.phx_construction.frame_left.psi_glazing,
                "W/MK",
                self._get_target_unit("psi_g_left"),
            ),
            XLItemCompo(
                create_range("psi_g_right"),
                self.phx_construction.frame_right.psi_glazing,
                "W/MK",
                self._get_target_unit("psi_g_right"),
            ),
            XLItemCompo(
                create_range("psi_g_bottom"),
                self.phx_construction.frame_bottom.psi_glazing,
                "W/MK",
                self._get_target_unit("psi_g_bottom"),
            ),
            XLItemCompo(
                create_range("psi_g_top"),
                self.phx_construction.frame_top.psi_glazing,
                "W/MK",
                self._get_target_unit("psi_g_top"),
            ),
            XLItemCompo(
                create_range("psi_i_left"),
                self.phx_construction.frame_left.psi_install,
                "W/MK",
                self._get_target_unit("psi_i_left"),
            ),
            XLItemCompo(
                create_range("psi_i_right"),
                self.phx_construction.frame_right.psi_install,
                "W/MK",
                self._get_target_unit("psi_i_right"),
            ),
            XLItemCompo(
                create_range("psi_i_bottom"),
                self.phx_construction.frame_bottom.psi_install,
                "W/MK",
                self._get_target_unit("psi_i_bottom"),
            ),
            XLItemCompo(
                create_range("psi_i_top"),
                self.phx_construction.frame_top.psi_install,
                "W/MK",
                self._get_target_unit("psi_i_top"),
            ),
        ]

        return xl_item_list
