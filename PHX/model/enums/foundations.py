# -*- Python Version: 3.10 -*-

"""Valid 'types' for Foundation Options and Types"""

from enum import Enum


class CalculationSetting(Enum):
    """Foundation heat loss calculation setting.

    Values:
        USER_DEFINED: User-specified foundation calculation parameters.
    """

    USER_DEFINED = 6


class FoundationType(Enum):
    """Classification of foundation types for ground heat loss calculations.

    Values:
        HEATED_BASEMENT: Fully conditioned basement within the thermal envelope.
        UNHEATED_BASEMENT: Unconditioned basement below the thermal envelope.
        SLAB_ON_GRADE: Foundation slab directly on soil.
        VENTED_CRAWLSPACE: Ventilated crawlspace below the building.
        NONE: No foundation type assigned.
    """

    HEATED_BASEMENT = 1
    UNHEATED_BASEMENT = 2
    SLAB_ON_GRADE = 3
    VENTED_CRAWLSPACE = 4
    NONE = 5


class PerimeterInsulationPosition(Enum):
    """Orientation of perimeter insulation at the foundation edge.

    Values:
        UNDEFINED: Insulation position not specified.
        HORIZONTAL: Insulation placed horizontally (e.g. wing insulation).
        VERTICAL: Insulation placed vertically along the foundation wall.
    """

    UNDEFINED = 1
    HORIZONTAL = 2
    VERTICAL = 3
