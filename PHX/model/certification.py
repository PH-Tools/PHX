# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Passive House Certification Classes"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, Optional

from PHX.model import ground
from PHX.model.enums import phi_certification_phpp_9, phius_certification
from PHX.model.enums.building import WindExposureType
from PHX.model.enums.hvac import PhxSummerBypassMode


@dataclass
class PhxSetpoints:
    winter: float = 20.0  # deg. C
    summer: float = 25.0  # deg. C

    def __eq__(self, other: PhxSetpoints) -> bool:
        TOLERANCE = 0.001
        if abs(self.winter - other.winter) > TOLERANCE:
            return False
        if abs(self.summer - other.summer) > TOLERANCE:
            return False
        return True


@dataclass
class PhxPhBuildingData:
    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)

    num_of_units: Optional[int] = 1
    num_of_floors: Optional[int] = 1
    occupancy_setting_method: int = 2  # Design
    airtightness_q50: float = 1.0  # m3/hr-m2-envelope
    airtightness_n50: float = 1.0  # ach
    wind_coefficient_e: float = 0.07
    wind_coefficient_f: float = 15
    setpoints: PhxSetpoints = field(default_factory=PhxSetpoints)
    mech_room_temp: float = 20.0
    non_combustible_materials: bool = False
    foundations: list[ground.PhxFoundation] = field(default_factory=list)
    building_exposure_type: WindExposureType = WindExposureType.SEVERAL_SIDES_EXPOSED_NO_SCREENING
    summer_hrv_bypass_mode: PhxSummerBypassMode = PhxSummerBypassMode.ALWAYS

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    def add_foundation(self, _input: Optional[ground.PhxFoundation]) -> None:
        if not _input:
            return
        self.foundations.append(_input)

    def __eq__(self, other: PhxPhBuildingData) -> bool:
        TOLERANCE = 0.001
        if self.num_of_units != other.num_of_units:
            return False
        if self.num_of_floors != other.num_of_floors:
            return False
        if self.occupancy_setting_method != other.occupancy_setting_method:
            return False
        if abs(self.airtightness_q50 - other.airtightness_q50) > TOLERANCE:
            return False
        if abs(self.airtightness_n50 - other.airtightness_n50) > TOLERANCE:
            return False
        if abs(self.wind_coefficient_e - other.wind_coefficient_e) > TOLERANCE:
            return False
        if abs(self.wind_coefficient_f - other.wind_coefficient_f) > TOLERANCE:
            return False
        if self.setpoints != other.setpoints:
            return False
        if abs(self.mech_room_temp - other.mech_room_temp) > TOLERANCE:
            return False
        if self.non_combustible_materials != other.non_combustible_materials:
            return False
        if self.foundations != other.foundations:
            return False
        if self.summer_hrv_bypass_mode != other.summer_hrv_bypass_mode:
            return False
        return True


# -----------------------------------------------------------------------------
@dataclass
class PhxPhiusCertificationCriteria:
    ph_selection_target_data: int = 2

    phius_annual_heating_demand: float = 15.0
    phius_annual_cooling_demand: float = 15.0
    phius_peak_heating_load: float = 10.0
    phius_peak_cooling_load: float = 10.0

    def __eq__(self, other: PhxPhiusCertificationCriteria) -> bool:
        TOLERANCE = 0.001
        if abs(self.phius_annual_heating_demand - other.phius_annual_heating_demand) > TOLERANCE:
            return False
        if abs(self.phius_annual_cooling_demand - other.phius_annual_cooling_demand) > TOLERANCE:
            return False
        if abs(self.phius_peak_heating_load - other.phius_peak_heating_load) > TOLERANCE:
            return False
        if abs(self.phius_peak_cooling_load - other.phius_peak_cooling_load) > TOLERANCE:
            return False
        return True


