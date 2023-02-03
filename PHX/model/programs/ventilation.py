# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Program Class for organizing Fresh-Air Ventilation Data."""

from __future__ import annotations
from typing import ClassVar
from dataclasses import dataclass, field

from PHX.model.loads.ventilation import PhxLoadVentilation
from PHX.model.schedules.ventilation import PhxScheduleVentilation


@dataclass
class PhxProgramVentilation:
    """A PHX Program for the Fresh-Air Ventilation with a load and schedule."""

    display_name: str = "Unnamed_Ventilation_Program"
    load: PhxLoadVentilation = field(default_factory=PhxLoadVentilation)
    schedule: PhxScheduleVentilation = field(default_factory=PhxScheduleVentilation)
