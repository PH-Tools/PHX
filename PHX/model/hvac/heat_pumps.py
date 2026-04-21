# -*- Python Version: 3.10 -*-

"""PHX heat pump device classes for heating and cooling.

Includes annual-COP, monthly-rated, hot-water-only, and combined heat pump
types, each with associated parameter dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from PHX.model.enums.hvac import DeviceType, HeatPumpType, SystemType
from PHX.model.hvac import _base
from PHX.model.hvac.cooling_params import PhxCoolingParams

# -----------------------------------------------------------------------------
# Base


@dataclass
class PhxHeatPumpDevice(_base.PhxMechanicalDevice):
    """Base class for all PHX heat pump devices (heating and/or cooling).

    Attributes:
        params_cooling (PhxCoolingParams): Cooling-mode parameters (ventilation, recirculation,
            dehumidification, panel).
    """

    params_cooling: PhxCoolingParams = field(default_factory=PhxCoolingParams)

    def __post_init__(self) -> None:
        super().__post_init__()


# -----------------------------------------------------------------------------
# Params


@dataclass
class PhxHeatPumpAnnualParams(_base.PhxMechanicalDeviceParams):
    """Parameters for a heat pump characterized by a single annual COP.

    Attributes:
        hp_type (HeatPumpType): Always HeatPumpType.ANNUAL.
        annual_COP (float | None): Annual coefficient of performance (W/W). Default: None.
        total_system_perf_ratio (float | None): Total system performance ratio. Default: None.
    """

    hp_type: HeatPumpType = field(init=False, default=HeatPumpType.ANNUAL)
    annual_COP: float | None = None
    total_system_perf_ratio: float | None = None


@dataclass
class PhxHeatPumpMonthlyParams(_base.PhxMechanicalDeviceParams):
    """Parameters for a heat pump characterized by two rated COP/temperature points.

    COP_1/ambient_temp_1 and COP_2/ambient_temp_2 define the two operating
    points from which monthly performance is interpolated.

    Attributes:
        hp_type (HeatPumpType): Always HeatPumpType.RATED_MONTHLY.
        COP_1 (float | None): COP at the first rated ambient temperature. Default: None.
        COP_2 (float | None): COP at the second rated ambient temperature. Default: None.
        ambient_temp_1 (float | None): First rated ambient temperature (C). Default: None.
        ambient_temp_2 (float | None): Second rated ambient temperature (C). Default: None.
    """

    hp_type: HeatPumpType = field(init=False, default=HeatPumpType.RATED_MONTHLY)
    _COP_1: float | None = None
    _COP_2: float | None = None
    _ambient_temp_1: float | None = None
    _ambient_temp_2: float | None = None

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
    def COP_1(self) -> float | None:
        return self._COP_1

    @COP_1.setter
    def COP_1(self, value: float | None) -> None:
        if value is not None:
            self._COP_1 = value

    @property
    def COP_2(self) -> float | None:
        return self._COP_2

    @COP_2.setter
    def COP_2(self, value: float | None) -> None:
        if value is not None:
            self._COP_2 = value

    @property
    def ambient_temp_1(self) -> float | None:
        return self._ambient_temp_1

    @ambient_temp_1.setter
    def ambient_temp_1(self, value: float | None) -> None:
        if value is not None:
            self._ambient_temp_1 = value

    @property
    def ambient_temp_2(self) -> float | None:
        return self._ambient_temp_2

    @ambient_temp_2.setter
    def ambient_temp_2(self, value: float | None) -> None:
        if value is not None:
            self._ambient_temp_2 = value


@dataclass
class PhxHeatPumpHotWaterParams(_base.PhxMechanicalDeviceParams):
    """Parameters for a dedicated DHW heat pump (heat-pump water heater).

    Attributes:
        hp_type (HeatPumpType): Always HeatPumpType.HOT_WATER.
        annual_COP (float | None): Annual COP for DHW production (W/W). Default: None.
        total_system_perf_ratio (float | None): Total system performance ratio. Default: None.
        annual_energy_factor (float | None): Annual energy factor (EF). Default: None.
    """

    hp_type: HeatPumpType = field(init=False, default=HeatPumpType.HOT_WATER)
    annual_COP: float | None = None
    total_system_perf_ratio: float | None = None
    annual_energy_factor: float | None = None


@dataclass
class PhxHeatPumpCombinedParams(_base.PhxMechanicalDeviceParams):
    """Parameters for a combined (space heating + DHW) heat pump.

    Attributes:
        hp_type (HeatPumpType): Always HeatPumpType.COMBINED.
    """

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
    """A heat pump characterized by a single annual COP value.

    Attributes:
        system_type (SystemType): Always SystemType.HEAT_PUMP.
        device_type (DeviceType): Always DeviceType.HEAT_PUMP.
        params (PhxHeatPumpAnnualParams): Annual COP parameters.
        params_cooling (PhxCoolingParams): Cooling-mode parameters.
    """

    system_type: SystemType = field(init=False, default=SystemType.HEAT_PUMP)
    device_type: DeviceType = field(init=False, default=DeviceType.HEAT_PUMP)
    params: PhxHeatPumpAnnualParams = field(default_factory=PhxHeatPumpAnnualParams)
    params_cooling: PhxCoolingParams = field(default_factory=PhxCoolingParams)


@dataclass
class PhxHeatPumpMonthly(PhxHeatPumpDevice):
    """A heat pump characterized by two rated COP/temperature operating points.

    Attributes:
        system_type (SystemType): Always SystemType.HEAT_PUMP.
        device_type (DeviceType): Always DeviceType.HEAT_PUMP.
        params (PhxHeatPumpMonthlyParams): Monthly-rated COP parameters.
        params_cooling (PhxCoolingParams): Cooling-mode parameters.
    """

    system_type: SystemType = field(init=False, default=SystemType.HEAT_PUMP)
    device_type: DeviceType = field(init=False, default=DeviceType.HEAT_PUMP)
    params: PhxHeatPumpMonthlyParams = field(default_factory=PhxHeatPumpMonthlyParams)
    params_cooling: PhxCoolingParams = field(default_factory=PhxCoolingParams)


@dataclass
class PhxHeatPumpCombined(PhxHeatPumpDevice):
    """A combined heat pump serving both space heating and DHW.

    Attributes:
        system_type (SystemType): Always SystemType.HEAT_PUMP.
        device_type (DeviceType): Always DeviceType.HEAT_PUMP.
        params (PhxHeatPumpCombinedParams): Combined heat pump parameters.
        params_cooling (PhxCoolingParams): Cooling-mode parameters.
    """

    system_type: SystemType = field(init=False, default=SystemType.HEAT_PUMP)
    device_type: DeviceType = field(init=False, default=DeviceType.HEAT_PUMP)
    params: PhxHeatPumpCombinedParams = field(default_factory=PhxHeatPumpCombinedParams)
    params_cooling: PhxCoolingParams = field(default_factory=PhxCoolingParams)


@dataclass
class PhxHeatPumpHotWater(PhxHeatPumpDevice):
    """A dedicated DHW heat pump (heat-pump water heater).

    Attributes:
        system_type (SystemType): Always SystemType.HEAT_PUMP.
        device_type (DeviceType): Always DeviceType.HEAT_PUMP.
        params (PhxHeatPumpHotWaterParams): DHW heat pump parameters.
        params_cooling (PhxCoolingParams): Cooling-mode parameters.
    """

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
