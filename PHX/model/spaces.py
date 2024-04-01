# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Space (Room) Class"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from PHX.model.programs import occupancy as occupancy_prog
from PHX.model.programs.lighting import PhxProgramLighting
from PHX.model.programs.ventilation import PhxProgramVentilation


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

    # -- Programs
    ventilation: PhxProgramVentilation = field(default_factory=PhxProgramVentilation)
    occupancy: occupancy_prog.PhxProgramOccupancy = field(default_factory=occupancy_prog.PhxProgramOccupancy)
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
