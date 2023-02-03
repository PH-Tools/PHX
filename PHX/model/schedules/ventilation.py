# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Fresh-Air Ventilation Utilization Schedule."""

from __future__ import annotations
from typing import ClassVar, Any, Union
from dataclasses import dataclass, field
import uuid


@dataclass
class Vent_OperatingPeriod:
    period_operating_hours: float = 0.0  # hours/period
    period_operation_speed: float = 0.0  # % of peak design airflow


@dataclass
class Vent_UtilPeriods:
    high: Vent_OperatingPeriod = field(default_factory=Vent_OperatingPeriod)
    standard: Vent_OperatingPeriod = field(default_factory=Vent_OperatingPeriod)
    basic: Vent_OperatingPeriod = field(default_factory=Vent_OperatingPeriod)
    minimum: Vent_OperatingPeriod = field(default_factory=Vent_OperatingPeriod)


@dataclass
class PhxScheduleVentilation:
    """A PHX Schedule for the Ventilation."""

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    name: str = "__unnamed_vent_schedule__"
    identifier: Union[uuid.UUID, str] = field(default_factory=uuid.uuid4)
    operating_hours: float = 24.0
    operating_days: float = 7.0
    operating_weeks: float = 52.0
    operating_periods: Vent_UtilPeriods = field(default_factory=Vent_UtilPeriods)
    holiday_days: float = 0.0

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    def force_max_utilization_hours(
        self, _max_hours: float = 24.0, _tol: int = 2
    ) -> None:
        """Ensure that the total utilization hours never exceed target (default=24).
        Will adjust the minimum daily_op_sched as needed.
        """

        b = round(self.operating_periods.standard.period_operating_hours, _tol)
        c = round(self.operating_periods.basic.period_operating_hours, _tol)
        a = round(self.operating_periods.minimum.period_operating_hours, _tol)
        total = a + b + c
        remainder = round(_max_hours - total, _tol)
        self.operating_periods.high.period_operating_hours = remainder

    def __hash__(self):
        return hash(self.identifier)
