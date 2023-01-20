# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Program Class for organizing Occupancy Data (People)"""

from __future__ import annotations
from typing import ClassVar, Any
from dataclasses import dataclass

from PHX.model.loads.occupancy import PhxLoadOccupancy
from PHX.model.schedules.occupancy import PhxScheduleOccupancy


@dataclass
class PhxProgramOccupancy:
    """A PHX Program for the Occupancy (People) with a load and schedule."""

    display_name: str = "Unnamed_Occupancy_Program"
    load: PhxLoadOccupancy = PhxLoadOccupancy()
    schedule: PhxScheduleOccupancy = PhxScheduleOccupancy()
