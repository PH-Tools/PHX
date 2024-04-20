# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Valid 'types' for Site Settings."""

from enum import Enum


class SiteSelection(Enum):
    WUFI_DATABASE = 1
    USER_DEFINED = 2
    STANDARD = 3


class SiteClimateSelection(Enum):
    STANDARD = 1
    WUFI_DATABASE = 2
    USER_DEFINED = 6


class SiteEnergyFactorSelection(Enum):
    STANDARD_USA = 1
    STANDARD_GERMANY = 2
    STANDARD_ITALY = 2
    STANDARD_CANADA = 4
    USER_DEFINED = 6
