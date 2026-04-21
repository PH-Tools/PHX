# -*- Python Version: 3.10 -*-

"""PHX Lighting Utilization Schedule."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class PhxScheduleLighting:
    """Lighting utilization schedule defining daily operating hours and annual utilization.

    Defines when and how intensely lighting is used via a daily operating period
    (start/end hour) and an annual utilization pattern (days per year and a
    relative utilization factor within those days).

    Attributes:
        id_num (int): Auto-incremented instance counter, assigned in __post_init__.
        identifier (uuid.UUID | str): Unique identifier. Default: auto-generated UUID4.
        display_name (str): Human-readable schedule name.
            Default: "__unnamed_lighting_schedule__".
        start_hour (float): Daily operating period start hour (0-24). Default: 0.0.
        end_hour (float): Daily operating period end hour (0-24). Default: 1.0.
        annual_utilization_days (float): Number of lit days per year. Default: 0.0.
        relative_utilization_factor (float): Fractional utilization within the operating
            period, relative to the annual_utilization_days. Default: 0.0.
    """

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    identifier: uuid.UUID | str = field(default_factory=uuid.uuid4)
    display_name = "__unnamed_lighting_schedule__"
    start_hour: float = 0.0
    end_hour: float = 1.0
    annual_utilization_days: float = 0.0
    relative_utilization_factor: float = 0.0  # Relative to the 'annual_utilization_days'

    @classmethod
    def from_annual_operating_hours(cls, _annual_operating_hours: float) -> PhxScheduleLighting:
        """Create a lighting schedule from total annual operating hours.

        Distributes the daily hours symmetrically around noon and sets
        365 annual utilization days at full utilization.

        Arguments:
        ----------
            * _annual_operating_hours (float): Total lighting operating hours per year.

        Returns:
        --------
            * PhxScheduleLighting: A new schedule configured for the given annual hours.
        """
        new_schedule = cls()
        hours_per_day = _annual_operating_hours / 365
        new_schedule.start_hour = 12 - (hours_per_day / 2)
        new_schedule.end_hour = 12 + (hours_per_day / 2)
        new_schedule.annual_utilization_days = 365
        new_schedule.relative_utilization_factor = 1.0
        return new_schedule

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    def __eq__(self, other: PhxScheduleLighting) -> bool:
        TOLERANCE = 0.001
        if self.display_name != other.display_name:
            return False
        if abs(self.start_hour - other.start_hour) > TOLERANCE:
            return False
        if abs(self.end_hour - other.end_hour) > TOLERANCE:
            return False
        if abs(self.annual_utilization_days - other.annual_utilization_days) > TOLERANCE:
            return False
        if abs(self.relative_utilization_factor - other.relative_utilization_factor) > TOLERANCE:
            return False
        return self.unique_key == other.unique_key

    @property
    def annual_utilization_factor(self) -> float:
        """Return the annual Utilization Rate (0-1) relative to the entire year (8760 hours)"""

        operating_period_utilization_factor = self.annual_operating_hours / 8760  # Hrs / year

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
        return f"{self.start_hour :.3f}_{self.end_hour :.3f}_{self.annual_utilization_days :.3f}_{self.annual_utilization_factor :.3f}_"

    @property
    def full_load_lighting_hours(self) -> float:
        """Return the annual full-load lighting hours, clamped to 0-8760."""
        return max(0, min(8760, self.annual_operating_hours))
