# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Mechanical Ventilation Devices"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union, ClassVar

from PHX.model.enums.hvac import DeviceType, SystemType, PhxExhaustVentType
from PHX.model.hvac import _base


@dataclass
class PhxDeviceVentilation(_base.PhxMechanicalDevice):
    def __post_init__(self):
        super().__post_init__()
        self.usage_profile.ventilation = True


# -- HRV / ERV Air  -----------------------------------------------------------


@dataclass
class PhxDeviceVentilatorParams(_base.PhxMechanicalDeviceParams):
    sensible_heat_recovery: float = 0.0
    latent_heat_recovery: float = 0.0
    quantity: int = 1
    electric_efficiency: float = 0.55
    frost_protection_reqd: bool = True
    temperature_below_defrost_used: float = -5.0

    def __add__(self, other: PhxDeviceVentilatorParams) -> PhxDeviceVentilatorParams:
        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))
        new_obj.sensible_heat_recovery = (
            self.sensible_heat_recovery + other.sensible_heat_recovery
        ) / 2
        new_obj.latent_heat_recovery = (
            self.latent_heat_recovery + other.latent_heat_recovery
        ) / 2
        new_obj.quantity = self.quantity + other.quantity
        new_obj.electric_efficiency = (
            self.electric_efficiency + other.electric_efficiency
        ) / 2
        new_obj.frost_protection_reqd = any(
            [self.frost_protection_reqd, other.frost_protection_reqd]
        )
        new_obj.temperature_below_defrost_used = (
            self.temperature_below_defrost_used + other.temperature_below_defrost_used
        ) / 2
        return new_obj


@dataclass
class PhxDeviceVentilator(PhxDeviceVentilation):
    system_type: SystemType = field(init=False, default=SystemType.VENTILATION)
    device_type: DeviceType = field(init=False, default=DeviceType.VENTILATION)
    params: PhxDeviceVentilatorParams = field(default_factory=PhxDeviceVentilatorParams)

    def __post_init__(self):
        super().__post_init__()

    def __add__(self, other: PhxDeviceVentilator) -> PhxDeviceVentilator:
        base = super().__add__(other)
        new_obj = self.__class__.from_kwargs(**vars(base))
        return new_obj


# -- Exhaust Ventilators (Kitchen/Dryer) --------------------------------------


@dataclass
class PhxExhaustVentilatorParams(_base.PhxMechanicalDeviceParams):
    exhaust_type: PhxExhaustVentType = PhxExhaustVentType.KITCHEN_HOOD
    annual_runtime_minutes: float = 0.0
    exhaust_flow_rate_m3h: float = 0.0

    def _calc_flow_weighted_annual_minutes(
        self, other: PhxExhaustVentilatorParams
    ) -> float:
        """Return the flow-weighted annual runtime minutes.

        ie: Device A (50 mins @ 450 m3/h) + Device B (40 mins @ 200 m3/h) -> 47 mins
        """
        weighted_flow_a = self.annual_runtime_minutes * self.exhaust_flow_rate_m3h
        weighted_flow_b = other.annual_runtime_minutes * other.exhaust_flow_rate_m3h
        total_weighted_flow = weighted_flow_a + weighted_flow_b
        total_flow = self.exhaust_flow_rate_m3h + other.exhaust_flow_rate_m3h
        weighted_minutes = total_weighted_flow / total_flow
        return weighted_minutes

    def __add__(self, other: PhxExhaustVentilatorParams) -> PhxExhaustVentilatorParams:
        if not self.exhaust_type == other.exhaust_type:
            msg = (
                f"Error: Cannot combine PHX Exhaust Ventilation Device of type "
                f"'{self.exhaust_type}' with device of type: '{other.exhaust_type}'"
            )
            raise Exception(msg)

        base = super().__add__(other)
        new_obj = self.__class__(**vars(base))

        if (self.annual_runtime_minutes > 0) or (other.annual_runtime_minutes > 0):
            new_obj.annual_runtime_minutes = self._calc_flow_weighted_annual_minutes(
                other
            )

        new_obj.exhaust_flow_rate_m3h = (
            self.exhaust_flow_rate_m3h + other.exhaust_flow_rate_m3h
        )
        return new_obj


