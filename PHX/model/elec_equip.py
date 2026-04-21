# -*- Python Version: 3.10 -*-

"""PHX Passive House electrical equipment (appliance) classes for energy demand and IHG calculations."""

import inspect
import logging
import sys
import uuid
from dataclasses import dataclass, field
from typing import ClassVar

from PHX.model.enums.elec_equip import ElectricEquipmentType

logger = logging.getLogger(__name__)


@dataclass
class PhxElectricalDevice:
    """Base class for all PHX electrical equipment (dishwashers, laundry, lighting, etc.).

    Subclassed by device-specific types that set appropriate defaults for device_type,
    energy demand, and internal heat gain (IHG) utilization factors. Used by the WUFI
    and PHPP exporters to write appliance-level energy demand and IHG contributions.

    Attributes:
        identifier (uuid.UUID | str): Unique identifier for the device.
        display_name (str | None): User-facing name for the device. Default: "_unnamed_equipment_".
        comment (str | None): Optional descriptive comment. Default: "".
        in_conditioned_space (bool | None): Whether the device is inside the thermal envelope. Default: True.
        energy_demand (float | None): Annual energy demand [kWh/a]. Default: 100.0.
        energy_demand_per_use (float | None): Energy demand per use cycle [kWh/use]. Default: 100.0.
        combined_energy_factor (float | None): Combined energy factor for the device. Default: 0.0.
        ihg_utilization_factor (float): Fraction of energy demand that becomes internal heat gain (0.0-1.0).
            Default: 1.0.
        device_type (ElectricEquipmentType): The equipment type enum. Default: CUSTOM.
    """

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
    ihg_utilization_factor: float = 1.0

    device_type: ElectricEquipmentType = field(default=ElectricEquipmentType.CUSTOM)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def reference_quantity(self) -> int:
        """The reference quantity used for energy-demand normalization."""
        return self._reference_quantity

    @reference_quantity.setter
    def reference_quantity(self, value: int | None) -> None:
        if value is not None:
            self._reference_quantity = int(value)

    @property
    def reference_energy_norm(self) -> int:
        """The reference energy normalization standard for the device."""
        return self._reference_energy_norm

    @reference_energy_norm.setter
    def reference_energy_norm(self, value: int | None) -> None:
        if value is not None:
            self._reference_energy_norm = value

    @property
    def quantity(self) -> int:
        """The number of this device in the zone."""
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
    """A kitchen dishwasher appliance.

    Attributes:
        capacity (float | None): Rated capacity of the dishwasher [place settings]. Default: 1.0.
    """

    def __init__(self) -> None:
        super().__init__()
        self._water_connection: int = 1  # DHW Connection
        self._capacity_type: int = 1
        self.display_name = "Kitchen Dishwasher"
        self.capacity: float | None = 1.0
        self.device_type = ElectricEquipmentType.DISHWASHER
        self.ihg_utilization_factor = 0.30

    @property
    def water_connection(self) -> int | None:
        """The DHW connection type for the dishwasher."""
        return self._water_connection

    @water_connection.setter
    def water_connection(self, value: int | None) -> None:
        if value is not None:
            self._water_connection = value

    @property
    def capacity_type(self) -> int | None:
        """The capacity type classification for the dishwasher."""
        return self._capacity_type

    @capacity_type.setter
    def capacity_type(self, value: int | None) -> None:
        if value is not None:
            self._capacity_type = value


class PhxDeviceClothesWasher(PhxElectricalDevice):
    """A clothes washing machine appliance.

    Attributes:
        capacity (float | None): Drum capacity [m3]. Default: 0.0814.
        modified_energy_factor (float | None): Modified Energy Factor (MEF) per DOE test procedure.
            Default: 2.38.
        utilization_factor (float | None): Usage utilization factor. Default: 1.0.
    """

    def __init__(self) -> None:
        super().__init__()
        self.display_name = "Laundry - washer"
        self._water_connection: int = 1  # DHW Connection

        self.capacity: float | None = 0.0814  # m3
        self.modified_energy_factor: float | None = 2.38
        self.utilization_factor: float | None = 1.0
        self.device_type = ElectricEquipmentType.CLOTHES_WASHER
        self.ihg_utilization_factor = 0.30

    @property
    def water_connection(self) -> int | None:
        """The DHW connection type for the clothes washer."""
        return self._water_connection

    @water_connection.setter
    def water_connection(self, value: int | None) -> None:
        if value is not None:
            self._water_connection = value


class PhxDeviceClothesDryer(PhxElectricalDevice):
    """A clothes dryer appliance (electric or gas).

    Attributes:
        gas_consumption (float | None): Annual gas consumption [kWh]. Default: 0.0.
        gas_efficiency_factor (float | None): Gas energy efficiency factor. Default: 2.67.
        field_utilization_factor (float | None): Field utilization factor for in-situ performance. Default: 1.18.
    """

    def __init__(self) -> None:
        super().__init__()
        self.display_name = "Laundry - dryer"
        self._dryer_type: int = 4  # Condensation dryer
        self._field_utilization_factor_type: int = 1  # Timer

        self.gas_consumption: float | None = 0.0  # kWh
        self.gas_efficiency_factor: float | None = 2.67
        self.field_utilization_factor: float | None = 1.18
        self.device_type = ElectricEquipmentType.CLOTHES_DRYER
        self.ihg_utilization_factor = 0.70

    @property
    def dryer_type(self) -> int:
        """The dryer type classification (e.g., 4 = condensation dryer)."""
        return self._dryer_type

    @dryer_type.setter
    def dryer_type(self, value: int | None) -> None:
        if value is not None:
            self._dryer_type = value

    @property
    def field_utilization_factor_type(self) -> int | None:
        """The field utilization factor type (e.g., 1 = timer)."""
        return self._field_utilization_factor_type

    @field_utilization_factor_type.setter
    def field_utilization_factor_type(self, value: int | None) -> None:
        if value is not None:
            self._field_utilization_factor_type = value


