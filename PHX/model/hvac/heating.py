# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Mechanical Heating Devices."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from PHX.model.enums.hvac import DeviceType, PhxFuelType, SystemType
from PHX.model.hvac import _base


@dataclass
class PhxHeatingDevice(_base.PhxMechanicalDevice):
    def __post_init__(self):
        super().__post_init__()


# -----------------------------------------------------------------------------
# Electric


@dataclass
class PhxHeaterElectricParams(_base.PhxMechanicalDeviceParams):
    pass


@dataclass
class PhxHeaterElectric(PhxHeatingDevice):
    system_type: SystemType = field(init=False, default=SystemType.ELECTRIC)
    device_type: DeviceType = field(init=False, default=DeviceType.ELECTRIC)
    params: PhxHeaterElectricParams = field(default_factory=PhxHeaterElectricParams)


# -----------------------------------------------------------------------------
# Boilers


@dataclass
class PhxHeaterBoilerFossilParams(_base.PhxMechanicalDeviceParams):
    _fuel: PhxFuelType = PhxFuelType.NATURAL_GAS
    _condensing: bool = True
    _in_conditioned_space: bool = True
    _effic_at_30_percent_load: float = 0.98
    _effic_at_nominal_load: float = 0.94
    _avg_rtrn_temp_at_30_percent_load: float = 30
    _avg_temp_at_70C_55C: float = 41
    _avg_temp_at_55C_45C: float = 35
    _avg_temp_at_32C_28C: float = 24
    _standby_loss_at_70C: Optional[float] = None
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
    def condensing(self, value: Optional[bool]) -> None:
        if value is not None:
            self._condensing = value

    @property
    def in_conditioned_space(self) -> bool:
        return self._in_conditioned_space

    @in_conditioned_space.setter
    def in_conditioned_space(self, value: Optional[bool]) -> None:
        if value is not None:
            self._in_conditioned_space = value

    @property
    def effic_at_30_percent_load(self) -> float:
        return self._effic_at_30_percent_load

    @effic_at_30_percent_load.setter
    def effic_at_30_percent_load(self, value: Optional[float]) -> None:
        if value is not None:
            self._effic_at_30_percent_load = value

    @property
    def effic_at_nominal_load(self) -> float:
        return self._effic_at_nominal_load

    @effic_at_nominal_load.setter
    def effic_at_nominal_load(self, value: Optional[float]) -> None:
        if value is not None:
            self._effic_at_nominal_load = value

    @property
    def avg_rtrn_temp_at_30_percent_load(self) -> float:
        return self._avg_rtrn_temp_at_30_percent_load

    @avg_rtrn_temp_at_30_percent_load.setter
    def avg_rtrn_temp_at_30_percent_load(self, value: Optional[float]) -> None:
        if value is not None:
            self._avg_rtrn_temp_at_30_percent_load = value

    @property
    def avg_temp_at_70C_55C(self) -> float:
        return self._avg_temp_at_70C_55C

    @avg_temp_at_70C_55C.setter
    def avg_temp_at_70C_55C(self, value: Optional[float]) -> None:
        if value is not None:
            self._avg_temp_at_70C_55C = value

    @property
    def avg_temp_at_55C_45C(self) -> float:
        return self._avg_temp_at_55C_45C

    @avg_temp_at_55C_45C.setter
    def avg_temp_at_55C_45C(self, value: Optional[float]) -> None:
        if value is not None:
            self._avg_temp_at_55C_45C = value

    @property
    def avg_temp_at_32C_28C(self) -> float:
        return self._avg_temp_at_32C_28C

    @avg_temp_at_32C_28C.setter
    def avg_temp_at_32C_28C(self, value: Optional[float]) -> None:
        if value is not None:
            self._avg_temp_at_32C_28C = value

    @property
    def standby_loss_at_70C(self) -> Optional[float]:
        return self._standby_loss_at_70C

    @standby_loss_at_70C.setter
    def standby_loss_at_70C(self, value: Optional[float]) -> None:
        if value is not None:
            self._standby_loss_at_70C = value

    @property
    def rated_capacity(self) -> float:
        return self._rated_capacity

    @rated_capacity.setter
    def rated_capacity(self, value: Optional[float]) -> None:
        if value is not None:
            self._rated_capacity = value


@dataclass
class PhxHeaterBoilerWoodParams(_base.PhxMechanicalDeviceParams):
    _fuel: PhxFuelType = PhxFuelType.WOOD_LOG
    effic_in_basic_cycle: float = 0.6
    effic_in_const_operation: float = 0.7
    avg_frac_heat_output: float = 0.4
    temp_diff_on_off: float = 30.0
    rated_capacity: float = 15.0  # kW
    demand_basic_cycle: float = 1.0  # kWh
    power_stationary_run: float = 1.0  # W
    power_standard_run: Optional[float] = None
    no_transport_pellets: Optional[bool] = None
    only_control: Optional[bool] = None
    area_mech_room: Optional[float] = None

    @property
    def fuel(self):
        return self._fuel

    @fuel.setter
    def fuel(self, _in):
        self._fuel = PhxFuelType(_in)


@dataclass
class PhxHeaterBoilerFossil(PhxHeatingDevice):
    system_type: SystemType = field(init=False, default=SystemType.BOILER)
    device_type: DeviceType = field(init=False, default=DeviceType.BOILER)
    params: PhxHeaterBoilerFossilParams = field(default_factory=PhxHeaterBoilerFossilParams)


@dataclass
class PhxHeaterBoilerWood(PhxHeatingDevice):
    system_type: SystemType = field(init=False, default=SystemType.BOILER)
    device_type: DeviceType = field(init=False, default=DeviceType.BOILER)
    params: PhxHeaterBoilerWoodParams = field(default_factory=PhxHeaterBoilerWoodParams)


AnyPhxHeaterBoiler = Union[PhxHeaterBoilerFossil, PhxHeaterBoilerWood]


# -----------------------------------------------------------------------------
# District Heat


@dataclass
class PhxHeaterDistrictHeatParams(_base.PhxMechanicalDeviceParams):
    pass


@dataclass
class PhxHeaterDistrictHeat(PhxHeatingDevice):
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
