# -*- Python Version: 3.10 -*-

"""Valid 'types' for Building Elements."""

from __future__ import annotations

from enum import Enum


class ComponentFaceType(Enum):
    """Classification of building component face orientations.

    Values:
        NONE: Unclassified face type.
        WALL: Vertical wall surface.
        FLOOR: Horizontal floor surface.
        ROOF_CEILING: Roof or ceiling surface.
        WINDOW: Glazed window surface.
        ADIABATIC: Adiabatic boundary (no heat flow).
        CUSTOM: User-defined face type.
        AIR_BOUNDARY: Air boundary between zones.
    """

    NONE = 0
    WALL = 1
    FLOOR = 2
    ROOF_CEILING = 3
    WINDOW = 4
    ADIABATIC = 5
    CUSTOM = 6
    AIR_BOUNDARY = 7

    @classmethod
    def by_angle(cls, _angle: float) -> ComponentFaceType:
        """Return the face type inferred from a surface tilt angle.

        Arguments:
        ----------
            * _angle (float): The tilt angle in degrees from horizontal
                (0 = facing up, 180 = facing down).

        Returns:
        --------
            * ComponentFaceType: ROOF_CEILING if < 70, FLOOR if > 110, else WALL.
        """
        if _angle < 70.0:
            return cls.ROOF_CEILING
        if _angle > 110.0:
            return cls.FLOOR
        return cls.WALL


class ComponentExposureExterior(Enum):
    """Exterior exposure condition for a building component.

    Negative sentinel values represent special attachment types used by WUFI.
    Positive integers represent attachment to other thermal zones and are
    created dynamically at runtime via ``_missing_``.

    Values:
        NONE: No exposure assigned.
        EXTERIOR: Exposed to outdoor air.
        GROUND: In contact with ground.
        SURFACE: Exposed to another surface (interior boundary).
    """

    NONE = 0
    EXTERIOR = -1
    GROUND = -2
    SURFACE = -3

    @classmethod
    def _missing_(cls, value):
        """Allow dynamic, runtime-created pseudo-members for attached zone ids.

        WUFI uses negative sentinel values for special attachments (exterior/ground/surface)
        and positive integers for attachments to other zones. The standard Enum type does not
        include those zone id members up front, so we create them on-demand.
        """
        if isinstance(value, str) and value.isdigit():
            value = int(value)

        if isinstance(value, int) and value > 0:
            pseudo_member = object.__new__(cls)
            pseudo_member._value_ = value
            pseudo_member._name_ = f"ZONE_{value}"
            cls._value2member_map_[value] = pseudo_member
            return pseudo_member

        return None


class ComponentFaceOpacity(Enum):
    """Opacity classification of a building component face.

    Values:
        OPAQUE: Solid, non-transparent surface (walls, roofs, floors).
        TRANSPARENT: Glazed or translucent surface (windows, curtain walls).
        AIRBOUNDARY: Virtual air boundary between zones.
    """

    OPAQUE = 1
    TRANSPARENT = 2
    AIRBOUNDARY = 3


class ComponentColor(Enum):
    """Display color assignment for building components in WUFI visualization.

    Values:
        EXT_WALL_INNER: Interior side of an exterior wall.
        EXT_WALL_OUTER: Exterior side of an exterior wall.
        INNER_WALL: Interior partition wall.
        WINDOW: Window or glazed component.
        FLOOR: Floor surface.
        CEILING: Ceiling surface.
        SLOPED_ROOF_OUTER: Exterior side of a sloped roof.
        SLOPED_ROOF_INNER: Interior side of a sloped roof.
        SLOPED_ROOF_THATCH: Thatch-style sloped roof.
        FLAT_ROOF_OUTER: Exterior side of a flat roof.
        FLAT_ROOF_INNER: Interior side of a flat roof.
        SURFACE_GROUND_CONTACT: Surface in contact with ground.
        GROUND_ABOVE: Ground surface above the component.
        GROUND_BENEATH: Ground surface beneath the component.
    """

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
    """Classification of thermal bridge boundary conditions.

    Values:
        AMBIENT: Thermal bridge exposed to outdoor ambient air.
        PERIMETER: Thermal bridge at the building perimeter (e.g. slab edge).
        UNDERGROUND: Thermal bridge in contact with ground.
    """

    AMBIENT = 15
    PERIMETER = 16
    UNDERGROUND = 17


class SpecificHeatCapacityType(Enum):
    """Thermal mass classification for a building zone.

    Values:
        LIGHTWEIGHT: Light construction (e.g. wood frame).
        MIXED: Mixed construction weight.
        MASSIVE: Heavy construction (e.g. concrete, masonry).
        USER_DEFINED: User-specified heat capacity value.
    """

    LIGHTWEIGHT = 1
    MIXED = 2
    MASSIVE = 3
    USER_DEFINED = 6

