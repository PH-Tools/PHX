# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Valid 'types' for PHIUS Certification Settings."""

from enum import Enum


class PhiusCertificationBuildingCategoryType(Enum):
    RESIDENTIAL_BUILDING = 1
    NONRESIDENTIAL_BUILDING = 2


class PhiusCertificationBuildingUseType(Enum):
    RESIDENTIAL = 1
    OFFICE = 4
    SCHOOL = 5
    OTHER = 6
    UNDEFINED = 7


class PhiusCertificationBuildingStatus(Enum):
    IN_PLANNING = 1
    UNDER_CONSTRUCTION = 2
    COMPLETE = 3


class PhiusCertificationBuildingType(Enum):
    NEW_CONSTRUCTION = 1
    RETROFIT = 2
    MIXED = 3


class PhiusCertificationProgram(Enum):
    DEFAULT = 1
    PHIUS_2015 = 2
    PHIUS_2018 = 3
    ITALIAN = 4
    PHIUS_2018_CORE = 5
    PHIUS_2018_ZERO = 6
    PHIUS_2021_CORE = 7
    PHIUS_2021_ZERO = 8
