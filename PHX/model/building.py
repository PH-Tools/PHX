# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Building Classes"""

from __future__ import annotations
from typing import (
    ClassVar,
    List,
    Sequence,
    Union,
    Set,
    Dict,
    ValuesView,
    Any,
    Optional,
    Generator,
    NamedTuple,
)
from dataclasses import dataclass, field
from collections import defaultdict
from functools import reduce
import operator

from PHX.model import elec_equip, geometry, spaces
from PHX.model.components import (
    PhxComponentAperture,
    PhxComponentOpaque,
    PhxComponentThermalBridge,
    PhxApertureElement,
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
    res_occupant_quantity: float = 0.0
    res_number_bedrooms: int = 0
    res_number_dwellings: int = 0
    specific_heat_capacity: SpecificHeatCapacity = SpecificHeatCapacity.LIGHTWEIGHT

    spaces: List[spaces.PhxSpace] = field(default_factory=list)
    _thermal_bridges: Dict[str, PhxComponentThermalBridge] = field(default_factory=dict)

    # TODO: see if this can be safely removed?
    # ---------------------------------------------------------
    occupancy: Optional[occupancy.PhxProgramOccupancy] = None
    # ---------------------------------------------------------

    lighting: Any = None
    elec_equipment_collection: elec_equip.PhxElectricDeviceCollection = field(
        default_factory=elec_equip.PhxElectricDeviceCollection
    )
    exhaust_ventilator_collection: collection.PhxExhaustVentilatorCollection = field(
        default_factory=collection.PhxExhaustVentilatorCollection
    )

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    def add_thermal_bridge(self, _thermal_bridge: PhxComponentThermalBridge) -> None:
        """Add a new PhxComponentThermalBridge to the PhxZone."""
        self._thermal_bridges[_thermal_bridge.identifier] = _thermal_bridge

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

    @property
    def spaces_with_ventilation(self) -> List[spaces.PhxSpace]:
        """Return a list of all the spaces in the PhxZone which hav ventilation airflow."""
        return [s for s in self.spaces if s.has_ventilation_airflow]


@dataclass
class PhxBuilding:
    """PHX Building Class"""

    # -- Only opaque components (and shades) are stored in the _components list
    # -- as the apertures are stored in the opaque components themselves
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
        """Add new PHX Components to the PhxBuilding."""
        if not isinstance(_components, Sequence):
            _components = (_components,)

        for compo in _components:
            self._components.append(compo)

    def add_component(self, _component: PhxComponentOpaque) -> None:
        """Add a new PHX Components to the PhxBuilding."""
        self._components.append(_component)

    def add_zones(self, _zones: Union[PhxZone, Sequence[PhxZone]]) -> None:
        """Add a new PhxZone to the PhxBuilding."""
        if not isinstance(_zones, Sequence):
            _zones = (_zones,)

        for zone in _zones:
            self.zones.append(zone)

    def add_zone(self, _zone: PhxZone) -> None:
        """Add a new PhxZone to the PhxBuilding."""
        self.zones.append(_zone)

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
    def aperture_components(self) -> List[PhxComponentAperture]:
        """Returns a sorted list (by display name) of all the aperture components in the building.

        Returns:
        --------
            * (List[PhxComponentAperture]) A sorted list of all the aperture components.
        """
        return [ap for c in self.opaque_components for ap in c.apertures]

    @property
    def aperture_elements(self) -> List[PhxApertureElement]:
        """Returns a sorted list (by display name) of all the aperture elements in the building.

        Returns:
        --------
            * (List[PhxApertureElement]) A sorted list of all the aperture components.
        """
        return sorted(
            [
                el
                for c in self.opaque_components
                for ap in c.apertures
                for el in ap.elements
            ],
            key=lambda el: el.display_name,
        )

    @property
    def aperture_elements_by_orientation(self):
        """Return all of the Aperture Elements, grouped by their cardinal orientation."""

        class Output(NamedTuple):
            north: List[PhxApertureElement]
            east: List[PhxApertureElement]
            south: List[PhxApertureElement]
            west: List[PhxApertureElement]
            horizontal: List[PhxApertureElement]

        aperture_elements_by_orientation = Output([], [], [], [], [])

        for el in self.aperture_elements:
            if not el.polygon:
                continue

            if (
                el.polygon.angle_from_horizontal <= 45
                or el.polygon.angle_from_horizontal >= 135
            ):
                aperture_elements_by_orientation.horizontal.append(el)
            elif el.polygon.cardinal_orientation_angle < 45:
                aperture_elements_by_orientation.north.append(el)
            elif el.polygon.cardinal_orientation_angle < 135:
                aperture_elements_by_orientation.east.append(el)
            elif el.polygon.cardinal_orientation_angle < 225:
                aperture_elements_by_orientation.south.append(el)
            elif el.polygon.cardinal_orientation_angle < 315:
                aperture_elements_by_orientation.west.append(el)
            else:
                aperture_elements_by_orientation.north.append(el)

        return aperture_elements_by_orientation

    @property
    def aperture_components_horizontal(self) -> List[PhxComponentAperture]:
        return [ap for ap in self.aperture_components]

    @property
    def wall_aperture_components(self) -> List[PhxComponentAperture]:
        """Returns a sorted list (by display name) of all the wall aperture (window) components in the building.

        Returns:
        --------
            * (List[PhxComponentAperture]) A sorted list of all the wall aperture components.
        """
        return sorted(
            [ap for c in self.above_grade_wall_components for ap in c.apertures],
            key=lambda ap: ap.display_name,
        )

    @property
    def roof_aperture_components(self) -> List[PhxComponentAperture]:
        """Returns a sorted list (by display name) of all the roof aperture (skylight) components in the building.

        Returns:
        --------
            * (List[PhxComponentAperture]) A sorted list of all the roof aperture components.
        """
        return sorted(
            [ap for c in self.roof_components for ap in c.apertures],
            key=lambda ap: ap.display_name,
        )

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
    def roof_components(self) -> List[PhxComponentOpaque]:
        """Returns a sorted list (by display name) of all the roof components in the building.

        Returns:
        --------
            * (List[PhxComponentOpaque]) A sorted list of all the roof components.
        """
        return sorted(
            [c for c in self._components if c.is_roof], key=lambda _: _.display_name
        )

    @property
    def above_grade_wall_components(self) -> List[PhxComponentOpaque]:
        """Returns a sorted list (by display name) of all the above grade wall components in the building.

        Returns:
        --------
            * (List[PhxComponentOpaque]) A sorted list of all the above grade wall components.
        """
        return sorted(
            [c for c in self._components if c.is_above_grade_wall],
            key=lambda _: _.display_name,
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

    def get_total_gross_wall_area(self) -> float:
        """Returns the total wall area of all the opaque components in the building."""
        return sum(
            c.get_total_gross_component_area() for c in self.above_grade_wall_components
        )

    def get_total_net_wall_area(self) -> float:
        """Returns the total net wall area of all the opaque components in the building."""
        return sum(
            c.get_total_net_component_area() for c in self.above_grade_wall_components
        )

    def get_total_gross_roof_area(self) -> float:
        """Returns the total roof area of all the opaque components in the building."""
        return sum(c.get_total_gross_component_area() for c in self.roof_components)

    def get_total_net_roof_area(self) -> float:
        """Returns the total net roof area of all the opaque components in the building."""
        return sum(c.get_total_net_component_area() for c in self.roof_components)

    def get_total_wall_aperture_area(self) -> float:
        """Returns the total window area of all the opaque components in the building."""
        return sum(c.get_total_aperture_area() for c in self.wall_aperture_components)

    def get_total_roof_aperture_area(self) -> float:
        """Returns the total skylight area of all the opaque components in the building."""
        return sum(c.get_total_aperture_area() for c in self.roof_aperture_components)

    def scale_all_wall_aperture_components(self, _scale_factor: float = 1.0) -> None:
        """Scale all the wall-aperture component's polygons by a given factor.

        Args:
        -----
            * scale_factor (float): The factor to scale the aperture components by.
        """
        for c in self.wall_aperture_components:
            c.scale(_scale_factor)

    def scale_all_roof_aperture_components(self, _scale_factor: float = 1.0) -> None:
        """Scale all the roof-aperture component's polygons by a given factor.

        Args:
        -----
            * scale_factor (float): The factor to scale the aperture components by.
        """
        for c in self.roof_aperture_components:
            c.scale(_scale_factor)