class SpecificHeatCapacityValueWhM2K(Enum):
    """Specific heat capacity values in Wh/m2K for standard construction types.

    Values:
        LIGHTWEIGHT: 60 Wh/m2K for lightweight construction.
        MIXED: 132 Wh/m2K for mixed construction.
        MASSIVE: 204 Wh/m2K for massive construction.
    """

    LIGHTWEIGHT = 60
    MIXED = 132
    MASSIVE = 204


class WufiVolumeGrossMode(Enum):
    """Method for determining gross building volume in WUFI.

    Values:
        USER_DEFINED: Gross volume entered manually by the user.
        FROM_VISUALIZED_COMPONENTS: Gross volume calculated from modeled component geometry.
    """

    USER_DEFINED = 6
    FROM_VISUALIZED_COMPONENTS = 7


class WufiVolumeNetMode(Enum):
    """Method for determining net interior volume in WUFI.

    Values:
        ESTIMATED_FROM_GROSS: Net volume estimated as a fraction of gross volume.
        FROM_GROSS_AND_COMPONETS: Net volume derived from gross volume minus component thicknesses.
        USER_DEFINED: Net volume entered manually by the user.
        FROM_VISUALIZED_COMPONENTS: Net volume calculated from modeled component geometry.
    """

    ESTIMATED_FROM_GROSS = 4
    FROM_GROSS_AND_COMPONETS = 5
    USER_DEFINED = 6
    FROM_VISUALIZED_COMPONENTS = 7


class WufiWeightedFloorAreaMode(Enum):
    """Method for determining weighted floor area (TFA/iCFA) in WUFI.

    Values:
        FROM_VISUALIZED_GEOMETRY: Floor area calculated from modeled floor geometry.
        ESTIMATED_FROM_GROSS_VOLUME: Floor area estimated from the gross volume.
        USER_DEFINED: Floor area entered manually by the user.
    """

    FROM_VISUALIZED_GEOMETRY = 2
    ESTIMATED_FROM_GROSS_VOLUME = 4
    USER_DEFINED = 6


class ZoneType(Enum):
    """Classification of thermal zones in the energy model.

    Values:
        SIMULATED: Zone included in the active energy balance simulation.
        ATTACHED: Adjacent unconditioned zone not directly simulated.
    """

    SIMULATED = 1
    ATTACHED = 2


class AttachedZoneType(Enum):
    """Specific type of an attached (non-simulated) thermal zone.

    Values:
        NONE: No attached zone type assigned.
        UNHEATED_SPACE: Generic unheated adjacent space.
        UNHEATED_CELLAR: Unheated basement or cellar.
        UNHEATED_CRAWLSPACE: Unheated crawlspace below the building.
        UNHEATED_WINTER_GARDEN: Unheated sunroom or winter garden.
        UNHEATED_ATTIC: Unheated attic space.
        CONDITIONED: Attached zone that is conditioned.
    """

    NONE = 0
    UNHEATED_SPACE = 1
    UNHEATED_CELLAR = 2
    UNHEATED_CRAWLSPACE = 3
    UNHEATED_WINTER_GARDEN = 4
    UNHEATED_ATTIC = 5
    CONDITIONED = 6


class WindExposureType(Enum):
    """Wind exposure classification for infiltration calculations.

    Values:
        SEVERAL_SIDES_EXPOSED_NO_SCREENING: Multiple facades exposed, no wind screening.
        SEVERAL_SIDES_EXPOSED_MODERATE_SCREENING: Multiple facades exposed, moderate wind screening.
        SEVERAL_SIDES_EXPOSED_HIGH_SCREENING: Multiple facades exposed, high wind screening.
        ONE_SIDE_EXPOSED_NO_SCREENING: Single facade exposed, no wind screening.
        ONE_SIDE_EXPOSED_MODERATE_SCREENING: Single facade exposed, moderate wind screening.
        ONE_SIDE_EXPOSED_HIGH_SCREENING: Single facade exposed, high wind screening.
        USER_DEFINED: User-specified wind exposure coefficient.
    """

    SEVERAL_SIDES_EXPOSED_NO_SCREENING = 1
    SEVERAL_SIDES_EXPOSED_MODERATE_SCREENING = 2
    SEVERAL_SIDES_EXPOSED_HIGH_SCREENING = 3
    ONE_SIDE_EXPOSED_NO_SCREENING = 4
    ONE_SIDE_EXPOSED_MODERATE_SCREENING = 5
    ONE_SIDE_EXPOSED_HIGH_SCREENING = 7
    USER_DEFINED = 6
