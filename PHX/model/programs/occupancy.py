# -*- Python Version: 3.10 -*-

"""PHX Program Class for organizing Occupancy Data (People)"""

from __future__ import annotations

from dataclasses import dataclass, field

from PHX.model.loads.occupancy import PhxLoadOccupancy
from PHX.model.schedules.occupancy import PhxScheduleOccupancy


@dataclass
class PhxProgramOccupancy:
    """Occupancy program pairing a people-density load with a utilization schedule.

    Combines a PhxLoadOccupancy (people per m2) with a PhxScheduleOccupancy
    (operating hours and utilization factors) to define the complete occupancy
    profile for a PHX zone or space.

    Attributes:
        display_name (str): Human-readable program name. Default: "Unnamed_Occupancy_Program".
        load (PhxLoadOccupancy): The occupancy density load. Default: empty PhxLoadOccupancy.
        schedule (PhxScheduleOccupancy): The occupancy utilization schedule.
            Default: empty PhxScheduleOccupancy.
    """

    display_name: str = "Unnamed_Occupancy_Program"
    load: PhxLoadOccupancy = field(default_factory=PhxLoadOccupancy)
    schedule: PhxScheduleOccupancy = field(default_factory=PhxScheduleOccupancy)
