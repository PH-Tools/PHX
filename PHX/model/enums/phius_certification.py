# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

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
