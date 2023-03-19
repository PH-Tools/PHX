# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Passive House Electrical Equipment (Appliances) Classes"""

from typing import Optional, ClassVar, Union, List
from dataclasses import dataclass, field
import uuid


@dataclass
class PhxElectricalDevice:
    """Base class for PHX Electrical Equipment (dishwashers, laundry, lighting, etc.)"""

    _count: ClassVar[int] = 0

    identifier: Union[uuid.UUID, str] = field(default_factory=uuid.uuid4)
    display_name: str = "_unnamed_equipment_"
    id_num: int = field(init=False, default=0)
    comment: str = ""
    reference_quantity: int = 1
    quantity: int = 1
    in_conditioned_space: bool = True
    reference_energy_norm: int = 2
    energy_demand: float = 100
    energy_demand_per_use: float = 100
    combined_energy_factor: float = 0

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    def get_energy_demand(self) -> float:
        """To allow for subclass custom behavior. Cannot use @property since 
        it will not work with __setattr__ which is used during HBPH->PHX object creation.
        """
        return self.energy_demand
    
    def get_quantity(self) -> int:
        """To allow for subclass custom behavior. Cannot use @property since 
        it will not work with __setattr__ which is used during HBPH->PHX object creation.
        """
        return self.quantity


class PhxDeviceDishwasher(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "Kitchen Dishwasher"
        self.capacity_type: int = 1
        self.capacity: float = 1
        self.water_connection: int = 1  # DHW Connection


class PhxDeviceClothesWasher(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "Laundry - washer"
        self.capacity: float = 0.0814  # m3
        self.modified_energy_factor: float = 2.38
        self.water_connection: int = 1  # DHW Connection
        self.utilization_factor: float = 1


class PhxDeviceClothesDryer(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "Laundry - dryer"
        self.dryer_type: int = 4  # Condensation dryer
        self.gas_consumption: float = 0  # kWh
        self.gas_efficiency_factor: float = 2.67
        self.field_utilization_factor_type: int = 1  # Timer
        self.field_utilization_factor: float = 1.18


class PhxDeviceRefrigerator(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "Kitchen refrigerator"


class PhxDeviceFreezer(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "kitchen freezer"


class PhxDeviceFridgeFreezer(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "Kitchen fridge/freeze combo"


class PhxDeviceCooktop(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "Kitchen cooking"
        self.cooktop_type: int = 1  # Electric


class PhxDeviceMEL(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "PHIUS+ MELS"


class PhxDeviceLightingInterior(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "PHIUS+ Interior Lighting"
        self.frac_high_efficiency: float = 1.0


class PhxDeviceLightingExterior(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "PHIUS+ Exterior Lighting"
        self.frac_high_efficiency: float = 1.0


class PhxDeviceLightingGarage(PhxElectricalDevice):
    def __init__(self):
        super().__init__()
        self.display_name = "PHIUS+ Garage Lighting"
        self.frac_high_efficiency: float = 1.0


class PhxDeviceCustomElec(PhxElectricalDevice):
    def __init__(self):
        self.display_name = "User defined"
        super().__init__()


class PhxDeviceCustomLighting(PhxElectricalDevice):
    """Override so that WUFI output quantity shows up as 1"""
    
    def __init__(self):
        self.display_name = "User defined - lighting"
        super().__init__()
    
    def get_energy_demand(self) -> float:
        return self.energy_demand * self.quantity
    
    def get_quantity(self) -> int:
        return 1


class PhxDeviceCustomMEL(PhxElectricalDevice):
    """Override so that WUFI output quantity shows up as 1"""

    def __init__(self):
        self.display_name = "User defined - Misc electrical loads"
        super().__init__()
    
    def get_energy_demand(self) -> float:
        return self.energy_demand * self.quantity
    
    def get_quantity(self) -> int:
        return 1


class PhxElevatorHydraulic(PhxElectricalDevice):
    
    def __init__(self):
        self.display_name = "User defined - Misc electrical loads"
        super().__init__()
    
    def get_energy_demand(self) -> float:
        return self.energy_demand * self.quantity
    
    def get_quantity(self) -> int:
        return 1
    
class PhxElevatorGearedTraction(PhxElectricalDevice):
    
    def __init__(self):
        self.display_name = "User defined - Misc electrical loads"
        super().__init__()
    
    def get_energy_demand(self) -> float:
        return self.energy_demand * self.quantity
    
    def get_quantity(self) -> int:
        return 1  
    
class PhxElevatorGearlessTraction(PhxElectricalDevice):
    
    def __init__(self):
        self.display_name = "User defined - Misc electrical loads"
        super().__init__()

    def get_energy_demand(self) -> float:
        return self.energy_demand * self.quantity
    
    def get_quantity(self) -> int:
        return 1
    
# -----------------------------------------------------------------------------


@dataclass
class PhxElectricDeviceCollection:
    """A collection of all the PhxElectricalDevices (laundry, lighting, etc.) in the Zone"""

    _devices: dict = field(default_factory=dict)

    @property
    def devices(self) -> List[PhxElectricalDevice]:
        """Returns a list of all the devices in the PhxElectricDeviceCollection, sorted by display_name."""
        if not self._devices:
            return []
        return sorted(self._devices.values(), key=lambda e: e.display_name)

    def device_key_in_collection(self, _device_key) -> bool:
        """Returns True if the key supplied is in the existing device collection."""
        return _device_key in self._devices.keys()

    def get_equipment_by_key(self, _key: str) -> Optional[PhxElectricalDevice]:
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
        for _ in self.devices:
            yield _

    def __len__(self) -> int:
        """Number of devices in the PhxElectricDeviceCollection"""
        return len(self.devices)

    def __bool__(self) -> bool:
        return bool(self._devices)
