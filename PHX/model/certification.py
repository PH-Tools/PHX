# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Passive House Certification Classes"""

from __future__ import annotations
from typing import ClassVar
from dataclasses import dataclass, field
from enum import Enum

from PHX.model import ground
from PHX.model.enums import phi_certification_phpp_9, phius_certification


@dataclass
class PhxSetpoints:
    winter: float = 20.0  # deg. C
    summer: float = 25.0  # deg. C


@dataclass
class PhxPhBuildingData:
    _count: ClassVar[int] = 0

    id_num: int = field(init=False, default=0)

    num_of_units: int = 1
    num_of_floors: int = 1
    occupancy_setting_method: int = 2  # Design

    airtightness_q50: float = 1.0  # m3/hr-m2-envelope
    airtightness_n50: float = 1.0  # ach
    wind_coefficient_e: float = 0.07
    wind_coefficient_f: float = 15

    setpoints: PhxSetpoints = field(default_factory=PhxSetpoints)
    mech_room_temp: float = 20.0

    foundations: list[ground.PhxFoundation] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    def add_foundation(self, _input: ground.PhxFoundation) -> None:
        self.foundations.append(_input)


# -----------------------------------------------------------------------------
@dataclass
class PhxPhiusCertificationCriteria:
    ph_selection_target_data: int = 2

    phius_annual_heating_demand: float = 15.0
    phius_annual_cooling_demand: float = 15.0
    phius_peak_heating_load: float = 10.0
    phius_peak_cooling_load: float = 10.0


@dataclass
class PhxPhiusCertificationSettings:
    phius_building_certification_program = (
        phius_certification.PhiusCertificationProgram.PHIUS_2021_CORE
    )
    phius_building_category_type = (
        phius_certification.PhiusCertificationBuildingCategoryType.RESIDENTIAL_BUILDING
    )
    phius_building_use_type = (
        phius_certification.PhiusCertificationBuildingUseType.RESIDENTIAL
    )
    phius_building_status = (
        phius_certification.PhiusCertificationBuildingStatus.IN_PLANNING
    )
    phius_building_type = (
        phius_certification.PhiusCertificationBuildingType.NEW_CONSTRUCTION
    )


@dataclass
class PhxPhiusCertification:
    phius_certification_criteria: PhxPhiusCertificationCriteria = field(
        default_factory=PhxPhiusCertificationCriteria
    )
    phius_certification_settings: PhxPhiusCertificationSettings = field(
        default_factory=PhxPhiusCertificationSettings
    )

    # TODO: Refactor this out to someplace more general than inside Phius....
    ph_building_data: PhxPhBuildingData = field(default_factory=PhxPhBuildingData)


# -----------------------------------------------------------------------------
@dataclass
class PhxPhiCertificationSettings:
    phi_building_category_type: Enum = (
        phi_certification_phpp_9.PhiCertBuildingCategoryType.RESIDENTIAL_BUILDING
    )
    phi_building_use_type: Enum = phi_certification_phpp_9.PhiCertBuildingUseType.DWELLING
    phi_building_ihg_type: Enum = phi_certification_phpp_9.PhiCertIHGType.STANDARD
    phi_building_occupancy_type: Enum = (
        phi_certification_phpp_9.PhiCertOccupancyType.STANDARD
    )

    phi_certification_type: Enum = phi_certification_phpp_9.PhiCertType.PASSIVE_HOUSE
    phi_certification_class: Enum = phi_certification_phpp_9.PhiCertClass.CLASSIC
    phi_pe_type: Enum = phi_certification_phpp_9.PhiCertificationPEType.PER
    phi_enerphit_type: Enum = phi_certification_phpp_9.PhiCertEnerPHitType.BY_DEMAND
    phi_retrofit_type: Enum = phi_certification_phpp_9.PhiCertRetrofitType.NEW_BUILDING


@dataclass
class PhxPhiCertification:
    phi_certification_settings: PhxPhiCertificationSettings = field(
        default_factory=PhxPhiCertificationSettings
    )
    version: int = 9
