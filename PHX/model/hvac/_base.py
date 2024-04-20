# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Passive House Mechanical Equipment Classes"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from inspect import signature
from typing import Any, ClassVar, Optional, Union

from PHX.model.enums.hvac import DeviceType, SystemType


@dataclass
class PhxUsageProfile:
    """Is the device used to provide..."""

    # -- Percent of total energy demand covered by this device
    space_heating_percent: float = 0.0
    dhw_heating_percent: float = 0.0
    cooling_percent: float = 0.0
    ventilation_percent: float = 0.0
    humidification_percent: float = 0.0
    dehumidification_percent: float = 0.0

    @property
    def space_heating(self) -> bool:
        """True if the device used to provide space heating."""
        return not math.isclose(self.space_heating_percent, 0)

    @space_heating.setter
    def space_heating(self, _in: bool) -> None:
        if _in and self.space_heating_percent == 0:
            self.space_heating_percent = 1.0
        elif _in == False:
            self.space_heating_percent = 0.0

    @property
    def dhw_heating(self) -> bool:
        """True if the device used to provide domestic hot water heating."""
        return not math.isclose(self.dhw_heating_percent, 0)

    @dhw_heating.setter
    def dhw_heating(self, _in: bool) -> None:
        if _in and self.dhw_heating_percent == 0:
            self.dhw_heating_percent = 1.0
        elif _in == False:
            self.dhw_heating_percent = 0.0

    @property
    def cooling(self) -> bool:
        """True if the device used to provide cooling."""
        return not math.isclose(self.cooling_percent, 0)

    @cooling.setter
    def cooling(self, _in: bool) -> None:
        if _in and self.cooling_percent == 0:
            self.cooling_percent = 1.0
        elif _in == False:
            self.cooling_percent = 0.0

    @property
    def ventilation(self) -> bool:
        """True if the device used to provide ventilation."""
        return not math.isclose(self.ventilation_percent, 0)

    @ventilation.setter
    def ventilation(self, _in: bool) -> None:
        if _in and self.ventilation_percent == 0:
            self.ventilation_percent = 1.0
        elif _in == False:
            self.ventilation_percent = 0.0

    @property
    def humidification(self) -> bool:
        """True if the device used to provide humidification."""
        return not math.isclose(self.humidification_percent, 0)

    @humidification.setter
    def humidification(self, _in: bool) -> None:
        if _in and self.humidification_percent == 0:
            self.humidification_percent = 1.0
        elif _in == False:
            self.humidification_percent = 0.0

    @property
    def dehumidification(self) -> bool:
        """True if the device used to provide dehumidification."""
        return not math.isclose(self.dehumidification_percent, 0)

    @dehumidification.setter
    def dehumidification(self, _in: bool) -> None:
        if _in and self.dehumidification_percent == 0:
            self.dehumidification_percent = 1.0
        elif _in == False:
            self.dehumidification_percent = 0.0

    def __add__(self, other: PhxUsageProfile) -> PhxUsageProfile:
        obj = self.__class__()
        obj.space_heating_percent = self.space_heating_percent + other.space_heating_percent
        obj.dhw_heating_percent = self.dhw_heating_percent + other.dhw_heating_percent
        obj.cooling_percent = self.cooling_percent + other.cooling_percent
        obj.ventilation_percent = self.ventilation_percent + other.ventilation_percent
        obj.humidification_percent = self.humidification_percent + other.humidification_percent
        obj.dehumidification_percent = self.dehumidification_percent + other.dehumidification_percent
        return obj


@dataclass
class PhxMechanicalDeviceParams:
    """Base class PHX MechanicalEquipment Params"""

    aux_energy: Optional[float] = None
    aux_energy_dhw: Optional[float] = None
    solar_fraction: Optional[float] = None
    in_conditioned_space: bool = True

    @staticmethod
    def safe_add(attr_1, attr_2):
        if not attr_1 and not attr_2:
            return None
        elif not attr_1 and attr_2:
            return attr_2
        elif attr_1 and not attr_2:
            return attr_1
        else:
            return attr_1 + attr_2

    def __add__(self, other: PhxMechanicalDeviceParams) -> PhxMechanicalDeviceParams:
        new_obj = self.__class__()
        new_obj.aux_energy = new_obj.safe_add(self.aux_energy, other.aux_energy)
        new_obj.aux_energy_dhw = new_obj.safe_add(self.aux_energy_dhw, other.aux_energy_dhw)
        new_obj.solar_fraction = new_obj.safe_add(self.solar_fraction, other.solar_fraction)
        new_obj.in_conditioned_space = any([self.in_conditioned_space, other.in_conditioned_space])
        return new_obj

    def __radd__(self, other):
        if isinstance(other, int):
            return self
        else:
            return self + other


@dataclass
class PhxMechanicalDevice:
    """Base class for PHX Mechanical Devices (heaters, tanks, ventilators, etc...)

    This equipment will be part of a PhxMechanicalSubSystem along with distribution.
    """

    _count: ClassVar[int] = 0

    _identifier: Union[uuid.UUID, str] = field(init=False, default_factory=uuid.uuid4)
    id_num: int = field(init=False, default=0)
    system_type: SystemType = SystemType.ANY
    device_type: DeviceType = DeviceType.ELECTRIC
    display_name: str = "_unnamed_equipment_"
    _quantity: int = 0
    unit: float = 0.0
    percent_coverage: float = 0.0
    usage_profile: PhxUsageProfile = field(default_factory=PhxUsageProfile)
    params: PhxMechanicalDeviceParams = field(default_factory=PhxMechanicalDeviceParams)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def identifier(self) -> str:
        return str(self._identifier)

    @identifier.setter
    def identifier(self, _in: str) -> None:
        if not _in:
            return
        self._identifier = str(_in)

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, _in: Optional[int]) -> None:
        if not _in:
            return
        self._quantity = int(_in)

    def __add__(self, other: PhxMechanicalDevice) -> PhxMechanicalDevice:
        if self.system_type != other.system_type:
            raise ValueError("Cannot add devices of different system types.")

        if self.device_type != other.device_type:
            raise ValueError("Cannot add devices of different device types.")

        obj = self.__class__()
        obj.device_type = self.device_type
        obj.system_type = self.system_type
        obj.display_name = self.display_name
        obj.quantity = self.quantity + other.quantity
        obj.unit = self.unit + other.unit
        obj.percent_coverage = self.percent_coverage + other.percent_coverage
        obj.usage_profile = self.usage_profile + other.usage_profile
        obj.params = self.params + other.params
        return obj

    def __radd__(self, other: PhxMechanicalDevice) -> PhxMechanicalDevice:
        if isinstance(other, int):
            return self
        else:
            return self + other

    @classmethod
    def from_kwargs(cls, **kwargs: dict[str, Any]) -> PhxMechanicalDevice:
        """Allow for the create of base object from arbitrary kwarg input.

        This is used by subclasses during __add__ or __copy__, otherwise fields
        such as 'id_num' or any other init=False fields result in an AttributeError.
        """
        # fetch the constructor's signature
        cls_fields = {field for field in signature(cls).parameters}

        # split the kwargs into native ones and new ones
        native_args, new_args = {}, {}
        for name, val in kwargs.items():
            if name in cls_fields:
                native_args[name] = val
            else:
                new_args[name] = val

        # use the native ones to create the class ...
        return cls(**native_args)

    def __str__(self):
        return f"{self.__class__.__name__}()"
