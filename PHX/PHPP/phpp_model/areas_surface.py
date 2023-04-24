# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a PHPP Areas / Surface-Entry row"""

from dataclasses import dataclass
from functools import partial
import re
from typing import List, Optional, Dict

from PHX.model import components, geometry
from PHX.model.enums.building import ComponentExposureExterior, ComponentFaceType

from PHX.xl import xl_data
from PHX.PHPP.phpp_localization import shape_model


@dataclass
class SurfaceRow:
    """A single Areas/Surface entry row."""

    __slots__ = ("shape", "phx_polygon", "phx_component", "phpp_assembly_id_name")
    shape: shape_model.Areas
    phx_polygon: geometry.PhxPolygon
    phx_component: components.PhxComponentOpaque
    phpp_assembly_id_name: Optional[str]

    @property
    def phpp_group_number(self) -> int:
        """Return the correct PHPP 'Group Number' depending on the exposure and type."""

        if self.phx_component.exposure_exterior == ComponentExposureExterior.SURFACE:
            return 18
        elif self.phx_component.face_type == ComponentFaceType.WALL:
            if self.phx_component.exposure_exterior == ComponentExposureExterior.EXTERIOR:
                return 8
            else:
                return 9
        elif self.phx_component.face_type == ComponentFaceType.FLOOR:
            return 11
        elif self.phx_component.face_type == ComponentFaceType.ROOF_CEILING:
            return 10
        else:
            return 12

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        return f"{getattr(self.shape.surface_rows.inputs, _field_name).column}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.surface_rows.inputs, _field_name).unit

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
        XLItemAreas = partial(xl_data.XlItem, _sheet_name)
        return [
            XLItemAreas(create_range("description"), self.phx_polygon.display_name),
            XLItemAreas(create_range("group_number"), self.phpp_group_number),
            XLItemAreas(create_range("quantity"), 1),
            XLItemAreas(
                create_range("area"),
                self.phx_polygon.area,
                "M2",
                self._get_target_unit("area"),
            ),
            XLItemAreas(create_range("assembly_id"), self.phpp_assembly_id_name),
            XLItemAreas(
                create_range("orientation"), self.phx_polygon.cardinal_orientation_angle
            ),
            XLItemAreas(create_range("angle"), self.phx_polygon.angle_from_horizontal),
            XLItemAreas(create_range("shading"), 0.5),
            XLItemAreas(create_range("absorptivity"), 0.6),
            XLItemAreas(create_range("emissivity"), 0.9),
        ]


@dataclass
class ExistingSurfaceRow:
    """The data from an existing PHPP Surface Entry row."""

    __slots__ = ("shape", "data", "group_type_exposure_map")
    shape: shape_model.Areas
    data: list
    group_type_exposure_map: Dict[int, str]  # From io_areas.Areas() parent class

    @property
    def name(self) -> str:
        l = self.shape.surface_rows.inputs.description.column
        i = xl_data.xl_ord(str(l)) - 65
        return self.data[i]

    @property
    def no_name(self) -> bool:
        """Return True if the name in the row-data is "-" or None."""
        return self.name == "-" or self.name is None

    @property
    def face_group_type_phpp_string(self) -> str:
        """Return the face's Group-Type string from the row-data."""
        col_letter = self.shape.surface_rows.inputs.group_number.column
        col_number_as_index = xl_data.xl_ord(str(col_letter)) - 65
        return str(self.data[col_number_as_index])

    @property
    def face_group_type_phpp_number(self) -> int:
        """Return the face's Group-Type number as an int from the Group-Type string."""
        result = re.split(r"\D+", self.face_group_type_phpp_string, 2)
        if not result:
            msg = f"Error getting Group-Type number? Could not find a number in the Group-Type string {self.face_group_type_phpp_string}?"
            raise Exception(msg)

        try:
            return int(result[0])
        except:
            msg = (
                f"Error getting Group-Type number? Could not convert {result[0]} to int?"
            )
            raise Exception(msg)

    @property
    def face_exposure_phpp_letter(self) -> str:
        """Return the face's exposure-type letter ("A", "B", etc..) based on the group_type_phpp_number"""
        return self.group_type_exposure_map[self.face_group_type_phpp_number]

    @property
    def face_type(self):
        """Return the face type enum (WALL, FLOOR, etc..) based on the group_type_phpp_number."""
        type_map = {
            2: ComponentFaceType.WINDOW,
            3: ComponentFaceType.WINDOW,
            4: ComponentFaceType.WINDOW,
            5: ComponentFaceType.WINDOW,
            6: ComponentFaceType.WINDOW,
            7: ComponentFaceType.WINDOW,
            8: ComponentFaceType.WALL,
            9: ComponentFaceType.WALL,
            10: ComponentFaceType.ROOF_CEILING,
            11: ComponentFaceType.FLOOR,
        }
        return type_map[self.face_group_type_phpp_number]

    @property
    def face_exposure(self):
        """Return the exposure type enum (EXTERIOR, GROUND, SURFACE) based on the face_exposure_phpp_letter"""
        type_map = {
            "A": ComponentExposureExterior.EXTERIOR,
            "B": ComponentExposureExterior.GROUND,
        }
        return type_map.get(
            self.face_exposure_phpp_letter, ComponentExposureExterior.SURFACE
        )
