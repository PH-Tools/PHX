# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Mechanical Collection Classes."""

from __future__ import annotations
from collections import defaultdict
from copy import copy
from dataclasses import dataclass, field
from functools import reduce
from typing import ClassVar, Dict, Optional, List, Any, Union

from PHX.model import hvac
from PHX.model.enums.hvac import DeviceType, PhxSupportiveDeviceType
from PHX.model.hvac.heating import AnyPhxHeater
from PHX.model.hvac.ventilation import (
    AnyPhxVentilation,
    AnyPhxExhaustVent,
    PhxExhaustVentilatorRangeHood,
    PhxExhaustVentilatorDryer,
    PhxExhaustVentilatorUserDefined,
)
from PHX.model.hvac.cooling import AnyPhxCooling
from PHX.model.hvac.water import AnyWaterTank
from PHX.model.hvac.piping import PhxRecirculationParameters
from PHX.model.hvac.supportive_devices import PhxSupportiveDevice
from PHX.model.hvac.renewable_devices import AnyRenewableDevice, PhxDevicePhotovoltaic


# ------------------------------------------------------------------------------


class NoVentUnitFoundError(Exception):
    def __init__(self, _id_num):
        self.msg = f"Error: Cannot locate the Mechanical Device with id num: {_id_num}"
        super().__init__(self.msg)


class NoSupportiveDeviceUnitFoundError(Exception):
    def __init__(self, _id_num):
        self.msg = f"Error: Cannot locate the Supportive Device with id num: {_id_num}"
        super().__init__(self.msg)


class NoRenewableDeviceUnitFoundError(Exception):
    def __init__(self, _id_num):
        self.msg = f"Error: Cannot locate the Renewable Device with id num: {_id_num}"
        super().__init__(self.msg)


# ------------------------------------------------------------------------------


@dataclass
class PhxZoneCoverage:
    """Percentage of the building load-type covered by the subsystem."""

    zone_num: int = 1
    heating: float = 1.0
    cooling: float = 1.0
    ventilation: float = 1.0
    humidification: float = 1.0
    dehumidification: float = 1.0


AnyMechDevice = Union[
    AnyPhxVentilation, AnyPhxHeater, AnyPhxCooling, AnyWaterTank, AnyRenewableDevice
]


# ------------------------------------------------------------------------------


