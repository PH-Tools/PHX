# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Program Class for organizing Fresh-Air Ventilation Data."""

from __future__ import annotations

from dataclasses import dataclass, field

from PHX.model.loads import ventilation as vent_loads
from PHX.model.schedules import ventilation as vent_schedules


@dataclass
class PhxProgramVentilation:
    """A PHX Program for the Fresh-Air Ventilation with a load and schedule."""

    display_name: str = "Unnamed_Ventilation_Program"
    load: vent_loads.PhxLoadVentilation = field(default_factory=vent_loads.PhxLoadVentilation)
    schedule: vent_schedules.PhxScheduleVentilation = field(default_factory=vent_schedules.PhxScheduleVentilation)

    @property
    def has_ventilation_airflow(self) -> bool:
        """Returns True if the load has any amount of ventilation airflow."""
        return self.load.total_airflow > 0.0
