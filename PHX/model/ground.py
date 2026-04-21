# -*- Python Version: 3.10 -*-

"""PHX Foundation Classes for below-grade and ground-contact thermal boundary conditions."""

from dataclasses import dataclass
from typing import Union

from PHX.model.enums.foundations import CalculationSetting, FoundationType, PerimeterInsulationPosition


@dataclass
class PhxFoundation:
    """Base class for all PHX foundation / ground-contact boundary conditions.

    Subclassed by heated basement, unheated basement, slab-on-grade, and vented
    crawlspace types. Each subclass carries the geometry and U-value attributes
    required by the WUFI ground-heat-loss calculation.

    Attributes:
        display_name (str): User-facing name for the foundation element. Default: "__unnamed_foundation__".
        foundation_setting_num (CalculationSetting): Calculation method selector. Default: USER_DEFINED.
    """

    display_name: str = "__unnamed_foundation__"

    foundation_setting_num: CalculationSetting = CalculationSetting.USER_DEFINED
    _foundation_type_num: FoundationType = FoundationType.NONE

    @property
    def foundation_type_num(self) -> FoundationType:
        """The FoundationType enum for this foundation element."""
        return self._foundation_type_num

    @foundation_type_num.setter
    def foundation_type_num(self, _input: FoundationType | int) -> None:
        if isinstance(_input, FoundationType):
            self._foundation_type_num = _input
        self._foundation_type_num = FoundationType(_input)


class PhxHeatedBasement(PhxFoundation):
    """A heated (conditioned) basement foundation within the thermal envelope.

    The basement volume is inside the conditioned space, so both the slab and the
    below-grade walls contribute to transmission heat loss.

    Attributes:
        floor_slab_area_m2 (float | None): Area of the basement floor slab [m2]. Default: 0.0.
        floor_slab_u_value (float | None): U-value of the basement floor slab [W/m2K]. Default: 1.0.
        floor_slab_exposed_perimeter_m (float | None): Exposed perimeter of the floor slab [m]. Default: 0.0.
        slab_depth_below_grade_m (float | None): Depth of the basement slab below exterior grade [m]. Default: 2.5.
        basement_wall_u_value (float | None): U-value of the below-grade basement walls [W/m2K]. Default: 1.0.
    """

    def __init__(self):
        super().__init__()
        self.floor_slab_area_m2: float | None = 0.0
        self.floor_slab_u_value: float | None = 1.0
        self.floor_slab_exposed_perimeter_m: float | None = 0.0
        self.slab_depth_below_grade_m: float | None = 2.5
        self.basement_wall_u_value: float | None = 1.0


class PhxUnHeatedBasement(PhxFoundation):
    """An unheated (unconditioned) basement below the thermal envelope.

    The basement volume is outside the conditioned space. The thermal boundary
    is at the ceiling between the basement and the conditioned floor above, with
    additional ground-coupling losses through the basement walls and slab.

    Attributes:
        floor_ceiling_area_m2 (float | None): Area of the ceiling above the basement (thermal boundary) [m2].
            Default: 0.0.
        ceiling_u_value (float | None): U-value of the ceiling above the basement [W/m2K]. Default: 0.0.
        floor_slab_exposed_perimeter_m (float | None): Exposed perimeter of the basement floor slab [m].
            Default: 0.0.
        slab_depth_below_grade_m (float | None): Depth of the basement slab below exterior grade [m]. Default: 0.0.
        basement_wall_height_above_grade_m (float | None): Height of basement wall exposed above grade [m].
            Default: 0.0.
        basement_wall_uValue_below_grade (float | None): U-value of basement walls below grade [W/m2K].
            Default: 0.0.
        basement_wall_uValue_above_grade (float | None): U-value of basement walls above grade [W/m2K].
            Default: 0.0.
        floor_slab_u_value (float | None): U-value of the basement floor slab [W/m2K]. Default: 0.0.
        basement_volume_m3 (float | None): Interior volume of the basement [m3]. Default: 0.0.
        basement_ventilation_ach (float | None): Air change rate of the basement [ACH]. Default: 0.0.
    """

    def __init__(self):
        super().__init__()
        self.floor_ceiling_area_m2: float | None = 0.0
        self.ceiling_u_value: float | None = 0.0
        self.floor_slab_exposed_perimeter_m: float | None = 0.0
        self.slab_depth_below_grade_m: float | None = 0.0
        self.basement_wall_height_above_grade_m: float | None = 0.0
        self.basement_wall_uValue_below_grade: float | None = 0.0
        self.basement_wall_uValue_above_grade: float | None = 0.0
        self.floor_slab_u_value: float | None = 0.0
        self.basement_volume_m3: float | None = 0.0
        self.basement_ventilation_ach: float | None = 0.0


