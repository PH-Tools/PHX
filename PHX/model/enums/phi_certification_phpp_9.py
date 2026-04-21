# -*- Python Version: 3.10 -*-

"""Valid 'types' for PHI Certification Settings (PHPP v9)."""

from enum import Enum


class PhiCertBuildingCategoryType(Enum):
    """Building category for PHI certification (PHPP v9).

    Values:
        RESIDENTIAL_BUILDING: Residential building category.
        NONRESIDENTIAL_BUILDING: Non-residential building category.
    """

    RESIDENTIAL_BUILDING = 1
    NONRESIDENTIAL_BUILDING = 2


class PhiCertBuildingUseType(Enum):
    """Building use type for PHI certification (PHPP v9).

    Values:
        DWELLING: Residential dwelling.
        NURSING_HOME: Nursing home or assisted living facility.
        OTHER_RES: Other residential use type.
        OFFICE: Office building.
        SCHOOL: School building.
        OTHER_NONRES: Other non-residential use type.
    """

    DWELLING = 10
    NURSING_HOME = 11
    OTHER_RES = 12
    OFFICE = 20
    SCHOOL = 21
    OTHER_NONRES = 22


class PhiCertIHGType(Enum):
    """Internal heat gains calculation method for PHI certification (PHPP v9).

    Values:
        STANDARD: Standard IHG values per PHI protocol.
        RES_CUSTOM: Custom IHG values for residential buildings.
        NONRES_CUSTOM: Custom IHG values for non-residential buildings.
    """

    STANDARD = 2
    RES_CUSTOM = 3
    NONRES_CUSTOM = 4


class PhiCertOccupancyType(Enum):
    """Occupancy calculation method for PHI certification (PHPP v9).

    Values:
        STANDARD: Standard occupancy based on TFA per PHI protocol.
        CUSTOM: User-specified occupancy count.
    """

    STANDARD = 1
    CUSTOM = 2


class PhiCertType(Enum):
    """PHI certification standard type (PHPP v9).

    Values:
        PASSIVE_HOUSE: Passive House certification.
        ENERPHIT: EnerPHit retrofit certification.
        LOW_ENERGY_BUILDING: PHI Low Energy Building certification.
        OTHER: Other certification type.
    """

    PASSIVE_HOUSE = 1
    ENERPHIT = 2
    LOW_ENERGY_BUILDING = 3
    OTHER = 4


class PhiCertClass(Enum):
    """PHI certification class based on renewable energy generation (PHPP v9).

    Values:
        CLASSIC: Classic Passive House (no renewable energy generation requirement).
        PLUS: Passive House Plus (moderate renewable energy generation).
        PREMIUM: Passive House Premium (high renewable energy generation).
    """

    CLASSIC = 1
    PLUS = 2
    PREMIUM = 3


class PhiCertificationPEType(Enum):
    """Primary energy evaluation method for PHI certification (PHPP v9).

    Values:
        PE: Primary Energy (non-renewable).
        PER: Primary Energy Renewable.
    """

    PE = 1
    PER = 2


class PhiCertEnerPHitType(Enum):
    """EnerPHit certification compliance pathway (PHPP v9).

    Values:
        BY_COMPONENT: Compliance via component-level U-value criteria.
        BY_DEMAND: Compliance via whole-building energy demand criteria.
    """

    BY_COMPONENT = 1
    BY_DEMAND = 2


class PhiCertRetrofitType(Enum):
    """Building retrofit status for PHI certification (PHPP v9).

    Values:
        NEW_BUILDING: New construction project.
        RETROFIT: Complete retrofit project.
        STEP_BY_STEP_RETROFIT: Phased step-by-step retrofit project.
    """

    NEW_BUILDING = 1
    RETROFIT = 2
    STEP_BY_STEP_RETROFIT = 3
