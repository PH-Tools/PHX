# -*- Python Version: 3.10 -*-

"""PHX Passive House Electrical Equipment (Appliances) Classes"""

import inspect
import sys
import uuid
from dataclasses import dataclass, field
from typing import ClassVar

from PHX.model.enums.elec_equip import ElectricEquipmentType


@dataclass
class PhxElectricalDevice:
    """Base class for PHX Electrical Equipment (dishwashers, laundry, lighting, etc.)"""

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    identifier: uuid.UUID | str = field(default_factory=uuid.uuid4)

    _reference_quantity: int = 1
    _reference_energy_norm: int = 2
    _quantity: int = 1

    display_name: str | None = "_unnamed_equipment_"
    comment: str | None = ""
    in_conditioned_space: bool | None = True
    energy_demand: float | None = 100.0
    energy_demand_per_use: float | None = 100.0
    combined_energy_factor: float | None = 0.0

    device_type: ElectricEquipmentType = field(default=ElectricEquipmentType.CUSTOM)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def reference_quantity(self) -> int:
        return self._reference_quantity

    @reference_quantity.setter
    def reference_quantity(self, value: int | None) -> None:
        if value is not None:
            self._reference_quantity = int(value)

    @property
    def reference_energy_norm(self) -> int:
        return self._reference_energy_norm

    @reference_energy_norm.setter
    def reference_energy_norm(self, value: int | None) -> None:
        if value is not None:
            self._reference_energy_norm = value

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int | None) -> None:
        if value is not None:
            self._quantity = value

    def get_energy_demand(self) -> float:
        """To allow for subclass custom behavior. Cannot use @property since
        it will not work with __setattr__ which is used during HBPH->PHX object creation.
        """
        return self.energy_demand or 0.0

    def get_quantity(self) -> int:
        """To allow for subclass custom behavior. Cannot use @property since
        it will not work with __setattr__ which is used during HBPH->PHX object creation.
        """
        return self.quantity or 1


