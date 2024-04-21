# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Model class for a PHPP Areas / Surface-Entry row"""

import re
from dataclasses import dataclass
from functools import partial
from typing import Dict, List, Optional

from PHX.model import components, geometry
from PHX.model.enums.building import ComponentExposureExterior, ComponentFaceType
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import version
from PHX.xl import xl_data


@dataclass
class SurfaceRow:
    """A single Areas/Surface entry row."""

    __slots__ = ("shape", "phx_polygon", "phx_component", "phpp_assembly_id_name", "phpp_version")
    shape: shape_model.Areas
    phx_polygon: geometry.PhxPolygon
    phx_component: components.PhxComponentOpaque
    phpp_assembly_id_name: Optional[str]
    phpp_version: version.PHPPVersion

    @property
    def phpp_group_number_format(self) -> str:
        """Return the correct PHPP 'Group Format' depending on the PHPP version."""
        if self.phpp_version.number_major == "9":
            return "{}"
        else:
            return "{}-"

    @property
    def phpp_group_number(self) -> str:
        """Return the correct PHPP 'Group Number' depending on the exposure and type."""

        if self.phx_component.exposure_exterior == ComponentExposureExterior.SURFACE:
            return self.phpp_group_number_format.format(18)
        elif self.phx_component.face_type == ComponentFaceType.WALL:
            if self.phx_component.exposure_exterior == ComponentExposureExterior.EXTERIOR:
                return self.phpp_group_number_format.format(8)
            else:
                return self.phpp_group_number_format.format(9)
        elif self.phx_component.face_type == ComponentFaceType.FLOOR:
            return self.phpp_group_number_format.format(11)
        elif self.phx_component.face_type == ComponentFaceType.ROOF_CEILING:
            return self.phpp_group_number_format.format(10)
        else:
            return self.phpp_group_number_format.format(12)

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
            XLItemAreas(create_range("description"), f"'{self.phx_polygon.display_name}"),
            # -- Note, Add a "-" to the group number so that it is 'text' otherwise the
            # -- IP PHPP won't recognize it properly.
            XLItemAreas(create_range("group_number"), self.phpp_group_number),
            XLItemAreas(create_range("quantity"), 1),
            XLItemAreas(
                create_range("area"),
                self.phx_polygon.area,
                "M2",
                self._get_target_unit("area"),
            ),
            XLItemAreas(create_range("assembly_id"), self.phpp_assembly_id_name),
            XLItemAreas(create_range("orientation"), self.phx_polygon.cardinal_orientation_angle),
            XLItemAreas(create_range("angle"), self.phx_polygon.angle_from_horizontal),
            XLItemAreas(create_range("shading"), 0.5),
            XLItemAreas(create_range("absorptivity"), 0.6),
            XLItemAreas(create_range("emissivity"), 0.9),
        ]


def get_name_from_assembly_id(
    _phpp_assembly_id: Optional[xl_data.xl_range_single_value],
) -> str:
    """Return the face's construction PHPP-Name (ie: "MyConst") from id-string."""
    try:
        return str(_phpp_assembly_id).split("-", 1)[1]
    except:
        if _phpp_assembly_id == None or _phpp_assembly_id == "None":
            return ""
        else:
            msg = f"Error getting construction PHPP-Name? " f"Could not split {_phpp_assembly_id} on '-'?"
            raise Exception(msg)


@dataclass
class ExistingSurfaceRow:
    """The data from an existing PHPP Surface Entry row."""

    __slots__ = ("shape", "data", "group_type_exposure_map")
    shape: shape_model.Areas
    data: list
    group_type_exposure_map: Dict[int, str]  # From io_areas.Areas() parent class

    @property
    def is_empty(self) -> bool:
        if self.name in ["-", "", "None", None]:
            return True
        if self.face_group_type_phpp_string in ["-", "", "None", None]:
            return True
        if self.face_group_type_phpp_number == 0:
            return True
        if self.face_type == ComponentFaceType.NONE:
            return True
        if self.face_exposure == ComponentExposureExterior.NONE:
            return True
        return False

    @property
    def name(self) -> str:
        col_letter = self.shape.surface_rows.inputs.description.column
        col_number_as_index = xl_data.xl_ord(str(col_letter)) - 65
        return str(self.data[col_number_as_index])

    @property
    def face_group_type_phpp_string(self) -> str:
        """Return the face's Group-Type string from the row-data."""
        col_letter = self.shape.surface_rows.inputs.group_number.column
        col_number_as_index = xl_data.xl_ord(str(col_letter)) - 65
        return str(self.data[col_number_as_index])

    @property
    def face_group_type_phpp_number(self) -> int:
        """Return the face's Group-Type number as an int from the Group-Type string."""
        phpp_data = self.face_group_type_phpp_string
        if phpp_data in ["-", "", "None", None]:
            return 0

        result = re.split(r"\D+", phpp_data, 2)
        if not result:
            msg = (
                f"Error getting Group-Type number? Could not find a number "
                f"in the Group-Type string from PHPP: '{phpp_data}'?"
            )
            raise Exception(msg)

        try:
            return int(result[0])
        except:
            msg = (
                f"Error getting Group-Type number? Could not convert '{result[0]}' "
                f"to int from the PHPP value: '{phpp_data}' or type: {type(phpp_data)}?"
            )
            raise Exception(msg)

    @property
    def face_exposure_phpp_letter(self) -> str:
        """Return the face's exposure-type letter ("A", "B", etc..) based on the group_type_phpp_number"""
        return self.group_type_exposure_map[self.face_group_type_phpp_number]

    @property
    def face_type(self) -> ComponentFaceType:
        """Return the face type enum (WALL, FLOOR, etc..) based on the group_type_phpp_number."""
        type_map = {
            0: ComponentFaceType.NONE,
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
            12: ComponentFaceType.CUSTOM,
            13: ComponentFaceType.CUSTOM,
            14: ComponentFaceType.CUSTOM,
            18: ComponentFaceType.ADIABATIC,
        }
        return type_map[self.face_group_type_phpp_number]

    @property
    def face_exposure(self) -> ComponentExposureExterior:
        """Return the exposure type enum (EXTERIOR, GROUND, SURFACE) based on the face_exposure_phpp_letter"""
        type_map = {
            "A": ComponentExposureExterior.EXTERIOR,
            "B": ComponentExposureExterior.GROUND,
            "": ComponentExposureExterior.NONE,
        }
        return type_map.get(self.face_exposure_phpp_letter, ComponentExposureExterior.SURFACE)

    @property
    def face_construction_phpp_id(self) -> str:
        """Return the face's construction PHPP-ID (ie: "01ud-MyConst") from the row-data."""
        col_letter = self.shape.surface_rows.inputs.assembly_id.column
        col_number_as_index = xl_data.xl_ord(str(col_letter)) - 65
        return str(self.data[col_number_as_index])

    @property
    def face_construction_phpp_name(self) -> str:
        """Return the face's construction PHPP-Name (ie: "MyConst") from the row-data."""
        return get_name_from_assembly_id(self.face_construction_phpp_id)
