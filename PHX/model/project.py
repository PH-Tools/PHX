# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Project Classes"""

from __future__ import annotations
from typing import ClassVar, List, Dict, Optional, Any
from dataclasses import dataclass, field

from PHX.model.building import PhxBuilding, PhxZone
from PHX.model.certification import PhxPhiusCertification, PhxPhiCertification
from PHX.model.constructions import PhxConstructionOpaque, PhxConstructionWindow
from PHX.model.geometry import PhxGraphics3D
from PHX.model.hvac.collection import PhxMechanicalSystemCollection
from PHX.model.phx_site import PhxSite
from PHX.model.schedules.ventilation import PhxScheduleVentilation
from PHX.model.schedules.occupancy import PhxScheduleOccupancy
from PHX.model.shades import PhxWindowShade
from PHX.model.utilization_patterns import (
    UtilizationPatternCollection_Occupancy,
    UtilizationPatternCollection_Ventilation,
)

@dataclass
class PhxVariant:
    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    name: str = "unnamed_variant"
    remarks: str = ""
    plugin: str = ""
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


@dataclass
class ProjectData_Agent:
    name: str = ""
    street: str = ""
    city: str = ""
    post_code: str = ""
    telephone: str = ""
    email: str = ""
    license_number: str = ""


@dataclass
class PhxProjectData:
    customer: ProjectData_Agent = field(default_factory=ProjectData_Agent)
    building: ProjectData_Agent = field(default_factory=ProjectData_Agent)
    owner: ProjectData_Agent = field(default_factory=ProjectData_Agent)
    responsible: ProjectData_Agent = field(default_factory=ProjectData_Agent)

    project_date: str = ""
    owner_is_client: bool = False
    year_constructed: int = 0
    image: None = None


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
    variants: List[PhxVariant] = field(default_factory=list)
    project_data: PhxProjectData = field(default_factory=PhxProjectData)
    data_version: int = 48
    unit_system: int = 1
    program_version: str = "3.2.0.1"
    scope: int = 3
    visualized_geometry: int = 2

    def add_new_variant(self, _variant: PhxVariant) -> None:
        """Adds a new PHX Variant to the Project."""
        self.variants.append(_variant)

    def add_new_window_type(self, _window_type: PhxConstructionWindow) -> None:
        """Adds a new PhxConstructionWindow to the Project's collection"""
        self.window_types[_window_type.identifier] = _window_type
    
    def add_new_shade_type(self, _shade_type: PhxWindowShade) -> None:
        """Adds a new PhxWindowShade to the Project's collection"""
        self.shade_types[_shade_type.identifier] = _shade_type

    def vent_sched_in_project_collection(self, _key: str) -> bool:
        """See if the project Ventilation schedule collection already includes the specified key."""
        return self.utilization_patterns_ventilation.key_is_in_collection(_key)

    def occupancy_sched_in_project_collection(self, _key: str) -> bool:
        """See if the project Occupancy schedule collection already includes the specified key."""
        return self.utilization_patterns_occupancy.key_is_in_collection(_key)

    def add_vent_sched_to_collection(
        self, vent_sched: Optional[PhxScheduleVentilation]
    ) -> None:
        """Add a new Ventilation schedule to the project's collection."""
        self.utilization_patterns_ventilation.add_new_util_pattern(vent_sched)

    def add_occupancy_sched_to_collection(
        self, vent_sched: Optional[PhxScheduleOccupancy]
    ) -> None:
        """Add a new Occupancy schedule to the project's collection."""
        self.utilization_patterns_occupancy.add_new_util_pattern(vent_sched)

    def __str__(self):
        return f"{self.__class__.__name__}"
