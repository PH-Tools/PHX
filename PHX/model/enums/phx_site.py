# -*- Python Version: 3.10 -*-

"""Valid 'types' for Site Settings."""

from enum import Enum


class SiteSelection(Enum):
    """Selection source for site location data.

    Values:
        WUFI_DATABASE: Site data from the WUFI climate database.
        USER_DEFINED: Site data entered manually by the user.
        STANDARD: Standard default site data.
    """

    WUFI_DATABASE = 1
    USER_DEFINED = 2
    STANDARD = 3


class SiteClimateSelection(Enum):
    """Selection source for climate data.

    Values:
        STANDARD: Standard climate data set.
        WUFI_DATABASE: Climate data from the WUFI climate database.
        USER_DEFINED: Climate data entered manually by the user.
    """

    STANDARD = 1
    WUFI_DATABASE = 2
    USER_DEFINED = 6


class SiteEnergyFactorSelection(Enum):
    """Selection source for primary energy and CO2 conversion factors.

    Values:
        STANDARD_USA: Standard US energy factors.
        STANDARD_GERMANY: Standard German energy factors.
        STANDARD_ITALY: Standard Italian energy factors.
        STANDARD_CANADA: Standard Canadian energy factors.
        USER_DEFINED: User-specified energy factors.
    """

    STANDARD_USA = 1
    STANDARD_GERMANY = 2
    STANDARD_ITALY = 2
    STANDARD_CANADA = 4
    USER_DEFINED = 6
