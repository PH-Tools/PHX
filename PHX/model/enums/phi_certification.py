# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Valid 'types' for PHI Certification Settings."""

from enum import Enum

class PhiCertificationBuildingCategoryType(Enum):
    RESIDENTIAL_BUILDING = 1
    NONRESIDENTIAL_BUILDING = 2

class PhiCertificationBuildingUseType(Enum):
        DWELLING = 10
        NURSING_HOME = 11
        OTHER_RES = 12
        OFFICE = 20
        SCHOOL = 21
        OTHER_NONRES = 22

class PhiCertificationIHGType(Enum):
        STANDARD = 2
        RES_CUSTOM = 3
        NONRES_CUSTOM = 4

class PhiCertificationOccupancyType(Enum):
        STANDARD = 1
        CUSTOM = 2

class PhiCertificationType(Enum):
    PASSIVE_HOUSE = 1
    ENERPHIT = 2
    LOW_ENERGY_BUILDING = 3
    OTHER = 4


class PhiCertificationClass(Enum):
    CLASSIC = 1
    PLUS = 2
    PREMIUM = 3


class PhiCertificationPEType(Enum):
    PE = 1
    PER = 2


class PhiCertificationEnerPHitType(Enum):
    BY_COMPONENT = 1
    BY_DEMAND = 2


class PhiCertificationRetrofitType(Enum):
    NEW_BUILDING = 1
    RETROFIT = 2
    STEP_BY_STEP_RETROFIT = 3
