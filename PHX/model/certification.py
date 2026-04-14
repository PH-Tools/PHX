# -*- Python Version: 3.10 -*-

"""PHX Passive House Certification Classes"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar

from PHX.model import ground
from PHX.model.enums import phi_certification_phpp_9, phius_certification
from PHX.model.enums.building import WindExposureType
from PHX.model.enums.hvac import PhxNighttimeVentilationControl, PhxSummerBypassMode


@dataclass
class PhxSetpoints:
    winter: float = 20.0  # deg. C
    summer: float = 25.0  # deg. C

    def __eq__(self, other: PhxSetpoints) -> bool:
        TOLERANCE = 0.001
        if abs(self.winter - other.winter) > TOLERANCE:
            return False
        return not abs(self.summer - other.summer) > TOLERANCE


@dataclass
class PhxSummerVentilation:
    ventilation_system_ach: float | None = None
    summer_bypass_mode: PhxSummerBypassMode = PhxSummerBypassMode.ALWAYS
    daytime_extract_system_ach: float = 0.0
    daytime_extract_system_fan_power_wh_m3: float = 0.0
    daytime_window_ach: float = 0.0
    nighttime_extract_system_ach: float = 0.0
    nighttime_extract_system_fan_power_wh_m3: float = 0.0
    nighttime_extract_system_heat_fraction: float = 0.0
    nighttime_extract_system_control: PhxNighttimeVentilationControl = (
        PhxNighttimeVentilationControl.TEMPERATURE_CONTROLLED
    )
    nighttime_window_ach: float = 0.0
    nighttime_minimum_indoor_temp_C: float = 0.0

    def __eq__(self, other: PhxSummerVentilation) -> bool:
        TOLERANCE = 0.001
        if not isinstance(other, PhxSummerVentilation):
            return NotImplemented
        if self.ventilation_system_ach is None and other.ventilation_system_ach is None:
            pass
        elif (
            self.ventilation_system_ach is None
            or other.ventilation_system_ach is None
            or abs(self.ventilation_system_ach - other.ventilation_system_ach) > TOLERANCE
        ):
            return False
        if self.summer_bypass_mode != other.summer_bypass_mode:
            return False
        if abs(self.daytime_extract_system_ach - other.daytime_extract_system_ach) > TOLERANCE:
            return False
        if abs(self.daytime_extract_system_fan_power_wh_m3 - other.daytime_extract_system_fan_power_wh_m3) > TOLERANCE:
            return False
        if abs(self.daytime_window_ach - other.daytime_window_ach) > TOLERANCE:
            return False
        if abs(self.nighttime_extract_system_ach - other.nighttime_extract_system_ach) > TOLERANCE:
            return False
        if (
            abs(self.nighttime_extract_system_fan_power_wh_m3 - other.nighttime_extract_system_fan_power_wh_m3)
            > TOLERANCE
        ):
            return False
        if abs(self.nighttime_extract_system_heat_fraction - other.nighttime_extract_system_heat_fraction) > TOLERANCE:
            return False
        if self.nighttime_extract_system_control != other.nighttime_extract_system_control:
            return False
        if abs(self.nighttime_window_ach - other.nighttime_window_ach) > TOLERANCE:
            return False
        return not abs(self.nighttime_minimum_indoor_temp_C - other.nighttime_minimum_indoor_temp_C) > TOLERANCE


@dataclass
class PhxPhBuildingData:
    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)

    num_of_units: int | None = 1
    num_of_floors: int | None = 1
    occupancy_setting_method: int = 2  # Design
    airtightness_q50: float = 1.0  # m3/hr-m2-envelope
    airtightness_n50: float = 1.0  # ach
    wind_coefficient_f: float = 15
    setpoints: PhxSetpoints = field(default_factory=PhxSetpoints)
    mech_room_temp: float = 20.0
    non_combustible_materials: bool = False
    foundations: list[ground.PhxFoundation] = field(default_factory=list)
    building_exposure_type: WindExposureType = WindExposureType.SEVERAL_SIDES_EXPOSED_NO_SCREENING
    summer_ventilation: PhxSummerVentilation = field(default_factory=PhxSummerVentilation)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    def add_foundation(self, _input: ground.PhxFoundation | None) -> None:
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
        return self.summer_ventilation == other.summer_ventilation

    @property
    def wind_coefficient_e(self) -> float:
        """Wind pressure coefficient E, used for calculating infiltration due to wind pressure."""
        match self.building_exposure_type:
            case WindExposureType.SEVERAL_SIDES_EXPOSED_NO_SCREENING:
                return 0.1
            case WindExposureType.SEVERAL_SIDES_EXPOSED_MODERATE_SCREENING:
                return 0.07
            case WindExposureType.SEVERAL_SIDES_EXPOSED_HIGH_SCREENING:
                return 0.04
            case _:
                return 0.1


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
        return not abs(self.phius_peak_cooling_load - other.phius_peak_cooling_load) > TOLERANCE


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
        return self.phius_building_type == other.phius_building_type


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
        return self.use_monthly_shading == other.use_monthly_shading


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
        return self.phi_retrofit_type == other.phi_retrofit_type


@dataclass
class PhxPhiCertification:
    phi_certification_settings: PhxPhiCertificationSettings = field(default_factory=PhxPhiCertificationSettings)
    version: int = 9

    def __eq__(self, other: PhxPhiCertification) -> bool:
        if self.phi_certification_settings != other.phi_certification_settings:
            return False
        return self.version == other.version
