# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Foundation Class"""

from typing import Union, Type
from dataclasses import dataclass
from PHX.model.enums.foundations import FoundationType, CalculationSetting, PerimeterInsulationPosition


@dataclass
class PhxFoundation:
    display_name: str = "__unnamed_foundation__"

    foundation_setting_num: CalculationSetting = CalculationSetting.USER_DEFINED
    _foundation_type_num: FoundationType = FoundationType.NONE

    @property
    def foundation_type_num(self) -> FoundationType:
        return self._foundation_type_num
    
    @foundation_type_num.setter
    def foundation_type_num(self, _input):
        self._foundation_type_num = FoundationType(_input)


class PhxHeatedBasement(PhxFoundation):
    def __init__(self):
        super().__init__()
        self.floor_slab_area_m2: float = 0.0
        self.floor_slab_u_value: float = 1.0
        self.floor_slab_exposed_perimeter_m: float = 0.0
        self.slab_depth_below_grade_m: float = 2.5
        self.basement_wall_u_value: float = 1.0


class PhxUnHeatedBasement(PhxFoundation):
    def __init__(self):
        super().__init__()
        self.floor_ceiling_area_m2: float = 0.0
        self.ceiling_u_value: float = 0.0
        self.floor_slab_exposed_perimeter_m: float = 0.0
        self.slab_depth_below_grade_m: float = 0.0
        self.basement_wall_height_above_grade_m: float = 0.0
        self.basement_wall_uValue_below_grade: float = 0.0
        self.basement_wall_uValue_above_grade: float = 0.0
        self.floor_slab_u_value: float = 0.0
        self.basement_volume_m3: float = 0.0
        self.basement_ventilation_ach: float = 0.0


class PhxSlabOnGrade(PhxFoundation):
    def __init__(self):
        super().__init__()
        self.floor_slab_area_m2: float = 0.0
        self.floor_slab_u_value: float = 1.0
        self.floor_slab_exposed_perimeter_m: float = 0.0
        self._perim_insulation_position: PerimeterInsulationPosition = PerimeterInsulationPosition.VERTICAL
        self.perim_insulation_width_or_depth_m: float = 0.300
        self.perim_insulation_thickness_m: float = 0.050
        self.perim_insulation_conductivity: float = 0.04

    @property
    def perim_insulation_position(self):
        return self._perim_insulation_position
    
    @perim_insulation_position.setter
    def perim_insulation_position(self, _input):
        self._perim_insulation_position = PerimeterInsulationPosition(_input)


class PhxVentedCrawlspace(PhxFoundation):
    def __init__(self):
        super().__init__()
        self.crawlspace_floor_slab_area_m2 = 0.0
        self.ceiling_above_crawlspace_u_value = 1.0
        self.crawlspace_floor_exposed_perimeter_m = 0.0
        self.crawlspace_wall_height_above_grade_m = 0.0
        self.crawlspace_floor_u_value = 1.0
        self.crawlspace_vent_opening_are_m2 = 0.0
        self.crawlspace_wall_u_value = 1.0


# type alias
PhxFoundationTypes = Union[
        Type[PhxFoundation], 
        Type[PhxHeatedBasement], 
        Type[PhxUnHeatedBasement], 
        Type[PhxSlabOnGrade], 
        Type[PhxVentedCrawlspace]
        ]