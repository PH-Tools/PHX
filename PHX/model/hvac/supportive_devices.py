# -*- Python Version: 3.10 -*-

"""PHX supportive (auxiliary energy) device classes.

Represents circulating pumps, storage load pumps, and other auxiliary
electrical devices that contribute to the building's total energy demand
and internal heat gains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from PHX.model.enums.hvac import PhxSupportiveDeviceType
from PHX.model.hvac import _base


@dataclass
class PhxSupportiveDeviceParams(_base.PhxMechanicalDeviceParams):
    """Parameters for a supportive (auxiliary energy) device.

    When devices are merged via __add__, energy demand is calculated as
    the time-weighted average and IHG utilization factor is energy-weighted.

    Attributes:
        in_conditioned_space (bool): True if device is inside the thermal envelope. Default: True.
        norm_energy_demand_W (float): Nominal power consumption (W). Default: 1.0.
        annual_period_operation_khrs (float): Annual operating period (kilo-hours). Default: 8.760.
        ihg_utilization_factor (float): Internal heat gains utilization factor (0.0-1.0).
            Default: 1.0.
    """

    in_conditioned_space: bool = True
    norm_energy_demand_W: float = 1.0
    annual_period_operation_khrs: float = 8.760
    ihg_utilization_factor: float = 1.0

    def __add__(self, other: PhxSupportiveDeviceParams) -> PhxSupportiveDeviceParams:
        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))
        new_obj.in_conditioned_space = any([self.in_conditioned_space, other.in_conditioned_space])

        # -- Merge the energy usage and hours of operation
        total_kilohours = self.annual_period_operation_khrs + other.annual_period_operation_khrs
        new_obj.annual_period_operation_khrs = total_kilohours
        energy_self = self.norm_energy_demand_W * self.annual_period_operation_khrs
        energy_other = other.norm_energy_demand_W * other.annual_period_operation_khrs
        total_energy = energy_self + energy_other
        new_obj.norm_energy_demand_W = total_energy / total_kilohours

        # -- Energy-weighted average of IHG utilization factor
        if total_energy > 0:
            new_obj.ihg_utilization_factor = (
                energy_self * self.ihg_utilization_factor + energy_other * other.ihg_utilization_factor
            ) / total_energy
        else:
            new_obj.ihg_utilization_factor = (self.ihg_utilization_factor + other.ihg_utilization_factor) / 2

        return new_obj


@dataclass
class PhxSupportiveDevice(_base.PhxMechanicalDevice):
    """A supportive device such as a circulating pump or auxiliary electrical load.

    Examples include heat-distribution circulating pumps, DHW recirculation
    pumps, DHW storage load pumps, and other auxiliary devices.

    Attributes:
        id_num (int): Auto-incrementing instance number.
        display_name (str): Human-readable label. Default: "__unnamed_device__".
        device_type (PhxSupportiveDeviceType): Device classification. Default: OTHER.
        quantity (int): Number of identical devices. Default: 1.
        params (PhxSupportiveDeviceParams): Supportive device parameters.
    """

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
