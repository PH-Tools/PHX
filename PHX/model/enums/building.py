# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Valid 'types' for Building Elements."""

from __future__ import annotations

from enum import Enum


class ComponentFaceType(Enum):
    NONE = 0
    WALL = 1
    FLOOR = 2
    ROOF_CEILING = 3
    AIR_BOUNDARY = 3
    WINDOW = 4
    ADIABATIC = 5
    CUSTOM = 6

    @classmethod
    def by_angle(cls, _angle: float) -> ComponentFaceType:
        if _angle < 70.0:
            return cls.ROOF_CEILING
        if _angle > 110.0:
            return cls.FLOOR
        return cls.WALL


class ComponentExposureExterior(Enum):
    NONE = 0
    EXTERIOR = -1
    GROUND = -2
    SURFACE = -3


class ComponentFaceOpacity(Enum):
    OPAQUE = 1
    TRANSPARENT = 2
    AIRBOUNDARY = 3


class ComponentColor(Enum):
    EXT_WALL_INNER = 1
    EXT_WALL_OUTER = 2
    INNER_WALL = 3
    WINDOW = 4
    FLOOR = 5
    CEILING = 6
    SLOPED_ROOF_OUTER = 7
    SLOPED_ROOF_INNER = 8
    SLOPED_ROOF_THATCH = 9  # WTF?
    FLAT_ROOF_OUTER = 10
    FLAT_ROOF_INNER = 11
    SURFACE_GROUND_CONTACT = 12
    GROUND_ABOVE = 13
    GROUND_BENEATH = 14


class ThermalBridgeType(Enum):
    AMBIENT = 15
    PERIMETER = 16
    UNDERGROUND = 17


class SpecificHeatCapacity(Enum):
    LIGHTWEIGHT = 1
    MIXED = 2
    MASSIVE = 3


class WufiVolumeGrossMode(Enum):
    USER_DEFINED = 6
    FROM_VISUALIZED_COMPONENTS = 7


class WufiVolumeNetMode(Enum):
    ESTIMATED_FROM_GROSS = 4
    FROM_GROSS_AND_COMPONETS = 5
    USER_DEFINED = 6
    FROM_VISUALIZED_COMPONENTS = 7


class WufiWeightedFloorAreaMode(Enum):
    FROM_VISUALIZED_GEOMETRY = 2
    ESTIMATED_FROM_GROSS_VOLUME = 4
    USER_DEFINED = 6


class ZoneType(Enum):
    SIMULATED = 1
    ATTACHED = 2


class AttachedZoneType(Enum):
    NONE = 0
    UNHEATED_SPACE = 1
    UNHEATED_CELLAR = 2
    UNHEATED_CRAWLSPACE = 3
    UNHEATED_WINTER_GARDEN = 4
    UNHEATED_ATTIC = 5
    CONDITIONED = 6


class WindExposureType(Enum):
    SEVERAL_SIDES_EXPOSED_NO_SCREENING = 1
    SEVERAL_SIDES_EXPOSED_MODERATE_SCREENING = 2
    SEVERAL_SIDES_EXPOSED_HIGH_SCREENING = 3
    ONE_SIDE_EXPOSED_NO_SCREENING = 4
    ONE_SIDE_EXPOSED_MODERATE_SCREENING = 5
    ONE_SIDE_EXPOSED_HIGH_SCREENING = 7
    USER_DEFINED = 6
