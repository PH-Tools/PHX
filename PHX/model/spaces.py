# -*- Python Version: 3.10 -*-

"""PHX Space (Room) classes and utilities for Passive House zone ventilation grouping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Optional

from PHX.model.identity import IdentityNamespaces, allocate_identity
from PHX.model.programs.lighting import PhxProgramLighting
from PHX.model.programs.occupancy import PhxProgramOccupancy
from PHX.model.programs.ventilation import PhxProgramVentilation


def _area_weighted_height(space_a: PhxSpace, space_b: PhxSpace, _attr_name: str) -> float:
    """Return the floor-area-weighted average of a height attribute of two spaces."""
    try:
        weighted_height_a = getattr(space_a, _attr_name) * space_a.floor_area
        weighted_height_b = getattr(space_b, _attr_name) * space_b.floor_area
        total_floor_area = space_a.floor_area + space_b.floor_area
        return (weighted_height_a + weighted_height_b) / total_floor_area
    except ZeroDivisionError:
        return 0.0


def area_weighted_clear_height(space_a: PhxSpace, space_b: PhxSpace) -> float:
    """Return the area-weighted average clear height of two spaces.

    Arguments:
    ----------
        * space_a (PhxSpace): The first space.
        * space_b (PhxSpace): The second space.

    Returns:
    --------
        * float: The weighted average clear height (m). Returns 0.0 if the combined floor area is zero.
    """
    return _area_weighted_height(space_a, space_b, "clear_height")


def area_weighted_ventilation_reference_height(space_a: PhxSpace, space_b: PhxSpace) -> float:
    """Return the area-weighted average ventilation reference height of two spaces.

    Arguments:
    ----------
        * space_a (PhxSpace): The first space.
        * space_b (PhxSpace): The second space.

    Returns:
    --------
        * float: The weighted average ventilation reference height (m). Returns 0.0 if the combined floor area is zero.
    """
    return _area_weighted_height(space_a, space_b, "ventilation_reference_height")


def spaces_are_not_addable(space_a: PhxSpace, space_v: PhxSpace) -> bool:
    """Return True if the two spaces cannot be merged.

    Spaces are incompatible for addition when they differ in WUFI space type
    or are served by different ventilation units.

    Arguments:
    ----------
        * space_a (PhxSpace): The first space.
        * space_v (PhxSpace): The second space.

    Returns:
    --------
        * bool: True if the spaces differ in wufi_type or vent_unit_id_num.
    """
    return any(
        (
            space_a.wufi_type != space_v.wufi_type,
            space_a.vent_unit_id_num != space_v.vent_unit_id_num,
        )
    )


@dataclass
class PhxSpace:
    """A single ventilation space (room) within a PHX zone.

    Represents one room-level entry in the WUFI-Passive / PHPP model. Each space
    carries its own geometry (floor area, volume, clear height), a WUFI space-type
    classification, and references to ventilation, occupancy, and lighting programs.
    Spaces that share the same WUFI type and ventilation unit can be merged via
    addition for Phius grouped-space reporting.

    Attributes:
        id_num (int): Auto-incrementing identifier assigned on creation.
        display_name (str): Human-readable space name. Default: 'Unnamed_Space'.
        wufi_type (int): WUFI-Passive space-type code (e.g. 1=Living, 2=Kitchen). Default: 99 (User Determined).
        quantity (int): Number of identical spaces this entry represents. Default: 1.
        floor_area (float): Gross floor area of the space (m2). Default: 0.0.
        weighted_floor_area (float): iCFA/TFA-weighted floor area (m2). Default: 0.0.
        net_volume (float): Net interior volume of the space (m3). Default: 0.0.
        clear_height (float): Average floor-to-ceiling clear height (m). Default: 2.5.
        ventilation_reference_height (float): The height PHPP multiplies the weighted floor
            area by for the ventilated volume Vv (the 'Addl vent' clear-height column).
            2.5 m per PHI convention, independent of the space's actual clear_height. Default: 2.5.
        vent_unit_id_num (Optional[int]): ID number of the assigned ventilation unit
            (ERV/HRV), or None when no mechanical unit is assigned. Default: None.
        vent_unit_display_name (str): Display name of the assigned ventilation unit. Default: ''.
        ventilation (PhxProgramVentilation): Ventilation program with airflow loads and schedules.
        occupancy (PhxProgramOccupancy): Occupancy program with people density and schedules.
        lighting (PhxProgramLighting): Lighting program with installed power and schedules.
        electric_equipment (None): Placeholder for future electric equipment program. Default: None.
    """

    _count: ClassVar[int] = 0

    id_num: int = field(init=False, default=0)
    display_name: str = "Unnamed_Space"
    wufi_type: int = 99  # User Determined
    quantity: int = 1
    floor_area: float = 0.0
    weighted_floor_area: float = 0.0
    net_volume: float = 0.0
    clear_height: float = 2.5
    ventilation_reference_height: float = 2.5

    # -- Ventilation Unit (ERV) number
    vent_unit_id_num: Optional[int] = None
    vent_unit_display_name: str = ""

    # -- Programs
    ventilation: PhxProgramVentilation = field(default_factory=PhxProgramVentilation)
    occupancy: PhxProgramOccupancy = field(default_factory=PhxProgramOccupancy)
    lighting: PhxProgramLighting = field(default_factory=PhxProgramLighting)

    electric_equipment = None

    def __post_init__(self) -> None:
        self.id_num = allocate_identity(IdentityNamespaces.SPACES, self.__class__)

    @property
    def peak_occupancy(self) -> float:
        """Returns the peak occupancy for the space (Num. of people)."""
        return self.occupancy.load.people_per_m2 * self.floor_area

    @peak_occupancy.setter
    def peak_occupancy(self, value: float) -> None:
        """Sets the peak occupancy for the space (Num. of people)."""
        try:
            self.occupancy.load.people_per_m2 = value / self.floor_area
        except ZeroDivisionError:
            self.occupancy.load.people_per_m2 = 0.0

    @property
    def has_ventilation_airflow(self) -> bool:
        """Returns True if the space has ventilation airflow."""
        return self.ventilation.has_ventilation_airflow

    def __add__(self, other: PhxSpace) -> PhxSpace:
        """Adds two spaces together.

        This is used to report out 'grouped' spaces for Phius. In almost all
        other cases, spaces should be kept separated. Note that the occupancy,
        lighting, and ventilation schedules are NOT merged, however the
        ventilation loads ARE added together.

        Neither source space is modified: the merged space gets its own
        PhxProgramVentilation carrying the summed load, so the sum never flows
        back into a source Space's program. The WUFI and METr exporters no
        longer call this; they write read-only rows from
        PHX.model.ventilation_rooms.ventilation_rooms(), which reproduces this
        arithmetic without constructing a PhxSpace.

        The *schedule* is deliberately shared rather than copied. Schedules are
        project-registered utilization patterns referenced from the output by
        'id_num'; a copy would be unregistered and the exporters would emit a
        dangling pattern reference.
        """
        if spaces_are_not_addable(self, other):
            raise ValueError(f"Space {self.display_name} cannot be added to space {other.display_name}.")

        return PhxSpace(
            display_name=self.vent_unit_display_name,
            wufi_type=self.wufi_type,
            quantity=1,
            floor_area=self.floor_area + other.floor_area,
            weighted_floor_area=self.weighted_floor_area + other.weighted_floor_area,
            net_volume=self.net_volume + other.net_volume,
            clear_height=area_weighted_clear_height(self, other),
            ventilation_reference_height=area_weighted_ventilation_reference_height(self, other),
            vent_unit_id_num=self.vent_unit_id_num,
            vent_unit_display_name=self.vent_unit_display_name,
            ventilation=PhxProgramVentilation(
                display_name=self.ventilation.display_name,
                load=self.ventilation.load + other.ventilation.load,
                schedule=self.ventilation.schedule,
            ),
            occupancy=self.occupancy,
            lighting=self.lighting,
        )
