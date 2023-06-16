# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Passive House Renewable Energy (PV) Device classes"""

from __future__ import annotations
from dataclasses import dataclass, field

from PHX.model.enums.hvac import DeviceType, SystemType
from PHX.model.hvac import _base


@dataclass
class PhxDevicePhotovoltaicParams(_base.PhxMechanicalDeviceParams):
    """PV System Parameters"""

    location_type: int = 1
    onsite_utilization_type: int = 1
    utilization_type: int = 1
    array_size: int = 0
    photovoltaic_renewable_energy: int = 0
    onsite_utilization_factor: float = 1.0
    auxiliary_energy: int = 0
    auxiliary_energy_DHW: int = 0
    in_conditioned_space: bool = False

    def __add__(self, other: PhxDevicePhotovoltaicParams) -> PhxDevicePhotovoltaicParams:
        return PhxDevicePhotovoltaicParams(
            location_type=self.location_type,
            onsite_utilization_type=self.onsite_utilization_type,
            utilization_type=self.utilization_type,
            array_size=self.array_size + other.array_size,
            photovoltaic_renewable_energy=self.photovoltaic_renewable_energy
            + other.photovoltaic_renewable_energy,
            onsite_utilization_factor=(
                self.onsite_utilization_factor + other.onsite_utilization_factor
            )
            / 2,
            auxiliary_energy=self.auxiliary_energy + other.auxiliary_energy,
            auxiliary_energy_DHW=self.auxiliary_energy_DHW + other.auxiliary_energy_DHW,
            in_conditioned_space=self.in_conditioned_space,
        )


@dataclass
class PhxDevicePhotovoltaic(_base.PhxMechanicalDevice):
    """PV Panel Systems."""

    system_type: SystemType = field(init=False, default=SystemType.PHOTOVOLTAIC)
    device_type: DeviceType = field(init=False, default=DeviceType.PHOTOVOLTAIC)
    params: PhxDevicePhotovoltaicParams = field(
        default_factory=PhxDevicePhotovoltaicParams
    )

    def __post_init__(self) -> None:
        super().__post_init__()

    def __add__(self, other: PhxDevicePhotovoltaic) -> PhxDevicePhotovoltaic:
        if self.system_type.value != other.system_type.value:
            raise ValueError(
                f"Error: Cannot add {self.system_type.value} to {other.system_type.value}"
            )
        if self.device_type.value != other.device_type.value:
            raise ValueError(
                f"Error: Cannot add {self.device_type.value} to {other.device_type.value}"
            )
        return self + other


AnyRenewableDevice = PhxDevicePhotovoltaic