@dataclass
class PhxRenewableDeviceCollection:
    """A Collection of PHX Renewable Energy Devices."""

    _count: ClassVar[int] = 0

    id_num: int = field(init=False, default=0)
    display_name: str = "Renewable Energy Device Collection"
    _devices: Dict[str, AnyRenewableDevice] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def devices(self) -> List[AnyRenewableDevice]:
        return list(self._devices.values())

    @property
    def pv_devices(self) -> List[PhxDevicePhotovoltaic]:
        """Return a List of all the Photovoltaic devices"""
        return [d for d in self.devices if d.device_type == DeviceType.PHOTOVOLTAIC]

    def clear_all_devices(self) -> None:
        """Reset the collection to an empty dictionary."""
        self._devices = {}

    def device_in_collection(self, _device_key) -> bool:
        """Return True if a PHX Renewable Device with the matching key is in the collection."""
        return _device_key in self._devices.keys()

    def get_device_by_key(self, _key: str) -> Optional[AnyRenewableDevice]:
        """Returns the PHX Renewable Device with the matching key, or None if not found.

        Arguments:
        ----------
            * _key (str): The key to search the collection for.

        Returns:
        --------
            * (Optional[PhxRenewableDevice]) The supportive device with
                the matching key, or None if not found.
        """
        return self._devices.get(_key, None)

    def get_device_by_id(self, _id_num: int) -> AnyRenewableDevice:
        """Returns a PHX Renewable Device from the collection which has a matching id-num.

        Arguments:
        ----------
            * _id_num (int): The Renewable Device id-number to search for.

        Returns:
        --------
            * (AnyRenewableDevice): The Renewable Device found with the
                matching ID-Number. Or Error if not found.
        """
        for device in self._devices.values():
            if device.id_num == _id_num:
                return device

        raise NoRenewableDeviceUnitFoundError(_id_num)

    def add_new_device(self, _key: str, _d: AnyRenewableDevice) -> None:
        """Adds a new PHX Supportive Device to the collection.

        Arguments:
        ----------
            * _key (str): The key to use when storing the new device
            * _device (AnyRenewableDevice): The new PHX Renewable Device
                to add to the collection.

        Returns:
        --------
            * None
        """
        if not _d:
            return
        self._devices[_key] = _d

    def group_devices_by_identifer(
        self, _devices: List[AnyRenewableDevice]
    ) -> Dict[str, List[AnyRenewableDevice]]:
        d = defaultdict(list)
        for device in _devices:
            d[device.identifier].append(copy(device))
        return d

    def merge_group_of_devices(
        self, _groups: Dict[str, List[AnyRenewableDevice]]
    ) -> List[AnyRenewableDevice]:
        """Merge a group of Dict of device-groups together into a single device."""
        merged_devices = []
        for group in _groups.values():
            merged_devices.append(reduce(lambda d1, d2: d1 + d2, group))
        return merged_devices

    def merge_all_devices(self) -> None:
        """Merge all the devices in the collection together by identifier."""
        pv_devices = self.group_devices_by_identifer(self.pv_devices)

        # -- start fresh
        self.clear_all_devices()

        # -- Merge, and add back the merged devices
        for device in self.merge_group_of_devices(pv_devices):
            self.add_new_device(device.identifier, device)

    def __iter__(self):
        """Get each device in the PhxRenewableDeviceCollection, one at a time."""
        for _ in self.devices:
            yield _

    def __len__(self) -> int:
        """Number of devices in the PhxRenewableDeviceCollection"""
        return len(self.devices)

    def __bool__(self) -> bool:
        return bool(self._devices)


