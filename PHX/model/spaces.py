# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Space (Room) Class"""

from __future__ import annotations
from typing import ClassVar
from dataclasses import dataclass, field

from PHX.model.programs.occupancy import PhxProgramOccupancy
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
    occupancy: PhxProgramOccupancy = field(default_factory=PhxProgramOccupancy)
    lighting = None
    electric_equipment = None

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count
