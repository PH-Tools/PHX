# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Occupancy (People) Utilization Schedule."""

from __future__ import annotations
from typing import ClassVar, Any, Union
from dataclasses import dataclass, field
import uuid


@dataclass
class PhxScheduleOccupancy:
    """A PHX Schedule for the Occupancy (People)."""

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    identifier: Union[uuid.UUID, str] = field(default_factory=uuid.uuid4)
    display_name = "__unnamed_occupancy_schedule__"
    start_hour: float = 0.0
    end_hour: float = 1.0
    annual_utilization_days: float = 0.0
    relative_utilization_factor: float = 0.0  # Relative to the 'annual_utilization_days'

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def annual_utilization_factor(self) -> float:
        """Return the annual Utilization Rate (0-1) relative to the entire year (8760 hours)"""

        operating_period_utilization_factor = (
            self.annual_operating_hours / 8760
        )  # Hrs / year

        return operating_period_utilization_factor * self.relative_utilization_factor

    @annual_utilization_factor.setter
    def annual_utilization_factor(self, _relative_utilization_factor: float):
        """Set the Relative Utilization Factor."""

        if _relative_utilization_factor is None:
            return

        # -- Re-Set the relative utilization factor to match
        self.start_hour = 0
        self.end_hour = 24
        self.annual_utilization_days = 365
        self.relative_utilization_factor = _relative_utilization_factor

    @property
    def daily_operating_hours(self) -> float:
        """Return the total Daily Operating Hours (end-hour - start-hour)."""
        return abs(self.end_hour - self.start_hour)

    @property
    def annual_operating_hours(self):
        """Return the total Annual Operating Hours (daily-hours * annual-util-days)."""
        return self.annual_utilization_days * self.daily_operating_hours

    @property
    def unique_key(self):
        """Return a key unique to this 'type' (collection of values) of pattern"""
        return "{}_{}_{}_{}_".format(
            self.start_hour,
            self.end_hour,
            self.annual_utilization_days,
            self.annual_utilization_factor,
        )
