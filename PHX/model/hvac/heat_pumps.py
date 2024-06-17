# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Mechanical Heat-Pump (Heating + Cooling) Devices."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from PHX.model.enums.hvac import DeviceType, HeatPumpType, SystemType
from PHX.model.hvac import _base
from PHX.model.hvac.cooling_params import PhxCoolingParams

# -----------------------------------------------------------------------------
# Base


@dataclass
class PhxHeatPumpDevice(_base.PhxMechanicalDevice):
    params_cooling: PhxCoolingParams = field(default_factory=PhxCoolingParams)

    def __post_init__(self) -> None:
        super().__post_init__()


# -----------------------------------------------------------------------------
# Params


@dataclass
class PhxHeatPumpAnnualParams(_base.PhxMechanicalDeviceParams):
    hp_type: HeatPumpType = field(init=False, default=HeatPumpType.ANNUAL)
    annual_COP: Optional[float] = None
    total_system_perf_ratio: Optional[float] = None


@dataclass
class PhxHeatPumpMonthlyParams(_base.PhxMechanicalDeviceParams):
    hp_type: HeatPumpType = field(init=False, default=HeatPumpType.RATED_MONTHLY)
    _COP_1: Optional[float] = None
    _COP_2: Optional[float] = None
    _ambient_temp_1: Optional[float] = None
    _ambient_temp_2: Optional[float] = None

    @property
    def monthly_COPS(self):
        return None

    @monthly_COPS.setter
    def monthly_COPS(self, _in):
        if not _in:
            return

        self.COP_1 = _in[0]
        try:
            self.COP_2 = _in[1]
        except IndexError:
            self.COP_2 = _in[0]

    @property
    def monthly_temps(self):
        return None

    @monthly_temps.setter
    def monthly_temps(self, _in):
        if not _in:
            return

        self.ambient_temp_1 = _in[0]
        try:
            self.ambient_temp_2 = _in[1]
        except IndexError:
            self.ambient_temp_2 = _in[0]

    @property
    def COP_1(self) -> Optional[float]:
        return self._COP_1

    @COP_1.setter
    def COP_1(self, value: Optional[float]) -> None:
        if value is not None:
            self._COP_1 = value

    @property
    def COP_2(self) -> Optional[float]:
        return self._COP_2

    @COP_2.setter
    def COP_2(self, value: Optional[float]) -> None:
        if value is not None:
            self._COP_2 = value

    @property
    def ambient_temp_1(self) -> Optional[float]:
        return self._ambient_temp_1

    @ambient_temp_1.setter
    def ambient_temp_1(self, value: Optional[float]) -> None:
        if value is not None:
            self._ambient_temp_1 = value

    @property
    def ambient_temp_2(self) -> Optional[float]:
        return self._ambient_temp_2

    @ambient_temp_2.setter
    def ambient_temp_2(self, value: Optional[float]) -> None:
        if value is not None:
            self._ambient_temp_2 = value


@dataclass
class PhxHeatPumpHotWaterParams(_base.PhxMechanicalDeviceParams):
    hp_type: HeatPumpType = field(init=False, default=HeatPumpType.HOT_WATER)
    annual_COP: Optional[float] = None
    total_system_perf_ratio: Optional[float] = None
    annual_energy_factor: Optional[float] = None


@dataclass
class PhxHeatPumpCombinedParams(_base.PhxMechanicalDeviceParams):
    hp_type: HeatPumpType = field(init=False, default=HeatPumpType.COMBINED)


AnyHeatPumpParams = Union[
    PhxHeatPumpAnnualParams,
    PhxHeatPumpMonthlyParams,
    PhxHeatPumpHotWaterParams,
    PhxHeatPumpCombinedParams,
]


# -----------------------------------------------------------------------------
# Equipment


@dataclass
class PhxHeatPumpAnnual(PhxHeatPumpDevice):
    system_type: SystemType = field(init=False, default=SystemType.HEAT_PUMP)
    device_type: DeviceType = field(init=False, default=DeviceType.HEAT_PUMP)
    params: PhxHeatPumpAnnualParams = field(default_factory=PhxHeatPumpAnnualParams)
    params_cooling: PhxCoolingParams = field(default_factory=PhxCoolingParams)


@dataclass
class PhxHeatPumpMonthly(PhxHeatPumpDevice):
    system_type: SystemType = field(init=False, default=SystemType.HEAT_PUMP)
    device_type: DeviceType = field(init=False, default=DeviceType.HEAT_PUMP)
    params: PhxHeatPumpMonthlyParams = field(default_factory=PhxHeatPumpMonthlyParams)
    params_cooling: PhxCoolingParams = field(default_factory=PhxCoolingParams)


@dataclass
class PhxHeatPumpCombined(PhxHeatPumpDevice):
    system_type: SystemType = field(init=False, default=SystemType.HEAT_PUMP)
    device_type: DeviceType = field(init=False, default=DeviceType.HEAT_PUMP)
    params: PhxHeatPumpCombinedParams = field(default_factory=PhxHeatPumpCombinedParams)
    params_cooling: PhxCoolingParams = field(default_factory=PhxCoolingParams)


@dataclass
class PhxHeatPumpHotWater(PhxHeatPumpDevice):
    system_type: SystemType = field(init=False, default=SystemType.HEAT_PUMP)
    device_type: DeviceType = field(init=False, default=DeviceType.HEAT_PUMP)
    params: PhxHeatPumpHotWaterParams = field(default_factory=PhxHeatPumpHotWaterParams)
    params_cooling: PhxCoolingParams = field(default_factory=PhxCoolingParams)


AnyPhxHeatPump = Union[
    PhxHeatPumpAnnual,
    PhxHeatPumpMonthly,
    PhxHeatPumpHotWater,
    PhxHeatPumpCombined,
]
