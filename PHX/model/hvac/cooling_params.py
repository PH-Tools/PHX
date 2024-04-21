# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Mechanical Cooling Devices and Parameters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from PHX.model.hvac import _base

# -- Cooling Parameter Types --------------------------------------------------


@dataclass
class PhxCoolingVentilationParams(_base.PhxMechanicalDeviceParams):
    used: bool = False
    single_speed: bool = False
    min_coil_temp: float = 12  # C
    capacity: float = 10  # kW
    annual_COP: float = 4  # W/W

    @property
    def total_system_perf_ratio(self):
        return 1 / self.annual_COP

    def __add__(self, other: PhxCoolingVentilationParams) -> PhxCoolingVentilationParams:
        if not other:
            return self

        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))
        new_obj.used = any([self.used, other.used])
        new_obj.single_speed = any([self.single_speed, other.single_speed])
        new_obj.min_coil_temp = (self.min_coil_temp + other.min_coil_temp) / 2
        new_obj.capacity = (self.capacity + other.capacity) / 2
        new_obj.annual_COP = (self.annual_COP + other.annual_COP) / 2
        return new_obj


@dataclass
class PhxCoolingRecirculationParams(_base.PhxMechanicalDeviceParams):
    used: bool = False
    single_speed: bool = False
    min_coil_temp: float = 12  # C
    capacity: float = 10  # kW
    annual_COP: float = 4  # W/W
    flow_rate_m3_hr: float = 100
    flow_rate_variable: bool = True

    @property
    def total_system_perf_ratio(self):
        return 1 / self.annual_COP

    def __add__(self, other: PhxCoolingRecirculationParams) -> PhxCoolingRecirculationParams:
        if not other:
            return self

        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))
        new_obj.used = any([self.used, other.used])
        new_obj.single_speed = any([self.single_speed, other.single_speed])
        new_obj.min_coil_temp = (self.min_coil_temp + other.min_coil_temp) / 2
        new_obj.flow_rate_m3_hr = (self.flow_rate_m3_hr + other.flow_rate_m3_hr) / 2
        new_obj.capacity = (self.capacity + other.capacity) / 2
        new_obj.flow_rate_variable = any([self.flow_rate_variable, other.flow_rate_variable])
        new_obj.annual_COP = (self.annual_COP + other.annual_COP) / 2
        return new_obj


@dataclass
class PhxCoolingDehumidificationParams(_base.PhxMechanicalDeviceParams):
    used: bool = False
    annual_COP: float = 4  # W/W
    useful_heat_loss: bool = False

    @property
    def total_system_perf_ratio(self):
        return 1 / self.annual_COP

    def __add__(self, other: PhxCoolingDehumidificationParams) -> PhxCoolingDehumidificationParams:
        if not other:
            return self

        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))
        new_obj.used = any([self.used, other.used])
        new_obj.useful_heat_loss = any([self.useful_heat_loss, other.useful_heat_loss])
        new_obj.annual_COP = (self.annual_COP + other.annual_COP) / 2
        return new_obj


@dataclass
class PhxCoolingPanelParams(_base.PhxMechanicalDeviceParams):
    used: bool = False
    annual_COP: float = 4  # W/W

    @property
    def total_system_perf_ratio(self):
        return 1 / self.annual_COP

    def __add__(self, other: PhxCoolingPanelParams) -> PhxCoolingPanelParams:
        if not other:
            return self

        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))
        new_obj.used = any([self.used, other.used])
        new_obj.annual_COP = (self.annual_COP + other.annual_COP) / 2
        return new_obj


AnyPhxCoolingParamsType = Union[
    PhxCoolingVentilationParams,
    PhxCoolingRecirculationParams,
    PhxCoolingDehumidificationParams,
    PhxCoolingPanelParams,
]

# -- Param Collection ---------------------------------------------------------


@dataclass
class PhxCoolingParams:
    ventilation: PhxCoolingVentilationParams = field(default_factory=PhxCoolingVentilationParams)
    recirculation: PhxCoolingRecirculationParams = field(default_factory=PhxCoolingRecirculationParams)
    dehumidification: PhxCoolingDehumidificationParams = field(default_factory=PhxCoolingDehumidificationParams)
    panel: PhxCoolingPanelParams = field(default_factory=PhxCoolingPanelParams)

    def __bool__(self) -> bool:
        return any([self.ventilation, self.recirculation, self.dehumidification, self.panel])
