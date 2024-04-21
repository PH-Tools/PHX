# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Water Devices"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from PHX.model.enums.hvac import DeviceType, PhxHotWaterInputOptions, PhxHotWaterTankType, SystemType
from PHX.model.hvac import _base


@dataclass
class PhxHotWaterDevice(_base.PhxMechanicalDevice):
    def __post_init__(self):
        super().__post_init__()
        self.usage_profile.dhw_heating = True


# -- Hot Water Tank -----------------------------------------------------------


@dataclass
class PhxHotWaterTankParams(_base.PhxMechanicalDeviceParams):
    # -- Device Params
    display_name: str = "_unnamed_PHX_hw_tank_"

    _tank_type: PhxHotWaterTankType = PhxHotWaterTankType.NONE
    _input_option: PhxHotWaterInputOptions = PhxHotWaterInputOptions.SPEC_TOTAL_LOSSES

    _in_conditioned_space: bool = True
    _solar_connection: bool = False
    _solar_losses: float = 0.0  # W/K
    _storage_loss_rate: float = 0.0  # W
    _storage_capacity: float = 0.0  # Liter
    _standby_losses: float = 4.0  # W/K
    _standby_fraction: float = 0.30  # %
    _room_temp: float = 20.0
    _water_temp: float = 60.0

    @property
    def tank_type(self) -> PhxHotWaterTankType:
        return self._tank_type

    @tank_type.setter
    def tank_type(self, value: Optional[PhxHotWaterTankType]) -> None:
        if value is not None:
            self._tank_type = value

    @property
    def input_option(self) -> PhxHotWaterInputOptions:
        return self._input_option

    @input_option.setter
    def input_option(self, value: Optional[PhxHotWaterInputOptions]) -> None:
        if value is not None:
            self._input_option = value

    @property
    def in_conditioned_space(self) -> bool:
        return self._in_conditioned_space

    @in_conditioned_space.setter
    def in_conditioned_space(self, value: Optional[bool]) -> None:
        if value is not None:
            self._in_conditioned_space = value

    @property
    def solar_connection(self) -> bool:
        return self._solar_connection

    @solar_connection.setter
    def solar_connection(self, value: Optional[bool]) -> None:
        if value is not None:
            self._solar_connection = value

    @property
    def solar_losses(self) -> float:
        return self._solar_losses

    @solar_losses.setter
    def solar_losses(self, value: Optional[float]) -> None:
        if value is not None:
            self._solar_losses = value

    @property
    def storage_loss_rate(self) -> float:
        return self._storage_loss_rate

    @storage_loss_rate.setter
    def storage_loss_rate(self, value: Optional[float]) -> None:
        if value is not None:
            self._storage_loss_rate = value

    @property
    def storage_capacity(self) -> float:
        return self._storage_capacity

    @storage_capacity.setter
    def storage_capacity(self, value: Optional[float]) -> None:
        if value is not None:
            self._storage_capacity = value

    @property
    def standby_losses(self) -> float:
        return self._standby_losses

    @standby_losses.setter
    def standby_losses(self, value: Optional[float]) -> None:
        if value is not None:
            self._standby_losses = value

    @property
    def standby_fraction(self) -> float:
        return self._standby_fraction

    @standby_fraction.setter
    def standby_fraction(self, value: Optional[float]) -> None:
        if value is not None:
            self._standby_fraction = value

    @property
    def room_temp(self) -> float:
        return self._room_temp

    @room_temp.setter
    def room_temp(self, value: Optional[float]) -> None:
        if value is not None:
            self._room_temp = value

    @property
    def water_temp(self) -> float:
        return self._water_temp

    @water_temp.setter
    def water_temp(self, value: Optional[float]) -> None:
        if value is not None:
            self._water_temp = value

    def __add__(self, other: PhxHotWaterTankParams) -> PhxHotWaterTankParams:
        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))

        new_obj.tank_type = self.tank_type
        new_obj.input_option = self.input_option

        new_obj.in_conditioned_space = any([self.in_conditioned_space, other.in_conditioned_space])
        new_obj.solar_connection = any([self.solar_connection, other.solar_connection])
        new_obj.solar_losses = (self.solar_losses + other.solar_losses) / 2

        new_obj.storage_loss_rate = (self.storage_loss_rate + other.storage_loss_rate) / 2
        new_obj.storage_capacity = (self.storage_capacity + other.storage_capacity) / 2

        new_obj.standby_losses = (self.standby_losses + other.standby_losses) / 2
        new_obj.standby_fraction = (self.standby_fraction + other.standby_fraction) / 2

        new_obj.room_temp = (self.room_temp + other.room_temp) / 2
        new_obj.water_temp = (self.water_temp + other.water_temp) / 2

        return new_obj


@dataclass
class PhxHotWaterTank(PhxHotWaterDevice):
    system_type: SystemType = field(init=False, default=SystemType.WATER_STORAGE)
    device_type: DeviceType = field(init=False, default=DeviceType.WATER_STORAGE)
    params: PhxHotWaterTankParams = field(default_factory=PhxHotWaterTankParams)

    def __add__(self, other: PhxHotWaterTank) -> PhxHotWaterTank:
        base = super().__add__(other)
        new_obj = self.__class__.from_kwargs(**vars(base))
        return new_obj


AnyWaterTank = PhxHotWaterTank
