# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Building Classes"""

from __future__ import annotations
from typing import ClassVar, List, Sequence, Union, Set, Dict, ValuesView, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from functools import reduce
import operator

from PHX.model import elec_equip, geometry, spaces
from PHX.model.components import (
    PhxComponentAperture,
    PhxComponentOpaque,
    PhxComponentThermalBridge,
)
from PHX.model.hvac import collection
from PHX.model.programs import occupancy
from PHX.model.enums.building import SpecificHeatCapacity

@dataclass
class PhxZone:
    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    display_name: str = ""
    volume_gross: float = 0.0
    volume_net: float = 0.0
    weighted_net_floor_area: float = 0.0
    clearance_height: float = 2.5
    specific_heat_capacity: SpecificHeatCapacity = SpecificHeatCapacity.LIGHTWEIGHT
    spaces: List[spaces.PhxSpace] = field(default_factory=list)
    elec_equipment_collection: elec_equip.PhxElectricDeviceCollection = field(
        default_factory=elec_equip.PhxElectricDeviceCollection
    )
    res_occupant_quantity: float = 0.0
    res_number_bedrooms: int = 0
    res_number_dwellings: int = 0
    exhaust_ventilator_collection: collection.PhxExhaustVentilatorCollection = field(
        default_factory=collection.PhxExhaustVentilatorCollection
    )
    _thermal_bridges: Dict[str, PhxComponentThermalBridge] = field(default_factory=dict)
    occupancy: Optional[occupancy.PhxProgramOccupancy] = None
    lighting: Any = None

    def add_thermal_bridges(
        self,
        _thermal_bridges: Union[
            PhxComponentThermalBridge, Sequence[PhxComponentThermalBridge]
        ],
    ) -> None:
        """Add a new PhxComponentThermalBridge (or list of Bridges) to the PhxZone."""
        if not isinstance(_thermal_bridges, Sequence):
            _thermal_bridges = (_thermal_bridges,)

        for tb in _thermal_bridges:
            self._thermal_bridges[tb.identifier] = tb

        return None

    @property
    def thermal_bridges(self) -> ValuesView[PhxComponentThermalBridge]:
        """Return all of the PhxComponentThermalBridge objects in the PhxZone."""
        return self._thermal_bridges.values()

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count


@dataclass
class PhxBuilding:
    _components: List[PhxComponentOpaque] = field(default_factory=list)
    zones: List[PhxZone] = field(default_factory=list)

    @property
    def weighted_net_floor_area(self) -> float:
        """Returns the total weighted net floor area of all zones in the PhxBuilding."""
        return sum(z.weighted_net_floor_area for z in self.zones)

    @property
    def net_volume(self) -> float:
        """Returns the total net-volume of all the zones in the PhxBuilding."""
        return sum(z.volume_net for z in self.zones)

    def add_components(
        self, _components: Union[PhxComponentOpaque, Sequence[PhxComponentOpaque]]
    ) -> None:
        """Add a new PhxComponentOpaque to the PhxBuilding."""
        if not isinstance(_components, Sequence):
            _components = (_components,)

        for compo in _components:
            self._components.append(compo)

    def add_zones(self, _zones: Union[PhxZone, Sequence[PhxZone]]) -> None:
        """Add a new PhxZone to the PhxBuilding."""
        if not isinstance(_zones, Sequence):
            _zones = (_zones,)

        for zone in _zones:
            self.zones.append(zone)

    def merge_opaque_components_by_assembly(self) -> None:
        """Merge together all the Opaque-Components in the Building if they gave the same Attributes."""
        # -- Group the opaque components by their unique key / type
        new_component_groups = defaultdict(list)
        for c in self.opaque_components:
            new_component_groups[c.unique_key].append(c)

        # -- Create new components from the group
        grouped_opaque_components: List[PhxComponentOpaque] = []
        for component_group in new_component_groups.values():
            grouped_opaque_components.append(reduce(operator.add, component_group))

        # -- Reset the Building's Components
        self._components = grouped_opaque_components

    def merge_aperture_components_by_assembly(self) -> None:
        """Merge together all the Aperture-Components in the Building if they gave the same Attributes."""
        # -- Group the aperture components by their unique key / type
        new_components: List[PhxComponentOpaque] = []
        for c in self.opaque_components:
            new_component_groups = defaultdict(list)
            for a in c.apertures:
                new_component_groups[a.unique_key].append(a)

            # -- Create new components from the groups
            grouped_aperture_components = []
            for component_group in new_component_groups.values():
                grouped_aperture_components.append(reduce(operator.add, component_group))

            # -- Reset the Components's Apertures
            c.apertures = grouped_aperture_components
            new_components.append(c)

        # -- Reset the Building's Components
        self._components = new_components

    @property
    def all_components(self) -> List[Union[PhxComponentOpaque, PhxComponentAperture]]:
        """Return a list of all the Opaque and Aperture Components in the Building.

        Returns:
        --------
            * (List[Union[PhxComponentOpaque, PhxComponentAperture]]) A list of all
                the opaque and aperture components.
        """
        all_components: List[Union[PhxComponentOpaque, PhxComponentAperture]] = []
        for c in self._components:
            all_components += c.apertures
            all_components.append(c)
        return sorted(all_components, key=lambda c: c.id_num)

    @property
    def opaque_components(self) -> List[PhxComponentOpaque]:
        """Returns a sorted list (by display name) of all the opaque non-shade components in the building.

        Returns:
        --------
            * (List[PhxComponentOpaque]) A sorted list of all the opaque components.
        """
        return sorted(
            [c for c in self._components if not c.is_shade], key=lambda _: _.display_name
        )

    @property
    def shading_components(self) -> List[PhxComponentOpaque]:
        """Returns a list of all the opaque shade components in the building.

        Returns:
        --------
            * (List[PhxComponentOpaque]) A sorted list of all the shading components.
        """
        return sorted(
            [c for c in self._components if c.is_shade], key=lambda _: _.display_name
        )

    @property
    def polygon_ids(self) -> Set[int]:
        """Return a Set of all the Polygon IDs of all Polygons from all the Components in the building."""
        p_ids = set()
        for compo in self.all_components:
            p_ids.update(compo.polygon_ids)
        return p_ids

    @property
    def polygons(self) -> List[geometry.PhxPolygon]:
        """Returns a list of all the Polygons of all the Components in the building."""
        return [poly for component in self.all_components for poly in component.polygons]

    def __bool__(self) -> bool:
        return bool(self.opaque_components) or bool(self.zones)
