# -*- Python Version: 3.10 -*-

"""PHX mechanical heating device classes.

Includes electric resistance, fossil-fuel boilers, wood boilers, and
district heat devices used for space heating and/or DHW.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from PHX.model.enums.hvac import DeviceType, PhxFuelType, SystemType
from PHX.model.hvac import _base


@dataclass
class PhxHeatingDevice(_base.PhxMechanicalDevice):
    """Base class for all PHX heating devices (electric, boiler, district heat)."""

    def __post_init__(self):
        super().__post_init__()


# -----------------------------------------------------------------------------
# Electric


@dataclass
class PhxHeaterElectricParams(_base.PhxMechanicalDeviceParams):
    """Parameters for an electric resistance heater (no additional fields beyond base)."""

    pass


@dataclass
class PhxHeaterElectric(PhxHeatingDevice):
    """An electric resistance heater for space heating and/or DHW.

    Attributes:
        system_type (SystemType): Always SystemType.ELECTRIC.
        device_type (DeviceType): Always DeviceType.ELECTRIC.
        params (PhxHeaterElectricParams): Electric heater parameters.
    """

    system_type: SystemType = field(init=False, default=SystemType.ELECTRIC)
    device_type: DeviceType = field(init=False, default=DeviceType.ELECTRIC)
    params: PhxHeaterElectricParams = field(default_factory=PhxHeaterElectricParams)


# -----------------------------------------------------------------------------
# Boilers


@dataclass
class PhxHeaterBoilerFossilParams(_base.PhxMechanicalDeviceParams):
    """Performance parameters for a fossil-fuel boiler (gas, oil, propane).

    Efficiencies and return temperatures follow PHPP / WUFI conventions for
    condensing and non-condensing boiler characterization.

    Attributes:
        fuel (PhxFuelType): Fuel type (natural gas, oil, etc.). Default: NATURAL_GAS.
        condensing (bool): True if the boiler is a condensing unit. Default: True.
        in_conditioned_space (bool): True if located inside the thermal envelope. Default: True.
        effic_at_30_percent_load (float): Efficiency at 30% part load. Default: 0.98.
        effic_at_nominal_load (float): Efficiency at nominal (full) load. Default: 0.94.
        avg_rtrn_temp_at_30_percent_load (float): Average return water temp at 30% load (C).
            Default: 30.
        avg_temp_at_70C_55C (float): Average boiler temp for 70/55 C flow/return (C). Default: 41.
        avg_temp_at_55C_45C (float): Average boiler temp for 55/45 C flow/return (C). Default: 35.
        avg_temp_at_32C_28C (float): Average boiler temp for 32/28 C flow/return (C). Default: 24.
        standby_loss_at_70C (float | None): Standby heat loss at 70 C (W). Default: None.
        rated_capacity (float): Rated heating capacity (kW). Default: 10.0.
    """

    _fuel: PhxFuelType = PhxFuelType.NATURAL_GAS
    _condensing: bool = True
    _in_conditioned_space: bool = True
    _effic_at_30_percent_load: float = 0.98
    _effic_at_nominal_load: float = 0.94
    _avg_rtrn_temp_at_30_percent_load: float = 30
    _avg_temp_at_70C_55C: float = 41
    _avg_temp_at_55C_45C: float = 35
    _avg_temp_at_32C_28C: float = 24
    _standby_loss_at_70C: float | None = None
    _rated_capacity: float = 10.0  # kW

    @property
    def fuel(self):
        return self._fuel

    @fuel.setter
    def fuel(self, _in):
        try:
            self._fuel = PhxFuelType[_in]
        except KeyError:
            self._fuel = PhxFuelType(_in)

    @property
    def condensing(self) -> bool:
        return self._condensing

    @condensing.setter
    def condensing(self, value: bool | None) -> None:
        if value is not None:
            self._condensing = value

    @property
    def in_conditioned_space(self) -> bool:
        return self._in_conditioned_space

    @in_conditioned_space.setter
    def in_conditioned_space(self, value: bool | None) -> None:
        if value is not None:
            self._in_conditioned_space = value

    @property
    def effic_at_30_percent_load(self) -> float:
        return self._effic_at_30_percent_load

    @effic_at_30_percent_load.setter
    def effic_at_30_percent_load(self, value: float | None) -> None:
        if value is not None:
            self._effic_at_30_percent_load = value

    @property
    def effic_at_nominal_load(self) -> float:
        return self._effic_at_nominal_load

    @effic_at_nominal_load.setter
    def effic_at_nominal_load(self, value: float | None) -> None:
        if value is not None:
            self._effic_at_nominal_load = value

    @property
    def avg_rtrn_temp_at_30_percent_load(self) -> float:
        return self._avg_rtrn_temp_at_30_percent_load

    @avg_rtrn_temp_at_30_percent_load.setter
    def avg_rtrn_temp_at_30_percent_load(self, value: float | None) -> None:
        if value is not None:
            self._avg_rtrn_temp_at_30_percent_load = value

    @property
    def avg_temp_at_70C_55C(self) -> float:
        return self._avg_temp_at_70C_55C

    @avg_temp_at_70C_55C.setter
    def avg_temp_at_70C_55C(self, value: float | None) -> None:
        if value is not None:
            self._avg_temp_at_70C_55C = value

    @property
    def avg_temp_at_55C_45C(self) -> float:
        return self._avg_temp_at_55C_45C

    @avg_temp_at_55C_45C.setter
    def avg_temp_at_55C_45C(self, value: float | None) -> None:
        if value is not None:
            self._avg_temp_at_55C_45C = value

    @property
    def avg_temp_at_32C_28C(self) -> float:
        return self._avg_temp_at_32C_28C

    @avg_temp_at_32C_28C.setter
    def avg_temp_at_32C_28C(self, value: float | None) -> None:
        if value is not None:
            self._avg_temp_at_32C_28C = value

    @property
    def standby_loss_at_70C(self) -> float | None:
        return self._standby_loss_at_70C

    @standby_loss_at_70C.setter
    def standby_loss_at_70C(self, value: float | None) -> None:
        if value is not None:
            self._standby_loss_at_70C = value

    @property
    def rated_capacity(self) -> float:
        return self._rated_capacity

    @rated_capacity.setter
    def rated_capacity(self, value: float | None) -> None:
        if value is not None:
            self._rated_capacity = value


@dataclass
class PhxHeaterBoilerWoodParams(_base.PhxMechanicalDeviceParams):
    """Performance parameters for a wood-fired boiler (log, pellet).

    Attributes:
        fuel (PhxFuelType): Wood fuel type (log, pellet). Default: WOOD_LOG.
        effic_in_basic_cycle (float): Efficiency during basic burn cycle. Default: 0.6.
        effic_in_const_operation (float): Efficiency during constant operation. Default: 0.7.
        avg_frac_heat_output (float): Average fraction of rated heat output. Default: 0.4.
        temp_diff_on_off (float): Temperature difference for on/off cycling (K). Default: 30.0.
        rated_capacity (float): Rated heating capacity (kW). Default: 15.0.
        demand_basic_cycle (float): Energy demand per basic cycle (kWh). Default: 1.0.
        power_stationary_run (float): Power consumption during stationary run (W). Default: 1.0.
        power_standard_run (float | None): Power consumption during standard run (W). Default: None.
        no_transport_pellets (bool | None): True if no pellet transport mechanism. Default: None.
        only_control (bool | None): True if device is control-only. Default: None.
        area_mech_room (float | None): Mechanical room area (m2). Default: None.
    """

    _fuel: PhxFuelType = PhxFuelType.WOOD_LOG
    effic_in_basic_cycle: float = 0.6
    effic_in_const_operation: float = 0.7
    avg_frac_heat_output: float = 0.4
    temp_diff_on_off: float = 30.0
    rated_capacity: float = 15.0  # kW
    demand_basic_cycle: float = 1.0  # kWh
    power_stationary_run: float = 1.0  # W
    power_standard_run: float | None = None
    no_transport_pellets: bool | None = None
    only_control: bool | None = None
    area_mech_room: float | None = None

    @property
    def fuel(self):
        return self._fuel

    @fuel.setter
    def fuel(self, _in):
        self._fuel = PhxFuelType(_in)


@dataclass
class PhxHeaterBoilerFossil(PhxHeatingDevice):
    """A fossil-fuel boiler (gas, oil, propane) for space heating and/or DHW.

    Attributes:
        system_type (SystemType): Always SystemType.BOILER.
        device_type (DeviceType): Always DeviceType.BOILER.
        params (PhxHeaterBoilerFossilParams): Fossil boiler performance parameters.
    """

    system_type: SystemType = field(init=False, default=SystemType.BOILER)
    device_type: DeviceType = field(init=False, default=DeviceType.BOILER)
    params: PhxHeaterBoilerFossilParams = field(default_factory=PhxHeaterBoilerFossilParams)


@dataclass
class PhxHeaterBoilerWood(PhxHeatingDevice):
    """A wood-fired boiler (log or pellet) for space heating and/or DHW.

    Attributes:
        system_type (SystemType): Always SystemType.BOILER.
        device_type (DeviceType): Always DeviceType.BOILER.
        params (PhxHeaterBoilerWoodParams): Wood boiler performance parameters.
    """

    system_type: SystemType = field(init=False, default=SystemType.BOILER)
    device_type: DeviceType = field(init=False, default=DeviceType.BOILER)
    params: PhxHeaterBoilerWoodParams = field(default_factory=PhxHeaterBoilerWoodParams)


AnyPhxHeaterBoiler = Union[PhxHeaterBoilerFossil, PhxHeaterBoilerWood]


# -----------------------------------------------------------------------------
# District Heat


@dataclass
class PhxHeaterDistrictHeatParams(_base.PhxMechanicalDeviceParams):
    """Parameters for a district heat connection (no additional fields beyond base)."""

    pass


@dataclass
class PhxHeaterDistrictHeat(PhxHeatingDevice):
    """A district heat connection for space heating and/or DHW.

    Attributes:
        system_type (SystemType): Always SystemType.DISTRICT_HEAT.
        device_type (DeviceType): Always DeviceType.DISTRICT_HEAT.
        params (PhxHeaterDistrictHeatParams): District heat parameters.
    """

    system_type: SystemType = field(init=False, default=SystemType.DISTRICT_HEAT)
    device_type: DeviceType = field(init=False, default=DeviceType.DISTRICT_HEAT)
    params: PhxHeaterDistrictHeatParams = field(default_factory=PhxHeaterDistrictHeatParams)


# -----------------------------------------------------------------------------


AnyPhxHeater = Union[
    PhxHeaterElectric,
    PhxHeaterBoilerFossil,
    PhxHeaterBoilerWood,
    PhxHeaterDistrictHeat,
]

AnyPhxHotWaterHeater = Union[
    PhxHeaterElectric,
    PhxHeaterBoilerFossil,
    PhxHeaterBoilerWood,
    PhxHeaterDistrictHeat,
]