@dataclass
class PhxPhiusCertificationSettings:
    phius_building_certification_program = phius_certification.PhiusCertificationProgram.PHIUS_2021_CORE
    phius_building_category_type = phius_certification.PhiusCertificationBuildingCategoryType.RESIDENTIAL_BUILDING
    phius_building_use_type = phius_certification.PhiusCertificationBuildingUseType.RESIDENTIAL
    phius_building_status = phius_certification.PhiusCertificationBuildingStatus.IN_PLANNING
    phius_building_type = phius_certification.PhiusCertificationBuildingType.NEW_CONSTRUCTION

    def __eq__(self, other: PhxPhiusCertificationSettings) -> bool:
        if self.phius_building_certification_program != other.phius_building_certification_program:
            return False
        if self.phius_building_category_type != other.phius_building_category_type:
            return False
        if self.phius_building_use_type != other.phius_building_use_type:
            return False
        if self.phius_building_status != other.phius_building_status:
            return False
        if self.phius_building_type != other.phius_building_type:
            return False
        return True


@dataclass
class PhxPhiusCertification:
    phius_certification_criteria: PhxPhiusCertificationCriteria = field(default_factory=PhxPhiusCertificationCriteria)
    phius_certification_settings: PhxPhiusCertificationSettings = field(default_factory=PhxPhiusCertificationSettings)

    # TODO: Refactor this out to someplace more general than inside Phius....
    ph_building_data: PhxPhBuildingData = field(default_factory=PhxPhBuildingData)
    use_monthly_shading: bool = True

    def __eq__(self, other: PhxPhiusCertification) -> bool:
        if self.phius_certification_criteria != other.phius_certification_criteria:
            return False
        if self.phius_certification_settings != other.phius_certification_settings:
            return False
        if self.ph_building_data != other.ph_building_data:
            return False
        if self.use_monthly_shading != other.use_monthly_shading:
            return False
        return True


# -----------------------------------------------------------------------------
@dataclass
class PhxPhiCertificationSettings:
    phi_building_category_type: Enum = phi_certification_phpp_9.PhiCertBuildingCategoryType.RESIDENTIAL_BUILDING
    phi_building_use_type: Enum = phi_certification_phpp_9.PhiCertBuildingUseType.DWELLING
    phi_building_ihg_type: Enum = phi_certification_phpp_9.PhiCertIHGType.STANDARD
    phi_building_occupancy_type: Enum = phi_certification_phpp_9.PhiCertOccupancyType.STANDARD

    phi_certification_type: Enum = phi_certification_phpp_9.PhiCertType.PASSIVE_HOUSE
    phi_certification_class: Enum = phi_certification_phpp_9.PhiCertClass.CLASSIC
    phi_pe_type: Enum = phi_certification_phpp_9.PhiCertificationPEType.PER
    phi_enerphit_type: Enum = phi_certification_phpp_9.PhiCertEnerPHitType.BY_DEMAND
    phi_retrofit_type: Enum = phi_certification_phpp_9.PhiCertRetrofitType.NEW_BUILDING

    def __eq__(self, other: PhxPhiCertificationSettings) -> bool:
        if self.phi_building_category_type != other.phi_building_category_type:
            return False
        if self.phi_building_use_type != other.phi_building_use_type:
            return False
        if self.phi_building_ihg_type != other.phi_building_ihg_type:
            return False
        if self.phi_building_occupancy_type != other.phi_building_occupancy_type:
            return False
        if self.phi_certification_type != other.phi_certification_type:
            return False
        if self.phi_certification_class != other.phi_certification_class:
            return False
        if self.phi_pe_type != other.phi_pe_type:
            return False
        if self.phi_enerphit_type != other.phi_enerphit_type:
            return False
        if self.phi_retrofit_type != other.phi_retrofit_type:
            return False
        return True


@dataclass
class PhxPhiCertification:
    phi_certification_settings: PhxPhiCertificationSettings = field(default_factory=PhxPhiCertificationSettings)
    version: int = 9

    def __eq__(self, other: PhxPhiCertification) -> bool:
        if self.phi_certification_settings != other.phi_certification_settings:
            return False
        if self.version != other.version:
            return False
        return True
