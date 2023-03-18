# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Valid 'types' for Foundation Options and Types"""

from enum import Enum


class CalculationSetting(Enum):
    USER_DEFINED = 6

class FoundationType(Enum):
    HEATED_BASEMENT = 1
    UNHEATED_BASEMENT = 2
    SLAB_ON_GRADE = 3
    VENTED_CRAWLSPACE = 4
    NONE = 5

class PerimeterInsulationPosition(Enum):
    UNDEFINED = 1
    HORIZONTAL = 2
    VERTICAL = 3