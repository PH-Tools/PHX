# -*- Python Version: 3.10 -*-

"""Valid 'types' for PHIUS Certification Settings."""

from enum import Enum


class PhiusCertificationBuildingCategoryType(Enum):
    """Building category for Phius certification.

    Values:
        RESIDENTIAL_BUILDING: Residential building category.
        NONRESIDENTIAL_BUILDING: Non-residential building category.
    """

    RESIDENTIAL_BUILDING = 1
    NONRESIDENTIAL_BUILDING = 2


class PhiusCertificationBuildingUseType(Enum):
    """Building use type for Phius certification.

    Values:
        RESIDENTIAL: Residential use.
        OFFICE: Office building use.
        SCHOOL: School building use.
        OTHER: Other building use type.
        UNDEFINED: Use type not yet defined.
    """

    RESIDENTIAL = 1
    OFFICE = 4
    SCHOOL = 5
    OTHER = 6
    UNDEFINED = 7


class PhiusCertificationBuildingStatus(Enum):
    """Current construction status of the building for Phius certification.

    Values:
        IN_PLANNING: Building is in the design/planning phase.
        UNDER_CONSTRUCTION: Building is currently under construction.
        COMPLETE: Building construction is complete.
    """

    IN_PLANNING = 1
    UNDER_CONSTRUCTION = 2
    COMPLETE = 3


class PhiusCertificationBuildingType(Enum):
    """Building construction type for Phius certification.

    Values:
        NEW_CONSTRUCTION: New construction project.
        RETROFIT: Retrofit of an existing building.
        MIXED: Mixed new construction and retrofit.
    """

    NEW_CONSTRUCTION = 1
    RETROFIT = 2
    MIXED = 3


class PhiusCertificationProgram(Enum):
    """Phius certification program version.

    Values:
        DEFAULT: Default certification program.
        PHIUS_2015: Phius+ 2015 standard.
        PHIUS_2018: Phius 2018 standard.
        ITALIAN: Italian Passive House standard.
        PHIUS_2018_CORE: Phius CORE 2018 (envelope-only) standard.
        PHIUS_2018_ZERO: Phius ZERO 2018 (net-zero) standard.
        PHIUS_2021_CORE: Phius CORE 2021 (envelope-only) standard.
        PHIUS_2021_ZERO: Phius ZERO 2021 (net-zero) standard.
    """

    DEFAULT = 1
    PHIUS_2015 = 2
    PHIUS_2018 = 3
    ITALIAN = 4
    PHIUS_2018_CORE = 5
    PHIUS_2018_ZERO = 6
    PHIUS_2021_CORE = 7
    PHIUS_2021_ZERO = 8