@dataclass
class PhxSupportiveDeviceCollection:
    """A Collection of PHX Supportive Devices."""

    _count: ClassVar[int] = 0

    id_num: int = field(init=False, default=0)
    display_name: str = "Supportive Device Collection"
    _devices: Dict[str, PhxSupportiveDevice] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def devices(self) -> List[PhxSupportiveDevice]:
        return list(self._devices.values())

    @property
    def heat_circulating_pumps(self) -> List[PhxSupportiveDevice]:
        """Return a List of all the Kitchen Hood devices"""
        return [
            d
            for d in self.devices
            if d.device_type == PhxSupportiveDeviceType.HEAT_CIRCULATING_PUMP
        ]

    @property
    def dhw_circulating_pumps(self) -> List[PhxSupportiveDevice]:
        """Return a List of all the Kitchen Hood devices"""
        return [
            d
            for d in self.devices
            if d.device_type == PhxSupportiveDeviceType.DHW_CIRCULATING_PUMP
        ]

    @property
    def dhw_storage_pumps(self) -> List[PhxSupportiveDevice]:
        """Return a List of all the Kitchen Hood devices"""
        return [
            d
            for d in self.devices
            if d.device_type == PhxSupportiveDeviceType.DHW_STORAGE_LOAD_PUMP
        ]

    @property
    def other_devices(self) -> List[PhxSupportiveDevice]:
        """Return a List of all the Kitchen Hood devices"""
        return [d for d in self.devices if d.device_type == PhxSupportiveDeviceType.OTHER]

    def clear_all_devices(self) -> None:
        """Reset the collection to an empty dictionary."""
        self._devices = {}

    def device_in_collection(self, _device_key) -> bool:
        """Return True if a PHX Supportive Device with the matching key is in the collection."""
        return _device_key in self._devices.keys()

    def get_device_by_key(self, _key: str) -> Optional[PhxSupportiveDevice]:
        """Returns the PHX Supportive Device with the matching key, or None if not found.

        Arguments:
        ----------
            * _key (str): The key to search the collection for.

        Returns:
        --------
            * (Optional[PhxSupportiveDevice]) The supportive device with
                the matching key, or None if not found.
        """
        return self._devices.get(_key, None)

    def get_device_by_id(self, _id_num: int) -> PhxSupportiveDevice:
        """Returns a PHX Supportive Device from the collection which has a matching id-num.

        Arguments:
        ----------
            * _id_num (int): The Supportive Device id-number to search for.

        Returns:
        --------
            * (PhxSupportiveDevice): The Supportive Device found with the
                matching ID-Number. Or Error if not found.
        """
        for device in self._devices.values():
            if device.id_num == _id_num:
                return device

        raise NoSupportiveDeviceUnitFoundError(_id_num)

    def add_new_device(self, _key: str, _d: PhxSupportiveDevice) -> None:
        """Adds a new PHX Supportive Device to the collection.

        Arguments:
        ----------
            * _key (str): The key to use when storing the new device
            * _device (hvac.ventilation.AnyPhxExhaustVent): The new PHX Supportive Device
                to add to the collection.

        Returns:
        --------
            * None
        """
        if not _d:
            return
        self._devices[_key] = _d

    def group_devices_by_identifer(
        self, _devices: List[PhxSupportiveDevice]
    ) -> Dict[str, List[PhxSupportiveDevice]]:
        d = defaultdict(list)
        for device in _devices:
            d[device.identifier].append(copy(device))
        return d

    def merge_group_of_devices(
        self, _groups: Dict[str, List[PhxSupportiveDevice]]
    ) -> List[PhxSupportiveDevice]:
        """Merge a group of Dict of device-groups together into a single device."""
        merged_devices = []
        for group in _groups.values():
            merged_devices.append(reduce(lambda d1, d2: d1 + d2, group))
        return merged_devices

    def merge_all_devices(self) -> None:
        """Merge all the devices in the collection together by identifier."""
        heat_circulating_pumps = self.group_devices_by_identifer(
            self.heat_circulating_pumps
        )
        dhw_circulating_pumps = self.group_devices_by_identifer(
            self.dhw_circulating_pumps
        )
        dhw_storage_pumps = self.group_devices_by_identifer(self.dhw_storage_pumps)
        others = self.group_devices_by_identifer(self.other_devices)

        # -- start fresh
        self.clear_all_devices()

        # -- Merge, and add back the merged devices
        for device in self.merge_group_of_devices(heat_circulating_pumps):
            self.add_new_device(device.identifier, device)
        for device in self.merge_group_of_devices(dhw_circulating_pumps):
            self.add_new_device(device.identifier, device)
        for device in self.merge_group_of_devices(dhw_storage_pumps):
            self.add_new_device(device.identifier, device)
        for device in self.merge_group_of_devices(others):
            self.add_new_device(device.identifier, device)

    def __iter__(self):
        """Get each device in the PhxSupportiveDeviceCollection, one at a time."""
        for _ in self.devices:
            yield _

    def __len__(self) -> int:
        """Number of devices in the PhxSupportiveDeviceCollection"""
        return len(self.devices)

    def __bool__(self) -> bool:
        return bool(self._devices)


