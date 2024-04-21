# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Foundation Class"""

from dataclasses import dataclass
from typing import Optional, Type, Union

from PHX.model.enums.foundations import CalculationSetting, FoundationType, PerimeterInsulationPosition


@dataclass
class PhxFoundation:
    display_name: str = "__unnamed_foundation__"

    foundation_setting_num: CalculationSetting = CalculationSetting.USER_DEFINED
    _foundation_type_num: FoundationType = FoundationType.NONE

    @property
    def foundation_type_num(self) -> FoundationType:
        return self._foundation_type_num

    @foundation_type_num.setter
    def foundation_type_num(self, _input: Union[FoundationType, int]) -> None:
        if isinstance(_input, FoundationType):
            self._foundation_type_num = _input
        self._foundation_type_num = FoundationType(_input)


class PhxHeatedBasement(PhxFoundation):
    def __init__(self):
        super().__init__()
        self.floor_slab_area_m2: Optional[float] = 0.0
        self.floor_slab_u_value: Optional[float] = 1.0
        self.floor_slab_exposed_perimeter_m: Optional[float] = 0.0
        self.slab_depth_below_grade_m: Optional[float] = 2.5
        self.basement_wall_u_value: Optional[float] = 1.0


class PhxUnHeatedBasement(PhxFoundation):
    def __init__(self):
        super().__init__()
        self.floor_ceiling_area_m2: Optional[float] = 0.0
        self.ceiling_u_value: Optional[float] = 0.0
        self.floor_slab_exposed_perimeter_m: Optional[float] = 0.0
        self.slab_depth_below_grade_m: Optional[float] = 0.0
        self.basement_wall_height_above_grade_m: Optional[float] = 0.0
        self.basement_wall_uValue_below_grade: Optional[float] = 0.0
        self.basement_wall_uValue_above_grade: Optional[float] = 0.0
        self.floor_slab_u_value: Optional[float] = 0.0
        self.basement_volume_m3: Optional[float] = 0.0
        self.basement_ventilation_ach: Optional[float] = 0.0


class PhxSlabOnGrade(PhxFoundation):
    def __init__(self):
        super().__init__()
        self.floor_slab_area_m2: Optional[float] = 0.0
        self.floor_slab_u_value: Optional[float] = 1.0
        self.floor_slab_exposed_perimeter_m: Optional[float] = 0.0
        self._perim_insulation_position: PerimeterInsulationPosition = PerimeterInsulationPosition.VERTICAL
        self.perim_insulation_width_or_depth_m: Optional[float] = 0.300
        self.perim_insulation_thickness_m: Optional[float] = 0.050
        self.perim_insulation_conductivity: Optional[float] = 0.04

    @property
    def perim_insulation_position(self) -> PerimeterInsulationPosition:
        return self._perim_insulation_position

    @perim_insulation_position.setter
    def perim_insulation_position(self, _input: Union[PerimeterInsulationPosition, int, None]) -> None:
        if not _input:
            return
        if isinstance(_input, PerimeterInsulationPosition):
            self._perim_insulation_position = _input
        self._perim_insulation_position = PerimeterInsulationPosition(_input)


class PhxVentedCrawlspace(PhxFoundation):
    def __init__(self):
        super().__init__()
        self.crawlspace_floor_slab_area_m2: Optional[float] = 0.0
        self.ceiling_above_crawlspace_u_value: Optional[float] = 1.0
        self.crawlspace_floor_exposed_perimeter_m: Optional[float] = 0.0
        self.crawlspace_wall_height_above_grade_m: Optional[float] = 0.0
        self.crawlspace_floor_u_value: Optional[float] = 1.0
        self.crawlspace_vent_opening_are_m2: Optional[float] = 0.0
        self.crawlspace_wall_u_value: Optional[float] = 1.0


# type alias
PhxFoundationTypes = Union[
    Type[PhxFoundation],
    Type[PhxHeatedBasement],
    Type[PhxUnHeatedBasement],
    Type[PhxSlabOnGrade],
    Type[PhxVentedCrawlspace],
]
