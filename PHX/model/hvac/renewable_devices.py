# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Passive House Renewable Energy (PV) Device classes"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from PHX.model.enums.hvac import DeviceType, SystemType
from PHX.model.hvac import _base


@dataclass
class PhxDevicePhotovoltaicParams(_base.PhxMechanicalDeviceParams):
    """PV System Parameters"""

    _location_type: int = 1
    _onsite_utilization_type: int = 2
    _utilization_type: int = 1

    _array_size: float = 0.0
    _photovoltaic_renewable_energy: float = 0.0
    _onsite_utilization_factor: float = 1.0
    _auxiliary_energy: float = 0.0
    _auxiliary_energy_DHW: float = 0.0
    _in_conditioned_space: bool = False

    @property
    def location_type(self) -> int:
        return self._location_type

    @location_type.setter
    def location_type(self, value: Optional[int]) -> None:
        if value is not None:
            self._location_type = value

    @property
    def onsite_utilization_type(self) -> int:
        return self._onsite_utilization_type

    @onsite_utilization_type.setter
    def onsite_utilization_type(self, value: Optional[int]) -> None:
        if value is not None:
            self._onsite_utilization_type = value

    @property
    def utilization_type(self) -> int:
        return self._utilization_type

    @utilization_type.setter
    def utilization_type(self, value: Optional[int]) -> None:
        if value is not None:
            self._utilization_type = value

    @property
    def array_size(self) -> float:
        return self._array_size

    @array_size.setter
    def array_size(self, value: Optional[float]) -> None:
        if value is not None:
            self._array_size = value

    @property
    def photovoltaic_renewable_energy(self) -> float:
        return self._photovoltaic_renewable_energy

    @photovoltaic_renewable_energy.setter
    def photovoltaic_renewable_energy(self, value: Optional[float]) -> None:
        if value is not None:
            self._photovoltaic_renewable_energy = value

    @property
    def onsite_utilization_factor(self) -> float:
        return self._onsite_utilization_factor

    @onsite_utilization_factor.setter
    def onsite_utilization_factor(self, value: Optional[float]) -> None:
        if value is not None:
            self._onsite_utilization_factor = value

    @property
    def auxiliary_energy(self) -> float:
        return self._auxiliary_energy

    @auxiliary_energy.setter
    def auxiliary_energy(self, value: Optional[float]) -> None:
        if value is not None:
            self._auxiliary_energy = value

    @property
    def auxiliary_energy_DHW(self) -> float:
        return self._auxiliary_energy_DHW

    @auxiliary_energy_DHW.setter
    def auxiliary_energy_DHW(self, value: Optional[float]) -> None:
        if value is not None:
            self._auxiliary_energy_DHW = value

    @property
    def in_conditioned_space(self) -> bool:
        return self._in_conditioned_space

    @in_conditioned_space.setter
    def in_conditioned_space(self, value: Optional[bool]) -> None:
        if value is not None:
            self._in_conditioned_space = value

    def __add__(self, other: PhxDevicePhotovoltaicParams) -> PhxDevicePhotovoltaicParams:
        return PhxDevicePhotovoltaicParams(
            _location_type=self.location_type,
            _onsite_utilization_type=self.onsite_utilization_type,
            _utilization_type=self.utilization_type,
            _array_size=self.array_size + other.array_size,
            _photovoltaic_renewable_energy=self.photovoltaic_renewable_energy + other.photovoltaic_renewable_energy,
            _onsite_utilization_factor=(self.onsite_utilization_factor + other.onsite_utilization_factor) / 2,
            _auxiliary_energy=self.auxiliary_energy + other.auxiliary_energy,
            _auxiliary_energy_DHW=self.auxiliary_energy_DHW + other.auxiliary_energy_DHW,
            in_conditioned_space=self.in_conditioned_space,
        )


@dataclass
class PhxDevicePhotovoltaic(_base.PhxMechanicalDevice):
    """PV Panel Systems."""

    system_type: SystemType = field(init=False, default=SystemType.PHOTOVOLTAIC)
    device_type: DeviceType = field(init=False, default=DeviceType.PHOTOVOLTAIC)
    params: PhxDevicePhotovoltaicParams = field(default_factory=PhxDevicePhotovoltaicParams)

    def __post_init__(self) -> None:
        super().__post_init__()

    def __add__(self, other: PhxDevicePhotovoltaic) -> PhxDevicePhotovoltaic:
        if self.system_type.value != other.system_type.value:
            raise ValueError(f"Error: Cannot add {self.system_type.value} to {other.system_type.value}")
        if self.device_type.value != other.device_type.value:
            raise ValueError(f"Error: Cannot add {self.device_type.value} to {other.device_type.value}")
        return self + other


AnyRenewableDevice = PhxDevicePhotovoltaic
