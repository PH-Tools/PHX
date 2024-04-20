# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Model class for a PHPP Windows/Window-Entry row"""

from dataclasses import dataclass
from functools import partial
from typing import List, Optional, Tuple

from PHX.model import constructions, geometry
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


def get_name_from_glazing_id(
    _phpp_glazing_id: Optional[xl_data.xl_range_single_value],
) -> str:
    """Return the aperture's PHPP-Name (ie: "MyGlass") from phpp-id-string."""
    try:
        return str(_phpp_glazing_id).split("-", 1)[1]
    except:
        if _phpp_glazing_id == None or _phpp_glazing_id == "None":
            return ""
        else:
            msg = f"Error getting construction PHPP-Name? " f"Could not split {_phpp_glazing_id} on '-'?"
            raise Exception(msg)


@dataclass
class WindowRow:
    """Model class for a single Window entry row."""

    __slots__ = (
        "shape",
        "phx_polygon",
        "phx_construction",
        "phpp_host_surface_id_name",
        "phpp_id_frame",
        "phpp_id_glazing",
        "phpp_id_variant_type",
    )
    shape: shape_model.Windows
    phx_polygon: geometry.PhxPolygonRectangular
    phx_construction: constructions.PhxConstructionWindow
    phpp_host_surface_id_name: Optional[str]
    phpp_id_frame: Optional[str]
    phpp_id_glazing: Optional[str]
    phpp_id_variant_type: Optional[str]

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.window_rows.inputs, _field_name).column
        return f"{col}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.window_rows.inputs, _field_name).unit

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
        XLItemWindows = partial(xl_data.XlItem, _sheet_name)
        items: List[xl_data.XlItem] = [
            XLItemWindows(create_range("variant_input"), self.phpp_id_variant_type),
            XLItemWindows(create_range("quantity"), 1),
            XLItemWindows(create_range("description"), f"'{self.phx_polygon.display_name}"),
            XLItemWindows(create_range("host"), self.phpp_host_surface_id_name),
            XLItemWindows(create_range("glazing_id"), self.phpp_id_glazing),
            XLItemWindows(create_range("frame_id"), self.phpp_id_frame),
            XLItemWindows(
                create_range("width"),
                self.phx_polygon.width,
                "M",
                self._get_target_unit("width"),
            ),
            XLItemWindows(
                create_range("height"),
                self.phx_polygon.height,
                "M",
                self._get_target_unit("height"),
            ),
            # -- TODO: Install condition, not Psi-Install
            XLItemWindows(create_range("psi_i_left"), self.phx_construction.frame_left.psi_install),
            XLItemWindows(
                create_range("psi_i_right"),
                self.phx_construction.frame_right.psi_install,
            ),
            XLItemWindows(
                create_range("psi_i_bottom"),
                self.phx_construction.frame_bottom.psi_install,
            ),
            XLItemWindows(create_range("psi_i_top"), self.phx_construction.frame_top.psi_install),
        ]

        items_merged = xl_data.merge_xl_item_row(items)

        return items_merged