@dataclass
class PhxExhaustVentilatorBase(_base.PhxMechanicalDevice):
    """Base class for all Exhaust Ventilation.

    Note that the _count and id_num are implemented here to allow each unique
    type of device to increment the count at the base-class level without affecting
    the _base.PhxMechanicalDevice class.
    """

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)

    def __post_init__(self):
        super().__post_init__()
        # -- Use PhxExhaustVentilatorBase._count instead of super() so that all
        # -- counting happens at the parent class, not the child class.
        PhxExhaustVentilatorBase._count += 1
        self.id_num = PhxExhaustVentilatorBase._count
        self.quantity = 1


@dataclass
class PhxExhaustVentilatorRangeHood(PhxExhaustVentilatorBase):
    system_type: SystemType = field(init=False, default=SystemType.VENTILATION)
    device_type: DeviceType = field(init=False, default=DeviceType.VENTILATION)
    params: PhxExhaustVentilatorParams = field(default_factory=PhxExhaustVentilatorParams)

    def __post_init__(self):
        super().__post_init__()
        self.params.exhaust_type = PhxExhaustVentType.KITCHEN_HOOD

    def __add__(
        self, other: PhxExhaustVentilatorRangeHood
    ) -> PhxExhaustVentilatorRangeHood:
        base = super().__add__(other)
        new_obj = self.__class__.from_kwargs(**vars(base))
        new_obj.quantity = self.quantity + other.quantity
        new_obj.display_name = f"Kitchen Hoods ({new_obj.quantity})"

        return new_obj

    def __str__(self):
        return f"{self.__class__.__name__}({self.display_name}, {self.params.exhaust_flow_rate_m3h:,.1f}m3/h)"


@dataclass
class PhxExhaustVentilatorDryer(PhxExhaustVentilatorBase):
    system_type: SystemType = field(init=False, default=SystemType.VENTILATION)
    device_type: DeviceType = field(init=False, default=DeviceType.VENTILATION)
    params: PhxExhaustVentilatorParams = field(default_factory=PhxExhaustVentilatorParams)

    def __post_init__(self):
        PhxExhaustVentilatorBase.__post_init__(self)
        self.params.exhaust_type = PhxExhaustVentType.DRYER

    def __add__(self, other: PhxExhaustVentilatorDryer) -> PhxExhaustVentilatorDryer:
        base = super().__add__(other)
        new_obj = self.__class__.from_kwargs(**vars(base))
        new_obj.quantity = self.quantity + other.quantity
        new_obj.display_name = f"Dryers ({new_obj.quantity})"
        return new_obj

    def __str__(self):
        return f"{self.__class__.__name__}({self.display_name}, {self.params.exhaust_flow_rate_m3h:,.1f}m3/h)"


@dataclass
class PhxExhaustVentilatorUserDefined(PhxExhaustVentilatorBase):
    system_type: SystemType = field(init=False, default=SystemType.VENTILATION)
    device_type: DeviceType = field(init=False, default=DeviceType.VENTILATION)
    params: PhxExhaustVentilatorParams = field(default_factory=PhxExhaustVentilatorParams)

    def __post_init__(self):
        super().__post_init__()
        self.params.exhaust_type = PhxExhaustVentType.USER_DEFINED

    def __add__(
        self, other: PhxExhaustVentilatorUserDefined
    ) -> PhxExhaustVentilatorUserDefined:
        base = super().__add__(other)
        new_obj = self.__class__.from_kwargs(**vars(base))
        new_obj.quantity = self.quantity + other.quantity
        new_obj.display_name = f"User-Determined ({new_obj.quantity})"
        return new_obj

    def __str__(self):
        return f"{self.__class__.__name__}({self.display_name}, {self.params.exhaust_flow_rate_m3h:,.1f}m3/h)"


# -----------------------------------------------------------------------------
# ---- Type Alias


AnyPhxVentilation = PhxDeviceVentilator

AnyPhxExhaustVent = Union[
    PhxExhaustVentilatorRangeHood,
    PhxExhaustVentilatorDryer,
    PhxExhaustVentilatorUserDefined,
]
