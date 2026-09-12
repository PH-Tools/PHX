# -*- Python Version: 3.10 -*-

"""Model class for the PHPP 'Ground' worksheet: one PHX foundation as building-section-1 inputs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PHX.model import ground
from PHX.model.enums.foundations import FoundationType, PerimeterInsulationPosition
from PHX.model.phx_site import PhxGround
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model.xl_checkbox_group import CHECKED, UNCHECKED, checkbox_group_items
from PHX.xl import xl_data

#: The four floor-slab type selectors, in worksheet order.
TYPE_SELECTORS = ("slab_on_grade", "heated_basement", "unheated_basement", "crawlspace")

ItemBuilder = Callable[..., xl_data.XlItem]


class GroundExportError(Exception):
    """Raised when a PHX foundation cannot be written to the PHPP 'Ground' worksheet."""


def _area(_length_m: float | None, _height_m: float | None) -> float:
    """A wall area [m2] from a perimeter length [m] and a height or depth [m]."""
    return (_length_m or 0.0) * (_height_m or 0.0)


@dataclass
class GroundFoundationBlock:
    """One PHX foundation, plus the site's soil, as the inputs of PHPP 'Ground' building section 1.

    Only the marked type's inputs are written: PHPP reads the other types' cells only
    when their selector is marked. 'H18'/'P18' (floor area and U-value) are formulas
    reading 'Areas' and are never written.
    """

    shape: shape_model.Ground
    phx_ground: PhxGround
    phx_foundation: ground.PhxFoundation

    def create_xl_items(self, _sheet_name: str, _header_row: int) -> list[xl_data.XlItem]:
        """Return the XlItems for the foundation, located relative to the 'Floor slab type' header row.

        Arguments:
        ----------
            * _sheet_name (str): The name of the worksheet to write to.
            * _header_row (int): The worksheet row of the located 'Floor slab type' header.

        Returns:
        --------
            * (list[xl_data.XlItem]): The XlItems to write.
        """
        if not (block := self.shape.input_block):
            raise GroundExportError(f"The '{self.shape.name}' worksheet layout is not mapped for this PHPP.")
        section = block.sections[0]

        def address(_name: str) -> str:
            spec: shape_model.GroundInput = getattr(block.inputs, _name)
            return f"{getattr(section, spec.column)}{_header_row + spec.row_offset}"

        def item(_name: str, _value: xl_data.xl_writable, _input_unit: str | None = None) -> xl_data.XlItem:
            if _value is None:
                return xl_data.XlItem(_sheet_name, address(_name), UNCHECKED)
            target_unit = getattr(block.inputs, _name).unit
            return xl_data.XlItem(_sheet_name, address(_name), _value, _input_unit, target_unit)

        selector, type_items = self._type_inputs(item)
        soil = self.phx_ground
        return [
            item("soil_conductivity", soil.ground_thermal_conductivity, "W/MK"),
            # -- PHX: density [kg/m3] x heat capacity [J/(kgK)] = J/(m3K); PHPP: MJ/(m3K)
            item("soil_heat_capacity", soil.ground_density * soil.ground_heat_capacity / 1_000_000, "MJ/M3K"),
            item("groundwater_depth", soil.depth_groundwater, "M"),
            item("groundwater_flow_rate", soil.flow_rate_groundwater, "M/D"),
            *checkbox_group_items(_sheet_name, [address(_) for _ in TYPE_SELECTORS], TYPE_SELECTORS.index(selector)),
            *type_items,
        ]

    def _type_inputs(self, item: ItemBuilder) -> tuple[str, list[xl_data.XlItem]]:
        """Return the selector name and type-specific XlItems for the concrete foundation class.

        Dispatches on the class, not on 'foundation_type_num': the subclasses do not set
        the enum themselves, so a directly constructed one reports NONE.
        """
        foundation = self.phx_foundation
        writers: dict[type, tuple[str, FoundationType, Callable]] = {
            ground.PhxSlabOnGrade: ("slab_on_grade", FoundationType.SLAB_ON_GRADE, self._slab_on_grade),
            ground.PhxHeatedBasement: ("heated_basement", FoundationType.HEATED_BASEMENT, self._heated_basement),
            ground.PhxUnHeatedBasement: (
                "unheated_basement",
                FoundationType.UNHEATED_BASEMENT,
                self._unheated_basement,
            ),
            ground.PhxVentedCrawlspace: ("crawlspace", FoundationType.VENTED_CRAWLSPACE, self._crawlspace),
        }
        if not (writer := writers.get(type(foundation))):
            raise GroundExportError(
                f"Cannot write the foundation '{foundation.display_name}' of type "
                f"'{type(foundation).__name__}' to the PHPP 'Ground' worksheet: it is not one of "
                f"{[_.__name__ for _ in writers]}."
            )

        selector, expected_type, write_type = writer
        if foundation.foundation_type_num not in (FoundationType.NONE, expected_type):
            raise GroundExportError(
                f"The foundation '{foundation.display_name}' is a '{type(foundation).__name__}' but its "
                f"foundation_type_num is '{foundation.foundation_type_num.name}'. The model reader that "
                "built it is inconsistent."
            )
        return selector, write_type(foundation, item)

    def _slab_on_grade(self, _slab: ground.PhxSlabOnGrade, item: ItemBuilder) -> list[xl_data.XlItem]:
        # -- 'P25' is the horizontal check; PHPP derives the vertical check 'P26' from it.
        is_horizontal = _slab.perim_insulation_position == PerimeterInsulationPosition.HORIZONTAL
        return [
            item("perimeter", _slab.floor_slab_exposed_perimeter_m, "M"),
            item("slab_perim_insulation_width", _slab.perim_insulation_width_or_depth_m, "M"),
            item("slab_perim_insulation_thickness", _slab.perim_insulation_thickness_m, "M"),
            item("slab_perim_insulation_conductivity", _slab.perim_insulation_conductivity, "W/MK"),
            item("slab_perim_insulation_horizontal", CHECKED if is_horizontal else UNCHECKED),
            item("slab_interior_wall_area", _slab.interior_wall_to_heated_area_m2, "M2"),
            item("slab_interior_wall_u_value", _slab.interior_wall_to_heated_u_value, "W/M2K"),
        ]

    def _heated_basement(self, _basement: ground.PhxHeatedBasement, item: ItemBuilder) -> list[xl_data.XlItem]:
        # -- PHX: perimeter [m] x depth below grade [m]; PHPP: wall area below ground 'Awb' [m2]
        wall_below_area = _area(_basement.floor_slab_exposed_perimeter_m, _basement.slab_depth_below_grade_m)
        if wall_below_area <= 0 or (_basement.basement_wall_u_value or 0.0) <= 0:
            raise GroundExportError(
                f"The heated basement '{_basement.display_name}' needs a below-grade wall area "
                f"(perimeter {_basement.floor_slab_exposed_perimeter_m} m x depth "
                f"{_basement.slab_depth_below_grade_m} m) and a wall U-value "
                f"({_basement.basement_wall_u_value}) above zero. PHPP flags 'Data missing' at "
                "'Ground!S31' and drops the detailed ground calculation otherwise."
            )
        return [
            item("perimeter", _basement.floor_slab_exposed_perimeter_m, "M"),
            item("heated_basement_wall_below_area", wall_below_area, "M2"),
            item("heated_basement_wall_below_u_value", _basement.basement_wall_u_value, "W/M2K"),
        ]

    def _unheated_basement(self, _basement: ground.PhxUnHeatedBasement, item: ItemBuilder) -> list[xl_data.XlItem]:
        perimeter = _basement.floor_slab_exposed_perimeter_m
        return [
            item("perimeter", perimeter, "M"),
            # -- PHX: perimeter [m] x wall height above grade [m]; PHPP: wall area above ground 'AW' [m2]
            item(
                "unheated_basement_wall_above_area",
                _area(perimeter, _basement.basement_wall_height_above_grade_m),
                "M2",
            ),
            item("unheated_basement_wall_above_u_value", _basement.basement_wall_uValue_above_grade, "W/M2K"),
            # -- PHX: perimeter [m] x depth below grade [m]; PHPP: wall area below ground 'Awb' [m2]
            item("unheated_basement_wall_below_area", _area(perimeter, _basement.slab_depth_below_grade_m), "M2"),
            item("unheated_basement_wall_below_u_value", _basement.basement_wall_uValue_below_grade, "W/M2K"),
            item("unheated_basement_interior_wall_area", _basement.interior_wall_to_heated_area_m2, "M2"),
            item("unheated_basement_interior_wall_u_value", _basement.interior_wall_to_heated_u_value, "W/M2K"),
            item("unheated_basement_air_change_rate", _basement.basement_ventilation_ach),
            item("unheated_basement_floor_u_value", _basement.floor_slab_u_value, "W/M2K"),
            item("unheated_basement_volume", _basement.basement_volume_m3, "M3"),
        ]

    def _crawlspace(self, _crawlspace: ground.PhxVentedCrawlspace, item: ItemBuilder) -> list[xl_data.XlItem]:
        return [
            item("perimeter", _crawlspace.crawlspace_floor_exposed_perimeter_m, "M"),
            item("crawlspace_floor_u_value", _crawlspace.crawlspace_floor_u_value, "W/M2K"),
            item("crawlspace_vent_opening_area", _crawlspace.crawlspace_vent_opening_are_m2, "M2"),
            item("crawlspace_wall_height", _crawlspace.crawlspace_wall_height_above_grade_m, "M"),
            item("crawlspace_wind_velocity", _crawlspace.wind_velocity_at_10m_m_s, "M/S"),
            item("crawlspace_wall_u_value", _crawlspace.crawlspace_wall_u_value, "W/M2K"),
            item("crawlspace_wind_shield_factor", _crawlspace.wind_shield_factor),
            item("crawlspace_interior_wall_area", _crawlspace.interior_wall_to_heated_area_m2, "M2"),
            item("crawlspace_interior_wall_u_value", _crawlspace.interior_wall_to_heated_u_value, "W/M2K"),
        ]
