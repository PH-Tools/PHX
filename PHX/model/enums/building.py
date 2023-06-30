# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Valid 'types' for Building Elements."""

from __future__ import annotations
from enum import Enum


class ComponentFaceType(Enum):
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