class PhxDeviceRefrigerator(PhxElectricalDevice):
    """A standalone kitchen refrigerator (no freezer compartment)."""

    def __init__(self) -> None:
        super().__init__()
        self.display_name = "Kitchen refrigerator"
        self.device_type = ElectricEquipmentType.REFRIGERATOR


class PhxDeviceFreezer(PhxElectricalDevice):
    """A standalone kitchen freezer."""

    def __init__(self) -> None:
        super().__init__()
        self.display_name = "kitchen freezer"
        self.device_type = ElectricEquipmentType.FREEZER


class PhxDeviceFridgeFreezer(PhxElectricalDevice):
    """A combined refrigerator/freezer unit."""

    def __init__(self) -> None:
        super().__init__()
        self.display_name = "Kitchen fridge/freeze combo"
        self.device_type = ElectricEquipmentType.FRIDGE_FREEZER


class PhxDeviceCooktop(PhxElectricalDevice):
    """A kitchen cooktop appliance (electric or gas)."""

    def __init__(self):
        super().__init__()
        self.display_name = "Kitchen cooking"
        self._cooktop_type: int = 1  # Electric
        self.device_type = ElectricEquipmentType.COOKING
        self.ihg_utilization_factor = 0.50

    @property
    def cooktop_type(self) -> int:
        """The cooktop fuel type (e.g., 1 = electric)."""
        return self._cooktop_type

    @cooktop_type.setter
    def cooktop_type(self, value: int | None) -> None:
        if value is not None:
            self._cooktop_type = value


class PhxDeviceMEL(PhxElectricalDevice):
    """Miscellaneous electrical loads (MEL) per the Phius protocol."""

    def __init__(self) -> None:
        super().__init__()
        self.display_name = "PHIUS+ MELS"
        self.device_type = ElectricEquipmentType.MEL


class PhxDeviceLightingInterior(PhxElectricalDevice):
    """Interior lighting per the Phius protocol.

    Attributes:
        frac_high_efficiency (float | None): Fraction of high-efficiency luminaires (0.0-1.0). Default: 1.0.
    """

    def __init__(self) -> None:
        super().__init__()
        self.display_name = "PHIUS+ Interior Lighting"
        self.frac_high_efficiency: float | None = 1.0
        self.device_type = ElectricEquipmentType.LIGHTING_INTERIOR


class PhxDeviceLightingExterior(PhxElectricalDevice):
    """Exterior lighting per the Phius protocol (outside the thermal envelope).

    Attributes:
        frac_high_efficiency (float | None): Fraction of high-efficiency luminaires (0.0-1.0). Default: 1.0.
    """

    def __init__(self) -> None:
        super().__init__()
        self.display_name = "PHIUS+ Exterior Lighting"
        self.frac_high_efficiency: float | None = 1.0
        self.device_type = ElectricEquipmentType.LIGHTING_EXTERIOR
        self.in_conditioned_space = False


class PhxDeviceLightingGarage(PhxElectricalDevice):
    """Garage lighting per the Phius protocol (outside the thermal envelope).

    Attributes:
        frac_high_efficiency (float | None): Fraction of high-efficiency luminaires (0.0-1.0). Default: 1.0.
    """

    def __init__(self) -> None:
        super().__init__()
        self.display_name = "PHIUS+ Garage Lighting"
        self.frac_high_efficiency: float | None = 1.0
        self.device_type = ElectricEquipmentType.LIGHTING_GARAGE
        self.in_conditioned_space = False


class PhxDeviceCustomElec(PhxElectricalDevice):
    """A user-defined custom electrical device."""

    def __init__(self) -> None:
        self.display_name = "User defined"
        super().__init__()
        self.device_type = ElectricEquipmentType.CUSTOM


class PhxDeviceCustomLighting(PhxElectricalDevice):
    """A user-defined custom lighting device.

    Overrides get_energy_demand to multiply by quantity and get_quantity to always
    return 1, so WUFI output shows the total demand on a single line item.
    """

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
    """A user-defined custom miscellaneous electrical load (MEL).

    Overrides get_energy_demand to multiply by quantity and get_quantity to always
    return 1, so WUFI output shows the total demand on a single line item.
    """

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
    """A hydraulic elevator, modeled as a custom electrical device for energy demand."""

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
    """A geared-traction elevator, modeled as a custom electrical device for energy demand."""

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
    """A gearless-traction elevator, modeled as a custom electrical device for energy demand."""

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
    """A collection of all the PhxElectricalDevices (laundry, lighting, etc.) in a Zone.

    Stores devices by key and provides sorted iteration and key-based lookup.
    """

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
        """Return the device matching the given key, or None if not found.

        Arguments:
        ----------
            * _key (str): The lookup key for the device.

        Returns:
        --------
            * PhxElectricalDevice | None: The matching device, or None.
        """
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
        replacing_existing = _key in self._devices
        self._devices[_key] = _device
        logger.debug(
            "Zone HomeDevice collection upsert: key='%s' replacing=%s class='%s' identifier='%s' total_devices=%s",
            _key,
            replacing_existing,
            _device.__class__.__name__,
            getattr(_device, "identifier", None),
            len(self._devices),
        )

    def __iter__(self):
        """Get each device in the PhxElectricDeviceCollection, one at a time."""
        yield from self.devices

    def __len__(self) -> int:
        """Number of devices in the PhxElectricDeviceCollection"""
        return len(self.devices)

    def __bool__(self) -> bool:
        return bool(self._devices)