class PhxSlabOnGrade(PhxFoundation):
    """A slab-on-grade foundation in direct contact with the soil.

    Includes optional perimeter insulation (horizontal or vertical) described by
    width/depth, thickness, and conductivity for the ISO 13370 ground-loss calculation.

    Attributes:
        floor_slab_area_m2 (float | None): Area of the floor slab [m2]. Default: 0.0.
        floor_slab_u_value (float | None): U-value of the floor slab [W/m2K]. Default: 1.0.
        floor_slab_exposed_perimeter_m (float | None): Exposed perimeter of the floor slab [m]. Default: 0.0.
        perim_insulation_width_or_depth_m (float | None): Horizontal width or vertical depth of perimeter
            insulation [m]. Default: 0.300.
        perim_insulation_thickness_m (float | None): Thickness of the perimeter insulation [m]. Default: 0.050.
        perim_insulation_conductivity (float | None): Thermal conductivity of the perimeter insulation [W/mK].
            Default: 0.04.
    """

    def __init__(self):
        super().__init__()
        self.floor_slab_area_m2: float | None = 0.0
        self.floor_slab_u_value: float | None = 1.0
        self.floor_slab_exposed_perimeter_m: float | None = 0.0
        self._perim_insulation_position: PerimeterInsulationPosition = PerimeterInsulationPosition.VERTICAL
        self.perim_insulation_width_or_depth_m: float | None = 0.300
        self.perim_insulation_thickness_m: float | None = 0.050
        self.perim_insulation_conductivity: float | None = 0.04

    @property
    def perim_insulation_position(self) -> PerimeterInsulationPosition:
        """The PerimeterInsulationPosition enum (horizontal or vertical)."""
        return self._perim_insulation_position

    @perim_insulation_position.setter
    def perim_insulation_position(self, _input: PerimeterInsulationPosition | int | None) -> None:
        if not _input:
            return
        if isinstance(_input, PerimeterInsulationPosition):
            self._perim_insulation_position = _input
        self._perim_insulation_position = PerimeterInsulationPosition(_input)


class PhxVentedCrawlspace(PhxFoundation):
    """A vented crawlspace foundation beneath the thermal envelope.

    The crawlspace is unconditioned and ventilated to the exterior. The thermal
    boundary is at the floor/ceiling above the crawlspace, with additional
    ground-coupling losses through the crawlspace floor slab and perimeter walls.

    Attributes:
        crawlspace_floor_slab_area_m2 (float | None): Area of the crawlspace floor slab [m2]. Default: 0.0.
        ceiling_above_crawlspace_u_value (float | None): U-value of the ceiling above the crawlspace (thermal
            boundary) [W/m2K]. Default: 1.0.
        crawlspace_floor_exposed_perimeter_m (float | None): Exposed perimeter of the crawlspace floor slab [m].
            Default: 0.0.
        crawlspace_wall_height_above_grade_m (float | None): Height of crawlspace wall exposed above grade [m].
            Default: 0.0.
        crawlspace_floor_u_value (float | None): U-value of the crawlspace floor slab [W/m2K]. Default: 1.0.
        crawlspace_vent_opening_are_m2 (float | None): Total area of crawlspace ventilation openings [m2].
            Default: 0.0.
        crawlspace_wall_u_value (float | None): U-value of the crawlspace perimeter walls [W/m2K]. Default: 1.0.
    """

    def __init__(self):
        super().__init__()
        self.crawlspace_floor_slab_area_m2: float | None = 0.0
        self.ceiling_above_crawlspace_u_value: float | None = 1.0
        self.crawlspace_floor_exposed_perimeter_m: float | None = 0.0
        self.crawlspace_wall_height_above_grade_m: float | None = 0.0
        self.crawlspace_floor_u_value: float | None = 1.0
        self.crawlspace_vent_opening_are_m2: float | None = 0.0
        self.crawlspace_wall_u_value: float | None = 1.0


# type alias
PhxFoundationTypes = Union[
    type[PhxFoundation],
    type[PhxHeatedBasement],
    type[PhxUnHeatedBasement],
    type[PhxSlabOnGrade],
    type[PhxVentedCrawlspace],
]