@dataclass
class PhxExhaustVentilatorCollection:
    """A Collection of PHX Exhaust Ventilation Devices."""

    _count: ClassVar[int] = 0

    id_num: int = field(init=False, default=0)
    display_name: str = "Exhaust Ventilator Collection"
    _devices: Dict[str, AnyPhxExhaustVent] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def devices(self) -> List[AnyPhxExhaustVent]:
        return list(self._devices.values())

    @property
    def kitchen_hood_devices(self) -> List[PhxExhaustVentilatorRangeHood]:
        """Return a List of all the Kitchen Hood devices"""
        return [d for d in self.devices if isinstance(d, PhxExhaustVentilatorRangeHood)]

    @property
    def dryer_devices(self) -> List[PhxExhaustVentilatorDryer]:
        """Return a List of all the Dryer devices"""
        return [d for d in self.devices if isinstance(d, PhxExhaustVentilatorDryer)]

    @property
    def user_determined_devices(self) -> List[PhxExhaustVentilatorUserDefined]:
        """Return a List of all the User-Determined devices"""
        return [d for d in self.devices if isinstance(d, PhxExhaustVentilatorUserDefined)]

    def clear_all_devices(self) -> None:
        """Reset the collection to an empty dictionary."""
        self._devices = {}

    def device_in_collection(self, _device_key) -> bool:
        """Return True if a PHX Exhaust Ventilator with the matching key is in the collection."""
        return _device_key in self._devices.keys()

    def get_ventilator_by_key(self, _key: str) -> Optional[AnyPhxExhaustVent]:
        """Returns the PHX Exhaust Ventilator with the matching key, or None if not found.

        Arguments:
        ----------
            * _key (str): The key to search the collection for.

        Returns:
        --------
            * (Optional[hvac.ventilation.AnyPhxExhaustVent]) The Mechanical device with
                the matching key, or None if not found.
        """
        return self._devices.get(_key, None)

    def get_ventilator_by_id(self, _id_num: int) -> AnyPhxExhaustVent:
        """Returns a PHX Exhaust Ventilator from the collection which has a matching id-num.

        Arguments:
        ----------
            * _id_num (int): The Exhaust Ventilator id-number to search for.

        Returns:
        --------
            * (hvac.ventilation.AnyPhxExhaustVent): The Exhaust Ventilator found with the
                matching ID-Number. Or Error if not found.
        """
        for device in self._devices.values():
            if device.id_num == _id_num:
                return device

        raise NoVentUnitFoundError(_id_num)

    def add_new_ventilator(self, _key: str, _d: AnyPhxExhaustVent) -> None:
        """Adds a new PHX Exhaust Ventilator to the collection.

        Arguments:
        ----------
            * _key (str): The key to use when storing the new mechanical device
            * _device (hvac.ventilation.AnyPhxExhaustVent): The new PHX exhaust ventilator
                to add to the collection.

        Returns:
        --------
            * None
        """
        if not _d:
            return
        self._devices[_key] = _d

    def merge_all_devices(self):
        """Merge all the devices in the collection together by type."""
        # -- Keep a copy of the devices the collection started with
        kitchen_hood_devices = copy(self.kitchen_hood_devices)
        dryer_devices = copy(self.dryer_devices)
        user_determined_devices = copy(self.user_determined_devices)

        # -- start fresh
        self.clear_all_devices()

        # -- Add back the merged devices
        if kitchen_hood_devices:
            kitchen_hood = reduce(lambda d1, d2: d1 + d2, kitchen_hood_devices)
            self.add_new_ventilator(kitchen_hood.identifier, kitchen_hood)

        if dryer_devices:
            dryer = reduce(lambda d1, d2: d1 + d2, dryer_devices)
            self.add_new_ventilator(dryer.identifier, dryer)

        if user_determined_devices:
            ud_devices = reduce(lambda d1, d2: d1 + d2, user_determined_devices)
            self.add_new_ventilator(ud_devices.identifier, ud_devices)

    def __iter__(self):
        """Get each device in the PhxExhaustVentilatorCollection, one at a time."""
        for _ in self.devices:
            yield _

    def __len__(self) -> int:
        """Number of devices in the PhxExhaustVentilatorCollection"""
        return len(self.devices)

    def __bool__(self) -> bool:
        return bool(self._devices)


# ------------------------------------------------------------------------------


