# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Aux-Energy . Supportive Extra Devices."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from PHX.model.enums.hvac import PhxSupportiveDeviceType
from PHX.model.hvac import _base


@dataclass
class PhxSupportiveDeviceParams(_base.PhxMechanicalDeviceParams):
    in_conditioned_space: bool = True
    norm_energy_demand_W: float = 1.0
    annual_period_operation_khrs: float = 8.760

    def __add__(self, other: PhxSupportiveDeviceParams) -> PhxSupportiveDeviceParams:
        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))
        new_obj.in_conditioned_space = any([self.in_conditioned_space, other.in_conditioned_space])

        # -- Merge the energy usage and hours of operation
        total_kilohours = self.annual_period_operation_khrs + other.annual_period_operation_khrs
        new_obj.annual_period_operation_khrs = total_kilohours
        total_watt_kilohours = (
            self.norm_energy_demand_W * self.annual_period_operation_khrs
            + other.norm_energy_demand_W * other.annual_period_operation_khrs
        )
        new_obj.norm_energy_demand_W = total_watt_kilohours / total_kilohours
        return new_obj


@dataclass
class PhxSupportiveDevice(_base.PhxMechanicalDevice):
    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)

    display_name: str = "__unnamed_device__"
    device_type: PhxSupportiveDeviceType = field(default=PhxSupportiveDeviceType.OTHER)
    quantity: int = 1
    params: PhxSupportiveDeviceParams = field(default_factory=PhxSupportiveDeviceParams)

    def __post_init__(self):
        super().__post_init__()
        PhxSupportiveDevice._count += 1
        self.id_num = PhxSupportiveDevice._count

    def __add__(self, other: PhxSupportiveDevice) -> PhxSupportiveDevice:
        if self.device_type != other.device_type:
            raise ValueError(f"Cannot add two different device types: {self.device_type} and {other.device_type}")
        base = super().__add__(other)
        new_obj = self.__class__.from_kwargs(**vars(base))
        new_obj.display_name = f"Supportive Device ({new_obj.quantity})"

        return new_obj
