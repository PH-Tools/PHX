# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Program Class for organizing Lighting Data."""

from __future__ import annotations

from dataclasses import dataclass, field

from PHX.model.loads.lighting import PhxLoadLighting
from PHX.model.schedules.lighting import PhxScheduleLighting


@dataclass
class PhxProgramLighting:
    """A PHX Program for the Lighting with a load and schedule."""

    display_name: str = "Unnamed_Lighting_Program"
    load: PhxLoadLighting = field(default_factory=PhxLoadLighting)
    schedule: PhxScheduleLighting = field(default_factory=PhxScheduleLighting)
