# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Project Classes"""

from __future__ import annotations
from typing import ClassVar, List, Dict, Optional, Any, Set
from dataclasses import dataclass, field

from PHX.model.building import PhxBuilding, PhxZone
from PHX.model.certification import PhxPhiusCertification, PhxPhiCertification
from PHX.model.constructions import PhxConstructionOpaque, PhxConstructionWindow
from PHX.model.geometry import PhxGraphics3D
from PHX.model.hvac.collection import PhxMechanicalSystemCollection
from PHX.model.phx_site import PhxSite
from PHX.model.schedules import ventilation, occupancy, lighting
from PHX.model.shades import PhxWindowShade
from PHX.model.utilization_patterns import (
    UtilizationPatternCollection_Occupancy,
    UtilizationPatternCollection_Ventilation,
    UtilizationPatternCollection_Lighting,
)


@dataclass
class WufiPlugin:
    insert_plugin: bool = False
    name_dll: Optional[Any] = None
    status_plugin: Optional[Any] = None


@dataclass
class PhxVariant:
    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    name: Optional[str] = "unnamed_variant"
    remarks: Optional[str] = None
    plugin: Optional[WufiPlugin] = field(default_factory=WufiPlugin)
    building: PhxBuilding = field(default_factory=PhxBuilding)
    phius_cert: PhxPhiusCertification = field(default_factory=PhxPhiusCertification)
    phi_cert: PhxPhiCertification = field(default_factory=PhxPhiCertification)
    site: PhxSite = field(default_factory=PhxSite)
    mech_systems: PhxMechanicalSystemCollection = field(
        default_factory=PhxMechanicalSystemCollection
    )

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def graphics3D(self):
        """Collects all of the geometry (Polygons, Vertices) in the Project."""
        phx_graphics3D = PhxGraphics3D()
        for phx_component in self.building.all_components:
            phx_graphics3D.add_polygons(phx_component.polygons)
        return phx_graphics3D

    @property
    def phi_certification_major_version(self) -> int:
        """Return the PHI Certification Version Number."""
        return self.phi_cert.version

    @property
    def zones(self) -> List[PhxZone]:
        """Return a list of all the PHX Zones in the variant.building"""
        return self.building.zones

    def get_total_gross_wall_area(self) -> float:
        """Returns the total wall area of the variant.building"""
        return self.building.get_total_gross_wall_area()

    def get_total_net_wall_area(self) -> float:
        """Returns the total net wall area of the variant.building"""
        return self.building.get_total_net_wall_area()

    def get_total_wall_aperture_area(self) -> float:
        """Returns the total window area of the variant.building"""
        return self.building.get_total_wall_aperture_area()

    def get_total_gross_roof_area(self) -> float:
        """Returns the total wall area of the variant.building"""
        return self.building.get_total_gross_roof_area()

    def get_total_net_roof_area(self) -> float:
        """Returns the total net wall area of the variant.building"""
        return self.building.get_total_net_roof_area()

    def get_total_roof_aperture_area(self) -> float:
        """Returns the total window area of the variant.building"""
        return self.building.get_total_roof_aperture_area()


@dataclass
class ProjectData_Agent:
    name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    post_code: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None


@dataclass
class PhxProjectData:
    customer: ProjectData_Agent = field(default_factory=ProjectData_Agent)
    building: ProjectData_Agent = field(default_factory=ProjectData_Agent)
    owner: ProjectData_Agent = field(default_factory=ProjectData_Agent)
    designer: ProjectData_Agent = field(default_factory=ProjectData_Agent)

    project_date: str = ""
    owner_is_client: bool = False
    year_constructed: int = 0
    image: Optional[bool] = None


