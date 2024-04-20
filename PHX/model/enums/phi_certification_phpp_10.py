# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Valid 'types' for PHI Certification Settings (PHPP v10)."""

from enum import Enum


class PhiCertBuildingUseType(Enum):
    DWELLING = 10
    OTHER_RES = 12
    OFFICE = 20
    SCHOOL_HALF_DAY = 21
    SCHOOL_FULL_DAY = 22
    OTHER_NONRES = 23


class PhiCertIHGType(Enum):
    STANDARD = 2
    RES_CUSTOM = 3
    NONRES_CUSTOM = 4


class PhiCertType(Enum):
    PASSIVE_HOUSE = 10
    ENERPHIT_BY_COMPONENT = 21
    ENERPHIT_BY_DEMAND = 22
    LOW_ENERGY_BUILDING = 30
    OTHER = 44


class PhiCertClass(Enum):
    CLASSIC = 10
    PLUS = 20
    PREMIUM = 30
    CLASSIC_PE = 11


class PhiCertificationPEType(Enum):
    STANDARD = 1
    PROJECT_SPECIFIC = 2


class PhiCertRetrofitType(Enum):
    NEW_BUILDING = 1
    RETROFIT = 2
    STEP_BY_STEP_RETROFIT = 3
