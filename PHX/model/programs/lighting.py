# -*- Python Version: 3.10 -*-

"""PHX Program Class for organizing Lighting Data."""

from __future__ import annotations

from dataclasses import dataclass, field

from PHX.model.loads.lighting import PhxLoadLighting
from PHX.model.schedules.lighting import PhxScheduleLighting


@dataclass
class PhxProgramLighting:
    """Lighting program pairing an installed power density load with a utilization schedule.

    Combines a PhxLoadLighting (W/m2) with a PhxScheduleLighting (operating hours
    and utilization factors) to define the complete lighting profile for a PHX
    zone or space.

    Attributes:
        display_name (str): Human-readable program name. Default: "Unnamed_Lighting_Program".
        load (PhxLoadLighting): The lighting power density load. Default: empty PhxLoadLighting.
        schedule (PhxScheduleLighting): The lighting utilization schedule.
            Default: empty PhxScheduleLighting.
    """

    display_name: str = "Unnamed_Lighting_Program"
    load: PhxLoadLighting = field(default_factory=PhxLoadLighting)
    schedule: PhxScheduleLighting = field(default_factory=PhxScheduleLighting)
