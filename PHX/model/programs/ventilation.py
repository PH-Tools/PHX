# -*- Python Version: 3.10 -*-

"""PHX Program Class for organizing Fresh-Air Ventilation Data."""

from __future__ import annotations

from dataclasses import dataclass, field

from PHX.model.loads import ventilation as vent_loads
from PHX.model.schedules import ventilation as vent_schedules


@dataclass
class PhxProgramVentilation:
    """Ventilation program pairing fresh-air airflow rates with a utilization schedule.

    Combines a PhxLoadVentilation (supply/extract/transfer airflow rates) with a
    PhxScheduleVentilation (operating periods at various speed levels) to define
    the complete ventilation profile for a PHX zone or space.

    Attributes:
        display_name (str): Human-readable program name. Default: "Unnamed_Ventilation_Program".
        load (PhxLoadVentilation): The ventilation airflow rate load.
            Default: empty PhxLoadVentilation.
        schedule (PhxScheduleVentilation): The ventilation utilization schedule with
            operating periods. Default: empty PhxScheduleVentilation.
    """

    display_name: str = "Unnamed_Ventilation_Program"
    load: vent_loads.PhxLoadVentilation = field(default_factory=vent_loads.PhxLoadVentilation)
    schedule: vent_schedules.PhxScheduleVentilation = field(default_factory=vent_schedules.PhxScheduleVentilation)

    @property
    def has_ventilation_airflow(self) -> bool:
        """Return True if the load has any non-zero ventilation airflow."""
        return self.load.total_airflow > 0.0