class PhxDeviceDishwasher(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self._water_connection: int = 1  # DHW Connection
        self._capacity_type: int = 1
        self.display_name = "Kitchen Dishwasher"
        self.capacity: float | None = 1.0
        self.device_type = ElectricEquipmentType.DISHWASHER

    @property
    def water_connection(self) -> int | None:
        return self._water_connection

    @water_connection.setter
    def water_connection(self, value: int | None) -> None:
        if value is not None:
            self._water_connection = value

    @property
    def capacity_type(self) -> int | None:
        return self._capacity_type

    @capacity_type.setter
    def capacity_type(self, value: int | None) -> None:
        if value is not None:
            self._capacity_type = value


class PhxDeviceClothesWasher(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self.display_name = "Laundry - washer"
        self._water_connection: int = 1  # DHW Connection

        self.capacity: float | None = 0.0814  # m3
        self.modified_energy_factor: float | None = 2.38
        self.utilization_factor: float | None = 1.0
        self.device_type = ElectricEquipmentType.CLOTHES_WASHER

    @property
    def water_connection(self) -> int | None:
        return self._water_connection

    @water_connection.setter
    def water_connection(self, value: int | None) -> None:
        if value is not None:
            self._water_connection = value


class PhxDeviceClothesDryer(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self.display_name = "Laundry - dryer"
        self._dryer_type: int = 4  # Condensation dryer
        self._field_utilization_factor_type: int = 1  # Timer

        self.gas_consumption: float | None = 0.0  # kWh
        self.gas_efficiency_factor: float | None = 2.67
        self.field_utilization_factor: float | None = 1.18
        self.device_type = ElectricEquipmentType.CLOTHES_DRYER

    @property
    def dryer_type(self) -> int:
        return self._dryer_type

    @dryer_type.setter
    def dryer_type(self, value: int | None) -> None:
        if value is not None:
            self._dryer_type = value

    @property
    def field_utilization_factor_type(self) -> int | None:
        return self._field_utilization_factor_type

    @field_utilization_factor_type.setter
    def field_utilization_factor_type(self, value: int | None) -> None:
        if value is not None:
            self._field_utilization_factor_type = value


class PhxDeviceRefrigerator(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self.display_name = "Kitchen refrigerator"
        self.device_type = ElectricEquipmentType.REFRIGERATOR


class PhxDeviceFreezer(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self.display_name = "kitchen freezer"
        self.device_type = ElectricEquipmentType.FREEZER


class PhxDeviceFridgeFreezer(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self.display_name = "Kitchen fridge/freeze combo"
        self.device_type = ElectricEquipmentType.FRIDGE_FREEZER


class PhxDeviceCooktop(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "Kitchen cooking"
        self._cooktop_type: int = 1  # Electric
        self.device_type = ElectricEquipmentType.COOKING

    @property
    def cooktop_type(self) -> int:
        return self._cooktop_type

    @cooktop_type.setter
    def cooktop_type(self, value: int | None) -> None:
        if value is not None:
            self._cooktop_type = value


class PhxDeviceMEL(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self.display_name = "PHIUS+ MELS"
        self.device_type = ElectricEquipmentType.MEL


class PhxDeviceLightingInterior(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self.display_name = "PHIUS+ Interior Lighting"
        self.frac_high_efficiency: float | None = 1.0
        self.device_type = ElectricEquipmentType.LIGHTING_INTERIOR


class PhxDeviceLightingExterior(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self.display_name = "PHIUS+ Exterior Lighting"
        self.frac_high_efficiency: float | None = 1.0
        self.device_type = ElectricEquipmentType.LIGHTING_EXTERIOR
        self.in_conditioned_space = False


class PhxDeviceLightingGarage(PhxElectricalDevice):
    def __init__(self) -> None:
        super().__init__()
        self.display_name = "PHIUS+ Garage Lighting"
        self.frac_high_efficiency: float | None = 1.0
        self.device_type = ElectricEquipmentType.LIGHTING_GARAGE
        self.in_conditioned_space = False


class PhxDeviceCustomElec(PhxElectricalDevice):
    def __init__(self) -> None:
        self.display_name = "User defined"
        super().__init__()
        self.device_type = ElectricEquipmentType.CUSTOM


class PhxDeviceCustomLighting(PhxElectricalDevice):
    """Override so that WUFI output quantity shows up as 1"""

    def __init__(self) -> None:
        self.display_name = "User defined - lighting"
        super().__init__()
        self.device_type = ElectricEquipmentType.CUSTOM_LIGHTING

    def get_energy_demand(self) -> float:
        if self.energy_demand is None:
            return 0
        return self.energy_demand * self.quantity

    def get_quantity(self) -> int:
        return 1


class PhxDeviceCustomMEL(PhxElectricalDevice):
    """Override so that WUFI output quantity shows up as 1"""

    def __init__(self) -> None:
        self.display_name = "User defined - Misc electrical loads"
        super().__init__()
        self.device_type = ElectricEquipmentType.CUSTOM_MEL

    def get_energy_demand(self) -> float:
        if self.energy_demand is None:
            return 0
        return self.energy_demand * self.quantity

    def get_quantity(self) -> int:
        return 1


class PhxElevatorHydraulic(PhxElectricalDevice):
    def __init__(self) -> None:
        self.display_name = "User defined - Misc electrical loads"
        super().__init__()
        self.device_type = ElectricEquipmentType.CUSTOM

    def get_energy_demand(self) -> float:
        if self.energy_demand is None:
            return 0
        return self.energy_demand * self.quantity

    def get_quantity(self) -> int:
        return 1


class PhxElevatorGearedTraction(PhxElectricalDevice):
    def __init__(self) -> None:
        self.display_name = "User defined - Misc electrical loads"
        super().__init__()
        self.device_type = ElectricEquipmentType.CUSTOM

    def get_energy_demand(self) -> float:
        if self.energy_demand is None:
            return 0
        return self.energy_demand * self.quantity

    def get_quantity(self) -> int:
        return 1


class PhxElevatorGearlessTraction(PhxElectricalDevice):
    def __init__(self) -> None:
        self.display_name = "User defined - Misc electrical loads"
        super().__init__()
        self.device_type = ElectricEquipmentType.CUSTOM

    def get_energy_demand(self) -> float:
        if self.energy_demand is None:
            return 0
        return self.energy_demand * self.quantity

    def get_quantity(self) -> int:
        return 1


# -----------------------------------------------------------------------------


def get_device_type_map() -> dict[ElectricEquipmentType, type[PhxElectricalDevice]]:
    """Returns a dictionary mapping all the device enum types to the PhxElectricalDevice classes.

    This is useful of you are building up new Devices from raw data or types inputs.
    """

    d = {}
    for _name, device_class in inspect.getmembers(sys.modules[__name__]):
        if not inspect.isclass(device_class):
            continue
        if not issubclass(device_class, PhxElectricalDevice):
            continue

        obj = device_class()
        d[obj.device_type] = device_class

    return d


# -----------------------------------------------------------------------------


@dataclass
class PhxElectricDeviceCollection:
    """A collection of all the PhxElectricalDevices (laundry, lighting, etc.) in the Zone"""

    _devices: dict = field(default_factory=dict)

    @property
    def devices(self) -> list[PhxElectricalDevice]:
        """Returns a list of all the devices in the PhxElectricDeviceCollection, sorted by display_name."""
        if not self._devices:
            return []
        return sorted(self._devices.values(), key=lambda e: e.display_name or "")

    def device_key_in_collection(self, _device_key) -> bool:
        """Returns True if the key supplied is in the existing device collection."""
        return _device_key in self._devices

    def get_equipment_by_key(self, _key: str) -> PhxElectricalDevice | None:
        return self._devices.get(_key, None)

    def add_new_device(self, _key: str, _device: PhxElectricalDevice) -> None:
        """Adds a new PHX Electric-Equipment device to the PhxElectricDeviceCollection.

        Arguments:
        ----------
            * _key (str): The key to use when storing the new electric-equipment
            * _devices (PhxElectricalDevice): The new PhxElectricalDevice to
                add to the collection.

        Returns:
        --------
            * None
        """
        self._devices[_key] = _device

    def __iter__(self):
        """Get each device in the PhxElectricDeviceCollection, one at a time."""
        yield from self.devices

    def __len__(self) -> int:
        """Number of devices in the PhxElectricDeviceCollection"""
        return len(self.devices)

    def __bool__(self) -> bool:
        return bool(self._devices)
