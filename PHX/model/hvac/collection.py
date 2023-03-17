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
from PHX.model.enums.hvac import DeviceType
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


class NoVentUnitFoundError(Exception):
    def __init__(self, _id_num):
        self.msg = f"Error: Cannot locate the Mechanical Device with id num: {_id_num}"
        super().__init__(self.msg)


@dataclass
class PhxZoneCoverage:
    """Percentage of the building load-type covered by the subsystem."""

    zone_num: float = 1.0
    heating: float = 1.0
    cooling: float = 1.0
    ventilation: float = 1.0
    humidification: float = 1.0
    dehumidification: float = 1.0


AnyMechDevice = Union[AnyPhxVentilation, AnyPhxHeater, AnyPhxCooling, AnyWaterTank]


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
    _distribution_piping_branches: Dict[str, hvac.PhxPipeElement] = field(default_factory=dict)
    _distribution_piping_recirc: Dict[str, hvac.PhxPipeElement] = field(default_factory=dict)
    _distribution_num_hw_tap_points: int = 1
    _distribution_ducting: Dict[str, hvac.PhxDuctElement] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def devices(self) -> List[AnyMechDevice]:
        return list(self._devices.values())

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
            weighted_total += phx_pipe_element.weighted_pipe_heat_loss_coefficient * phx_pipe_element.length_m
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
            weighted_total += phx_pipe_element.weighted_diameter_mm * phx_pipe_element.length_m
        return weighted_total / self.dhw_branch_total_length_m


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
        self._devices[_key] = _d

    def merge_all_devices(self):
        """Merge all the devices in the collection together by type."""
        kitchen_hood_devices = copy(self.kitchen_hood_devices)
        dryer_devices = copy(self.dryer_devices)
        user_determined_devices = copy(self.user_determined_devices)
        self.clear_all_devices()

        if kitchen_hood_devices:
            kitchen_hoods = reduce(lambda d1, d2: d1 + d2, kitchen_hood_devices)
            self.add_new_ventilator(kitchen_hoods.identifier, kitchen_hoods)

        if dryer_devices:
            dryers = reduce(lambda d1, d2: d1 + d2, dryer_devices)
            self.add_new_ventilator(dryers.identifier, dryers)

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