@dataclass
class PhxMechanicalSystemCollection:
    """A Collection of all the mechanical devices (heating, cooling, etc) and distribution in the project"""

    _count: ClassVar[int] = 0

    id_num: int = field(init=False, default=0)
    display_name: str = "Ideal Air System"
    sys_type_num: int = 1
    sys_type_str: str = "User defined (ideal system)"
    zone_coverage: PhxZoneCoverage = field(default_factory=PhxZoneCoverage)

    _devices: Dict[str, AnyMechDevice] = field(default_factory=dict)
    _distribution_hw_recirculation_params: PhxRecirculationParameters = field(
        default_factory=PhxRecirculationParameters
    )
    _distribution_piping_branches: Dict[str, hvac.PhxPipeElement] = field(
        default_factory=dict
    )
    _distribution_piping_recirc: Dict[str, hvac.PhxPipeElement] = field(
        default_factory=dict
    )
    _distribution_num_hw_tap_points: int = 1
    _distribution_ducting: Dict[str, hvac.PhxDuctElement] = field(default_factory=dict)

    supportive_devices: PhxSupportiveDeviceCollection = field(
        default_factory=PhxSupportiveDeviceCollection
    )
    renewable_devices: PhxRenewableDeviceCollection = field(
        default_factory=PhxRenewableDeviceCollection
    )

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    # -------------------------------------------------------------------------
    #  -- Mechanical Devices

    @property
    def devices(self) -> List[AnyMechDevice]:
        """Returns a list of the 'devices' in the collection."""
        return list(sorted(self._devices.values(), key=lambda d: d.identifier))

    def device_in_collection(self, _device_key) -> bool:
        """Return True if the a Mech device with the matching key is already in the collection."""
        return _device_key in self._devices.keys()

    def get_mech_device_by_key(self, _key: str) -> Optional[hvac.PhxMechanicalDevice]:
        """Returns the mechanical device with the matching key, or None if not found.

        Arguments:
        ----------
            * _key (str): The key to search the collection for.

        Returns:
        --------
            * (Optional[hvac.PhxMechanicalDevice]) The Mechanical device with
                the matching key, or None if not found.
        """
        return self._devices.get(_key, None)

    def get_mech_device_by_id(self, _id_num: int) -> hvac.PhxMechanicalDevice:
        """Returns a Mechanical Device from the collection which has a matching id-num.

        Arguments:
        ----------
            * _id_num (int): The Mechanical Device id-number to search for.

        Returns:
        --------
            * (hvac.PhxMechanicalDevice): The Mechanical Device found with the
                matching ID-Number. Or Error if not found.
        """
        for device in self._devices.values():
            if device.id_num == _id_num:
                return device

        raise NoVentUnitFoundError(_id_num)

    def add_new_mech_device(self, _key: str, _d: AnyMechDevice) -> None:
        """Adds a new PHX Mechanical device to the collection.

        Arguments:
        ----------
            * _key (str): The key to use when storing the new mechanical device
            * _device (_base.PhxMechanicalDevice): The new PHX mechanical device to
                add to the collection.

        Returns:
        --------
            * None
        """
        self._devices[_key] = _d

    # -------------------------------------------------------------------------
    #  -- Distribution Piping and Ducting

    def add_branch_piping(self, _p: hvac.PhxPipeElement) -> None:
        self._distribution_piping_branches[_p.identifier] = _p

    def add_recirc_piping(self, _p: hvac.PhxPipeElement) -> None:
        self._distribution_piping_recirc[_p.identifier] = _p

    def add_vent_ducting(self, _d: hvac.PhxDuctElement) -> None:
        self._distribution_ducting[_d.identifier] = _d

    @property
    def ventilation_devices(self) -> List[hvac.AnyPhxVentilation]:
        """Returns a list of the 'Ventilation' devices in the collection."""
        return [
            _
            for _ in self.devices
            if isinstance(_, hvac.PhxDeviceVentilation) and _.usage_profile.ventilation
        ]

    @property
    def space_heating_devices(self) -> List[hvac.AnyPhxHeater]:
        """Returns a list of the 'Space Heating' devices in the collection."""
        return [
            _
            for _ in self.devices
            if isinstance(_, hvac.PhxHeatingDevice) and _.usage_profile.space_heating
        ]

    @property
    def cooling_devices(self) -> List[hvac.AnyPhxCooling]:
        """Returns a list of all the 'Cooling' devices in the collection."""
        return [
            _
            for _ in self.devices
            if isinstance(_, hvac.PhxCoolingDevice) and _.usage_profile.cooling
        ]

    @property
    def dhw_heating_devices(self) -> List[hvac.AnyPhxHeater]:
        """Returns a list of only the 'DHW Heating' devices (no tanks) in the collection."""
        return [
            _
            for _ in self.devices
            if isinstance(_, hvac.PhxHeatingDevice)
            and _.usage_profile.dhw_heating
            and _.device_type != DeviceType.WATER_STORAGE
        ]

    @property
    def dhw_tank_devices(self) -> List[hvac.AnyWaterTank]:
        """Returns a list of only the 'DHW Storage Tank' devices (no heaters) in the collection."""
        return [
            _
            for _ in self.devices
            if isinstance(_, hvac.PhxHotWaterTank)
            and _.usage_profile.dhw_heating
            and _.device_type == DeviceType.WATER_STORAGE
        ]

    @property
    def dhw_branch_piping(self) -> List[hvac.PhxPipeElement]:
        """Returns a list of all the DHW branch-piping in the collection."""
        return list(self._distribution_piping_branches.values())

    @property
    def dhw_branch_piping_segments_by_diam(self) -> List[List[hvac.PhxPipeSegment]]:
        """Returns a list of the DHW branch-piping segments, grouped by diameter."""
        # -- Group piping segments by diameter
        d: Dict[float, List[hvac.PhxPipeSegment]] = defaultdict(list)
        for pipe in self.dhw_branch_piping:
            for segment in pipe.segments:
                d[segment.diameter_m].append(segment)

        return list(d.values())

    @property
    def dhw_recirc_piping(self) -> List[hvac.PhxPipeElement]:
        """Returns a list of all the DHW recirculation-piping in the collection."""
        return list(self._distribution_piping_recirc.values())

    @property
    def dhw_recirc_piping_segments_by_diam(self) -> List[List[hvac.PhxPipeSegment]]:
        """Returns a list of the DHW recirculation-piping segments, grouped by diameter."""
        # -- Group piping segments by diameter
        d: Dict[float, List[hvac.PhxPipeSegment]] = defaultdict(list)
        for pipe in self.dhw_recirc_piping:
            for segment in pipe.segments:
                d[segment.diameter_m].append(segment)

        return list(d.values())

    @property
    def vent_ducting(self) -> List[hvac.PhxDuctElement]:
        """Returns a list of all the Vent. Ducting in the collection."""
        return list(self._distribution_ducting.values())

    @property
    def dhw_recirc_total_length_m(self) -> float:
        return sum(_.length_m for _ in self.dhw_recirc_piping)

    @property
    def dhw_recirc_weighted_heat_loss_coeff(self) -> Optional[float]:
        """Return a length-weighted average pipe heat-loss coefficient."""
        if not self.dhw_recirc_total_length_m:
            return None

        weighted_total = 0.0
        for phx_pipe_element in self.dhw_recirc_piping:
            weighted_total += (
                phx_pipe_element.weighted_pipe_heat_loss_coefficient
                * phx_pipe_element.length_m
            )
        return weighted_total / self.dhw_recirc_total_length_m

    @property
    def dhw_branch_total_length_m(self) -> float:
        return sum(_.length_m for _ in self.dhw_branch_piping)

    @property
    def dhw_branch_weighted_diameter_mm(self) -> Optional[float]:
        """Return a length-weighted average diameter."""
        if not self.dhw_branch_total_length_m:
            return None

        weighted_total = 0.0
        for phx_pipe_element in self.dhw_branch_piping:
            weighted_total += (
                phx_pipe_element.weighted_diameter_mm * phx_pipe_element.length_m
            )
        return weighted_total / self.dhw_branch_total_length_m
