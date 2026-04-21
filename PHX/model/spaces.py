# -*- Python Version: 3.10 -*-

"""PHX Space (Room) classes and utilities for Passive House zone ventilation grouping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from PHX.model.programs.lighting import PhxProgramLighting
from PHX.model.programs.occupancy import PhxProgramOccupancy
from PHX.model.programs.ventilation import PhxProgramVentilation


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
    try:
        weighted_height_a = space_a.clear_height * space_a.floor_area
        weighted_height_b = space_b.clear_height * space_b.floor_area
        total_floor_area = space_a.floor_area + space_b.floor_area
        return (weighted_height_a + weighted_height_b) / total_floor_area
    except ZeroDivisionError:
        return 0.0


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
        vent_unit_id_num (int): ID number of the assigned ventilation unit (ERV/HRV). Default: 0.
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

    # -- Ventilation Unit (ERV) number
    vent_unit_id_num: int = 0
    vent_unit_display_name: str = ""

    # -- Programs
    ventilation: PhxProgramVentilation = field(default_factory=PhxProgramVentilation)
    occupancy: PhxProgramOccupancy = field(default_factory=PhxProgramOccupancy)
    lighting: PhxProgramLighting = field(default_factory=PhxProgramLighting)

    electric_equipment = None

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

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
        """
        if spaces_are_not_addable(self, other):
            raise ValueError(f"Space {self.display_name} cannot be added to space {other.display_name}.")

        new_space = PhxSpace(
            display_name=self.vent_unit_display_name,
            wufi_type=self.wufi_type,
            quantity=1,
            floor_area=self.floor_area + other.floor_area,
            weighted_floor_area=self.weighted_floor_area + other.weighted_floor_area,
            net_volume=self.net_volume + other.net_volume,
            clear_height=area_weighted_clear_height(self, other),
            vent_unit_id_num=self.vent_unit_id_num,
            vent_unit_display_name=self.vent_unit_display_name,
            ventilation=self.ventilation,
            occupancy=self.occupancy,
            lighting=self.lighting,
        )
        new_space.ventilation.load = self.ventilation.load + other.ventilation.load
        return new_space
