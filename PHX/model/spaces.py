# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Space (Room) Class"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from PHX.model.programs.lighting import PhxProgramLighting
from PHX.model.programs.occupancy import PhxProgramOccupancy
from PHX.model.programs.ventilation import PhxProgramVentilation


def area_weighted_clear_height(space_a: PhxSpace, space_b: PhxSpace) -> float:
    """Returns the area-weighted clear-height of two spaces."""
    try:
        weighted_height_a = space_a.clear_height * space_a.floor_area
        weighted_height_b = space_b.clear_height * space_b.floor_area
        total_floor_area = space_a.floor_area + space_b.floor_area
        return (weighted_height_a + weighted_height_b) / total_floor_area
    except ZeroDivisionError:
        return 0.0


def spaces_are_not_addable(space_a: PhxSpace, space_v: PhxSpace) -> bool:
    """Returns True if space_a can safely be added to space_b."""
    return any(
        (
            space_a.wufi_type != space_v.wufi_type,
            space_a.vent_unit_id_num != space_v.vent_unit_id_num,
        )
    )


@dataclass
class PhxSpace:
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
