# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Valid 'types' for PHI Certification Settings (PHPP v9)."""

from enum import Enum


class PhiCertBuildingCategoryType(Enum):
    RESIDENTIAL_BUILDING = 1
    NONRESIDENTIAL_BUILDING = 2


class PhiCertBuildingUseType(Enum):
    DWELLING = 10
    NURSING_HOME = 11
    OTHER_RES = 12
    OFFICE = 20
    SCHOOL = 21
    OTHER_NONRES = 22


class PhiCertIHGType(Enum):
    STANDARD = 2
    RES_CUSTOM = 3
    NONRES_CUSTOM = 4


class PhiCertOccupancyType(Enum):
    STANDARD = 1
    CUSTOM = 2


class PhiCertType(Enum):
    PASSIVE_HOUSE = 1
    ENERPHIT = 2
    LOW_ENERGY_BUILDING = 3
    OTHER = 4


class PhiCertClass(Enum):
    CLASSIC = 1
    PLUS = 2
    PREMIUM = 3


class PhiCertificationPEType(Enum):
    PE = 1
    PER = 2


class PhiCertEnerPHitType(Enum):
    BY_COMPONENT = 1
    BY_DEMAND = 2


class PhiCertRetrofitType(Enum):
    NEW_BUILDING = 1
    RETROFIT = 2
    STEP_BY_STEP_RETROFIT = 3