@dataclass
class PhxProject:
    name: str = "unnamed_project"
    assembly_types: Dict[str, PhxConstructionOpaque] = field(default_factory=dict)
    window_types: Dict[str, PhxConstructionWindow] = field(default_factory=dict)
    shade_types: Dict[str, PhxWindowShade] = field(default_factory=dict)
    utilization_patterns_ventilation: UtilizationPatternCollection_Ventilation = field(
        default_factory=UtilizationPatternCollection_Ventilation
    )
    utilization_patterns_occupancy: UtilizationPatternCollection_Occupancy = field(
        default_factory=UtilizationPatternCollection_Occupancy
    )
    utilization_patterns_lighting: UtilizationPatternCollection_Lighting = field(
        default_factory=UtilizationPatternCollection_Lighting
    )
    variants: List[PhxVariant] = field(default_factory=list)
    project_data: PhxProjectData = field(default_factory=PhxProjectData)
    data_version: int = 48
    unit_system: int = 1  # SI
    program_version: str = "3.2.0.1"
    scope: int = 3
    visualized_geometry: int = 2

    def add_new_variant(self, _variant: PhxVariant) -> None:
        """Adds a new PHX Variant to the Project."""
        self.variants.append(_variant)

    @property
    def assembly_type_id_numbers(self) -> Set[int]:
        return {assembly.id_num for assembly in self.assembly_types.values()}

    @property
    def window_type_id_numbers(self) -> Set[int]:
        return {window.id_num for window in self.window_types.values()}

    @property
    def shade_type_id_numbers(self) -> Set[int]:
        return {shade.id_num for shade in self.shade_types.values()}

    def add_assembly_type(self, _assembly_type: PhxConstructionOpaque, _key=None) -> None:
        """Adds a new PhxConstructionOpaque to the Project's collection"""
        # -- be sure to the ID-Num
        if _assembly_type.id_num in self.assembly_type_id_numbers:
            _assembly_type.id_num = max(self.assembly_type_id_numbers) + 1

        if _key:
            self.assembly_types[_key] = _assembly_type
        else:
            self.assembly_types[_assembly_type.identifier] = _assembly_type

    def add_new_window_type(self, _window_type: PhxConstructionWindow, _key=None) -> None:
        """Adds a new PhxConstructionWindow to the Project's collection"""
        if _window_type.id_num in self.window_type_id_numbers:
            _window_type.id_num = max(self.window_type_id_numbers) + 1

        if _key:
            self.window_types[_key] = _window_type
        else:
            self.window_types[_window_type.identifier] = _window_type

    def get_window_type(self, _key: str) -> PhxConstructionWindow:
        """Returns the PhxConstructionWindow with the specified key"""
        return self.window_types[_key]

    def add_new_shade_type(self, _shade_type: PhxWindowShade, _key=None) -> None:
        """Adds a new PhxWindowShade to the Project's collection"""
        if _shade_type.id_num in self.shade_type_id_numbers:
            _shade_type.id_num = max(self.shade_type_id_numbers) + 1

        if _key:
            self.shade_types[_key] = _shade_type
        else:
            self.shade_types[_shade_type.identifier] = _shade_type

    def vent_sched_in_project_collection(self, _key: str) -> bool:
        """See if the project Ventilation schedule collection already includes the specified key."""
        return self.utilization_patterns_ventilation.key_is_in_collection(_key)

    def occupancy_sched_in_project_collection(self, _key: str) -> bool:
        """See if the project Occupancy schedule collection already includes the specified key."""
        return self.utilization_patterns_occupancy.key_is_in_collection(_key)

    def lighting_sched_in_project_collection(self, _key: str) -> bool:
        """See if the project Lighting schedule collection already includes the specified key."""
        return self.utilization_patterns_lighting.key_is_in_collection(_key)

    def add_vent_sched_to_collection(
        self, vent_sched: ventilation.PhxScheduleVentilation
    ) -> None:
        """Add a new Ventilation schedule to the project's collection."""
        self.utilization_patterns_ventilation.add_new_util_pattern(vent_sched)

    def add_occupancy_sched_to_collection(
        self, vent_sched: Optional[occupancy.PhxScheduleOccupancy]
    ) -> None:
        """Add a new Occupancy schedule to the project's collection."""
        self.utilization_patterns_occupancy.add_new_util_pattern(vent_sched)

    def add_lighting_sched_to_collection(
        self, lighting_sched: Optional[lighting.PhxScheduleLighting]
    ) -> None:
        """Add a new Occupancy schedule to the project's collection."""
        self.utilization_patterns_lighting.add_new_util_pattern(lighting_sched)

    def get_total_gross_wall_area(self) -> float:
        """Get the total gross wall area for all variants in the project (ignoring any apertures)."""
        return sum([variant.get_total_gross_wall_area() for variant in self.variants])

    def get_total_net_wall_area(self) -> float:
        """Get the total net wall area for all variants in the project (ignoring any apertures)."""
        return sum([variant.get_total_net_wall_area() for variant in self.variants])

    def get_total_gross_roof_area(self) -> float:
        """Get the total gross roof area for all variants in the project."""
        return sum([variant.get_total_gross_roof_area() for variant in self.variants])

    def get_total_net_roof_area(self) -> float:
        """Get the total net roof area for all variants in the project."""
        return sum([variant.get_total_net_roof_area() for variant in self.variants])

    def get_total_wall_aperture_area(self) -> float:
        """Get the total window area for all variants in the project."""
        return sum([variant.get_total_wall_aperture_area() for variant in self.variants])

    def get_total_roof_aperture_area(self) -> float:
        """Get the total roof aperture area for all variants in the project."""
        return sum([variant.get_total_roof_aperture_area() for variant in self.variants])

    def __str__(self):
        return f"{self.__class__.__name__}"
