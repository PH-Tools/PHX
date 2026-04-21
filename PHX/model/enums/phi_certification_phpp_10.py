# -*- Python Version: 3.10 -*-

"""Valid 'types' for PHI Certification Settings (PHPP v10)."""

from enum import Enum


class PhiCertBuildingUseType(Enum):
    """Building use type for PHI certification (PHPP v10).

    Values:
        DWELLING: Residential dwelling.
        OTHER_RES: Other residential use type.
        OFFICE: Office building.
        SCHOOL_HALF_DAY: School with half-day operation.
        SCHOOL_FULL_DAY: School with full-day operation.
        OTHER_NONRES: Other non-residential use type.
    """

    DWELLING = 10
    OTHER_RES = 12
    OFFICE = 20
    SCHOOL_HALF_DAY = 21
    SCHOOL_FULL_DAY = 22
    OTHER_NONRES = 23


class PhiCertIHGType(Enum):
    """Internal heat gains calculation method for PHI certification (PHPP v10).

    Values:
        STANDARD: Standard IHG values per PHI protocol.
        RES_CUSTOM: Custom IHG values for residential buildings.
        NONRES_CUSTOM: Custom IHG values for non-residential buildings.
    """

    STANDARD = 2
    RES_CUSTOM = 3
    NONRES_CUSTOM = 4


class PhiCertType(Enum):
    """PHI certification standard type (PHPP v10).

    Values:
        PASSIVE_HOUSE: Passive House certification.
        ENERPHIT_BY_COMPONENT: EnerPHit certification via component-level criteria.
        ENERPHIT_BY_DEMAND: EnerPHit certification via energy demand criteria.
        LOW_ENERGY_BUILDING: PHI Low Energy Building certification.
        OTHER: Other certification type.
    """

    PASSIVE_HOUSE = 10
    ENERPHIT_BY_COMPONENT = 21
    ENERPHIT_BY_DEMAND = 22
    LOW_ENERGY_BUILDING = 30
    OTHER = 44


class PhiCertClass(Enum):
    """PHI certification class based on renewable energy generation (PHPP v10).

    Values:
        CLASSIC: Classic Passive House (no renewable energy generation requirement).
        PLUS: Passive House Plus (moderate renewable energy generation).
        PREMIUM: Passive House Premium (high renewable energy generation).
        CLASSIC_PE: Classic Passive House using Primary Energy (non-renewable) evaluation.
    """

    CLASSIC = 10
    PLUS = 20
    PREMIUM = 30
    CLASSIC_PE = 11


class PhiCertificationPEType(Enum):
    """Primary energy factor source for PHI certification (PHPP v10).

    Values:
        STANDARD: Standard primary energy factors per PHI dataset.
        PROJECT_SPECIFIC: Project-specific primary energy factors.
    """

    STANDARD = 1
    PROJECT_SPECIFIC = 2


class PhiCertRetrofitType(Enum):
    """Building retrofit status for PHI certification (PHPP v10).

    Values:
        NEW_BUILDING: New construction project.
        RETROFIT: Complete retrofit project.
        STEP_BY_STEP_RETROFIT: Phased step-by-step retrofit project.
    """

    NEW_BUILDING = 1
    RETROFIT = 2
    STEP_BY_STEP_RETROFIT = 3
