# -*- Python Version: 3.10 -*-

"""PHX Passive House Mechanical Equipment base classes.

Provides the base device, params, and usage-profile dataclasses that all
specific HVAC device types (ventilation, heating, cooling, DHW, PV, etc.)
inherit from.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from inspect import signature
from typing import Any, ClassVar

from PHX.model.enums.hvac import DeviceType, SystemType


@dataclass
class PhxUsageProfile:
    """Flags indicating which building loads a mechanical device serves and its percent coverage.

    Each load type has a float percent (0.0-1.0) and a bool convenience
    property. Setting the bool to True defaults the percent to 1.0 if it
    was previously 0.0.

    Attributes:
        space_heating_percent (float): Fraction of space heating demand covered. Default: 0.0.
        dhw_heating_percent (float): Fraction of DHW demand covered. Default: 0.0.
        cooling_percent (float): Fraction of cooling demand covered. Default: 0.0.
        ventilation_percent (float): Fraction of ventilation demand covered. Default: 0.0.
        humidification_percent (float): Fraction of humidification demand covered. Default: 0.0.
        dehumidification_percent (float): Fraction of dehumidification demand covered. Default: 0.0.
    """

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
        elif not _in:
            self.space_heating_percent = 0.0

    @property
    def dhw_heating(self) -> bool:
        """True if the device used to provide domestic hot water heating."""
        return not math.isclose(self.dhw_heating_percent, 0)

    @dhw_heating.setter
    def dhw_heating(self, _in: bool) -> None:
        if _in and self.dhw_heating_percent == 0:
            self.dhw_heating_percent = 1.0
        elif not _in:
            self.dhw_heating_percent = 0.0

    @property
    def cooling(self) -> bool:
        """True if the device used to provide cooling."""
        return not math.isclose(self.cooling_percent, 0)

    @cooling.setter
    def cooling(self, _in: bool) -> None:
        if _in and self.cooling_percent == 0:
            self.cooling_percent = 1.0
        elif not _in:
            self.cooling_percent = 0.0

    @property
    def ventilation(self) -> bool:
        """True if the device used to provide ventilation."""
        return not math.isclose(self.ventilation_percent, 0)

    @ventilation.setter
    def ventilation(self, _in: bool) -> None:
        if _in and self.ventilation_percent == 0:
            self.ventilation_percent = 1.0
        elif not _in:
            self.ventilation_percent = 0.0

    @property
    def humidification(self) -> bool:
        """True if the device used to provide humidification."""
        return not math.isclose(self.humidification_percent, 0)

    @humidification.setter
    def humidification(self, _in: bool) -> None:
        if _in and self.humidification_percent == 0:
            self.humidification_percent = 1.0
        elif not _in:
            self.humidification_percent = 0.0

    @property
    def dehumidification(self) -> bool:
        """True if the device used to provide dehumidification."""
        return not math.isclose(self.dehumidification_percent, 0)

    @dehumidification.setter
    def dehumidification(self, _in: bool) -> None:
        if _in and self.dehumidification_percent == 0:
            self.dehumidification_percent = 1.0
        elif not _in:
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
    """Base parameter set shared by all PHX mechanical devices.

    Subclassed by each device type to add device-specific parameters
    (e.g., COP, fuel type, recovery efficiency).

    Attributes:
        aux_energy (float | None): Auxiliary electricity consumption (kWh). Default: None.
        aux_energy_dhw (float | None): Auxiliary electricity for DHW (kWh). Default: None.
        solar_fraction (float | None): Solar thermal fraction (0.0-1.0). Default: None.
        in_conditioned_space (bool): True if the device is inside the thermal envelope. Default: True.
    """

    aux_energy: float | None = None
    aux_energy_dhw: float | None = None
    solar_fraction: float | None = None
    in_conditioned_space: bool = True

    @staticmethod
    def safe_add(attr_1, attr_2):
        """Add two optional numeric values, returning None only if both are falsy."""
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
    """Base class for all PHX mechanical devices (heaters, tanks, ventilators, heat pumps, etc.).

    Each device carries a usage profile describing which loads it serves and
    a params object holding device-specific performance data. Devices are
    collected into a PhxMechanicalSystemCollection alongside distribution
    (piping, ducting).

    Attributes:
        id_num (int): Auto-incrementing instance number (set in __post_init__).
        system_type (SystemType): High-level system category (ventilation, boiler, heat pump, etc.).
            Default: SystemType.ANY.
        device_type (DeviceType): Specific device classification. Default: DeviceType.ELECTRIC.
        display_name (str): Human-readable label. Default: "_unnamed_equipment_".
        unit (float): Device sizing / capacity value. Default: 0.0.
        percent_coverage (float): Fraction of total load served (0.0-1.0). Default: 0.0.
        usage_profile (PhxUsageProfile): Load coverage flags and percentages.
        params (PhxMechanicalDeviceParams): Device performance parameters.
    """

    _count: ClassVar[int] = 0

    _identifier: uuid.UUID | str = field(init=False, default_factory=uuid.uuid4)
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
    def quantity(self, _in: int | None) -> None:
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
        cls_fields = set(signature(cls).parameters)

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
