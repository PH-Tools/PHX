# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX  Mechanical Collection Classes."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Optional, List, Any, Union
from collections import defaultdict

from PHX.model import hvac
from PHX.model.enums.hvac import DeviceType
from PHX.model.hvac.heating import AnyPhxHeater
from PHX.model.hvac.ventilation import AnyPhxVentilation
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
    """A collection of all the mechanical devices (heating, cooling, etc) and distribution in the project"""

    _count: ClassVar[int] = 0

    id_num: int = field(init=False, default=0)
    display_name: str = "Ideal Air System"
    sys_type_num: int = 1
    sys_type_str: str = "User defined (ideal system)"
    zone_coverage: PhxZoneCoverage = field(default_factory=PhxZoneCoverage)

    _devices: Dict[str, AnyMechDevice] = field(default_factory=dict)
    _distribution_piping_branches: Dict[str, Any] = field(default_factory=dict)
    _distribution_num_hw_tap_points: int = 1
    _distribution_piping_recirc: Dict[str, Any] = field(default_factory=dict)
    _distribution_ducting: Dict[str, Any] = field(default_factory=dict)

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
                d[segment.diameter].append(segment)

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
                d[segment.diameter].append(segment)

        return list(d.values())
