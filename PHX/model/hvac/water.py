# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Water Devices"""

from __future__ import annotations
from dataclasses import dataclass, field

from PHX.model.enums.hvac import DeviceType, PhxHotWaterInputOptions, SystemType
from PHX.model.hvac import _base
from PHX.model.enums.hvac import PhxHotWaterTankType


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

    tank_type: PhxHotWaterTankType = PhxHotWaterTankType.NONE
    input_option: PhxHotWaterInputOptions = PhxHotWaterInputOptions.SPEC_TOTAL_LOSSES
    in_conditioned_space: bool = True

    solar_connection: bool = False
    solar_losses: float = 0.0  # W/K

    storage_loss_rate: float = 0.0  # W
    storage_capacity: float = 0.0  # Liter

    standby_losses: float = 4.0  # W/K
    standby_fraction: float = 0.30  # %

    room_temp: float = 20.0
    water_temp: float = 60.0

    def __add__(self, other: PhxHotWaterTankParams) -> PhxHotWaterTankParams:
        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))

        new_obj.tank_type = self.tank_type
        new_obj.input_option = self.input_option

        new_obj.in_conditioned_space = any(
            [self.in_conditioned_space, other.in_conditioned_space]
        )
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
