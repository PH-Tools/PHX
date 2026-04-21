# -*- Python Version: 3.10 -*-

"""PHX Project Classes"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

from PHX.model.building import PhxBuilding, PhxZone
from PHX.model.certification import PhxPhiCertification, PhxPhiusCertification
from PHX.model.constructions import PhxConstructionOpaque, PhxConstructionWindow
from PHX.model.geometry import PhxGraphics3D
from PHX.model.hvac import PhxMechanicalDevice
from PHX.model.hvac.collection import NoDeviceFoundError, PhxMechanicalSystemCollection
from PHX.model.phx_site import PhxSite
from PHX.model.schedules import lighting, occupancy, ventilation
from PHX.model.shades import PhxWindowShade
from PHX.model.utilization_patterns import (
    UtilizationPatternCollection_Lighting,
    UtilizationPatternCollection_Occupancy,
    UtilizationPatternCollection_Ventilation,
)


@dataclass
class WufiPlugin:
    """WUFI-Passive plugin configuration for a variant.

    Controls whether a WUFI plugin DLL is loaded when the project is opened
    in WUFI-Passive.

    Attributes:
        insert_plugin (bool): Whether to insert the plugin on load.
            Default: False.
        name_dll (Any | None): Name of the plugin DLL file. Default: None.
        status_plugin (Any | None): Plugin status flag. Default: None.
    """

    insert_plugin: bool = False
    name_dll: Any | None = None
    status_plugin: Any | None = None


@dataclass
class PhxVariant:
    """A single design variant within a PHX project.

    Each variant holds one building model, certification settings (PHI and Phius),
    site/climate data, and one or more mechanical system collections. In WUFI-Passive,
    variants appear as separate tabs allowing side-by-side comparison of design options.

    A default mechanical collection is created automatically on initialization.

    Attributes:
        id_num (int): Auto-incrementing variant identifier.
        name (str | None): Display name. Default: "unnamed_variant".
        remarks (str | None): Free-text notes. Default: None.
        plugin (WufiPlugin | None): WUFI plugin configuration.
        building (PhxBuilding): The building geometry and zone data.
        phius_cert (PhxPhiusCertification): Phius certification settings.
        phi_cert (PhxPhiCertification): PHI certification settings.
        site (PhxSite): Site location, climate, and energy factor data.
    """

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    name: str | None = "unnamed_variant"
    remarks: str | None = None
    plugin: WufiPlugin | None = field(default_factory=WufiPlugin)
    building: PhxBuilding = field(default_factory=PhxBuilding)
    phius_cert: PhxPhiusCertification = field(default_factory=PhxPhiusCertification)
    phi_cert: PhxPhiCertification = field(default_factory=PhxPhiCertification)
    site: PhxSite = field(default_factory=PhxSite)

    # -- Allow for multiple mechanical 'collections' in a variant
    # -- If WUFI, these are called 'systems', but they also use
    # -- the word 'system' in other places. So to avoid confusion, lets
    # -- call them 'collections' here
    _mech_collections: list[PhxMechanicalSystemCollection] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

        # -- Always Add a default mech-collection
        self._mech_collections.append(PhxMechanicalSystemCollection())

    @property
    def mech_systems(self) -> PhxMechanicalSystemCollection:
        """Return the Default Mechanical System Collection for the variant.

        This is a facade to allow for backwards compatibility as well.
        """
        return self._mech_collections[0]

    @property
    def mech_collections(self) -> list[PhxMechanicalSystemCollection]:
        """Return the list of Mechanical System Collections for the variant."""
        return self._mech_collections

    @property
    def default_mech_collection(self) -> PhxMechanicalSystemCollection:
        """Return the Default Mechanical System Collection for the variant."""
        return self._mech_collections[0]

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
    def zones(self) -> list[PhxZone]:
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

    def get_total_gross_envelope_area(self) -> float:
        """Returns the total gross envelope area of the variant.building"""
        return self.building.get_total_gross_envelope_area()

    def add_mechanical_collection(self, _mech_collection: PhxMechanicalSystemCollection) -> None:
        """Add a new mechanical collection to the variant."""
        self._mech_collections.append(_mech_collection)

    def clear_mechanical_collections(self) -> None:
        """Clear all mechanical collections from the variant."""
        self._mech_collections = []

    def get_mech_device_by_key(
        self, _key: str
    ) -> tuple[PhxMechanicalSystemCollection | None, PhxMechanicalDevice | None]:
        """Return a Tuple of a mech-collection and a mechanical device based on the specified device key, or None if not found."""

        found: list[tuple[PhxMechanicalSystemCollection | None, PhxMechanicalDevice | None]] = []
        for mech_collection in self._mech_collections:
            found.append((mech_collection, mech_collection._devices.get(_key, None)))

        if len(found) == 0:
            return None, None
        elif len(found) == 1:
            return found[0]
        else:
            raise ValueError(f"Multiple mechanical devices found with key: {_key}.")

    def device_in_collections(self, _key: str) -> bool:
        """See if the variant's mechanical device collections already includes the specified key."""
        return any(mech_collection.device_in_collection(_key) for mech_collection in self._mech_collections)

    def supportive_device_in_collections(self, _key: str) -> bool:
        """Return a supportive device based on the specified device key, or None if not found."""
        for mech_collection in self._mech_collections:
            if mech_collection.supportive_devices.device_in_collection(_key):
                return True
        return False

    def renewable_device_in_collections(self, _key: str) -> bool:
        """Return a renewable device based on the specified device key, or None if not found."""
        for mech_collection in self._mech_collections:
            if mech_collection.renewable_devices.device_in_collection(_key):
                return True
        return False

    def get_mech_device_by_id(self, _id_num: int) -> PhxMechanicalDevice:
        """Returns a Mechanical Device from the collections which has a matching id-num."""
        for mech_collection in self._mech_collections:
            phx_mech_ventilator = mech_collection.get_mech_device_by_id(_id_num)
            if phx_mech_ventilator:
                return phx_mech_ventilator

        raise NoDeviceFoundError(_id_num)


@dataclass
class ProjectData_Agent:
    """Contact information for a project stakeholder (customer, owner, designer, etc.).

    Attributes:
        name (str | None): Full name. Default: None.
        street (str | None): Street address. Default: None.
        city (str | None): City name. Default: None.
        post_code (str | None): Postal / ZIP code. Default: None.
        telephone (str | None): Phone number. Default: None.
        email (str | None): Email address. Default: None.
        license_number (str | None): Professional license number. Default: None.
    """

    name: str | None = None
    street: str | None = None
    city: str | None = None
    post_code: str | None = None
    telephone: str | None = None
    email: str | None = None
    license_number: str | None = None


@dataclass
class PhxProjectDate:
    """Timestamp for a PHX project, defaulting to the current date and time.

    Attributes:
        year (int): Four-digit year.
        month (int): Month (1-12).
        day (int): Day of month (1-31).
        hour (int): Hour (0-23).
        minutes (int): Minutes (0-59).
    """

    year: int = datetime.now().year
    month: int = datetime.now().month
    day: int = datetime.now().day
    hour: int = datetime.now().hour
    minutes: int = datetime.now().minute


@dataclass
class PhxProjectData:
    """Project-level metadata including stakeholder contacts and dates.

    Attributes:
        customer (ProjectData_Agent): Customer / client contact information.
        building (ProjectData_Agent): Building address and contact.
        owner (ProjectData_Agent): Building owner contact information.
        designer (ProjectData_Agent): Project designer / architect contact.
        project_date (PhxProjectDate): Project creation timestamp.
        owner_is_client (bool): Whether the owner is also the client.
            Default: False.
        year_constructed (int): Year the building was constructed. Default: 0.
        image (bool | None): Whether an image is attached. Default: None.
    """

    customer: ProjectData_Agent = field(default_factory=ProjectData_Agent)
    building: ProjectData_Agent = field(default_factory=ProjectData_Agent)
    owner: ProjectData_Agent = field(default_factory=ProjectData_Agent)
    designer: ProjectData_Agent = field(default_factory=ProjectData_Agent)

    project_date: PhxProjectDate = field(default_factory=PhxProjectDate)
    owner_is_client: bool = False
    year_constructed: int = 0
    image: bool | None = None


@dataclass
class PhxProject:
    """Top-level PHX project container.

    Holds the project-wide collections of construction assemblies, window types,
    shade types, utilization pattern schedules, and one or more design variants.
    This is the root object for any PHX model.

    Attributes:
        name (str): Project display name. Default: "unnamed_project".
        assembly_types (dict[str, PhxConstructionOpaque]): Opaque construction
            assemblies keyed by identifier.
        window_types (dict[str, PhxConstructionWindow]): Window constructions
            keyed by identifier.
        shade_types (dict[str, PhxWindowShade]): Window shade definitions
            keyed by identifier.
        utilization_patterns_ventilation (UtilizationPatternCollection_Ventilation):
            Project-level ventilation schedule collection.
        utilization_patterns_occupancy (UtilizationPatternCollection_Occupancy):
            Project-level occupancy schedule collection.
        utilization_patterns_lighting (UtilizationPatternCollection_Lighting):
            Project-level lighting schedule collection.
        variants (list[PhxVariant]): Design variants in this project.
        project_data (PhxProjectData): Project metadata and stakeholder contacts.
        data_version (int): WUFI data format version. Default: 48.
        unit_system (int): Unit system (1 = SI). Default: 1.
        program_version (str): WUFI program version string. Default: "3.2.0.1".
        scope (int): Project scope flag. Default: 3.
        visualized_geometry (int): Geometry visualization mode. Default: 2.
    """

    name: str = "unnamed_project"
    assembly_types: dict[str, PhxConstructionOpaque] = field(default_factory=dict)
    window_types: dict[str, PhxConstructionWindow] = field(default_factory=dict)
    shade_types: dict[str, PhxWindowShade] = field(default_factory=dict)
    utilization_patterns_ventilation: UtilizationPatternCollection_Ventilation = field(
        default_factory=UtilizationPatternCollection_Ventilation
    )
    utilization_patterns_occupancy: UtilizationPatternCollection_Occupancy = field(
        default_factory=UtilizationPatternCollection_Occupancy
    )
    utilization_patterns_lighting: UtilizationPatternCollection_Lighting = field(
        default_factory=UtilizationPatternCollection_Lighting
    )
    variants: list[PhxVariant] = field(default_factory=list)
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
    def assembly_type_id_numbers(self) -> set[int]:
        return {assembly.id_num for assembly in self.assembly_types.values()}

    @property
    def window_type_id_numbers(self) -> set[int]:
        return {window.id_num for window in self.window_types.values()}

    @property
    def shade_type_id_numbers(self) -> set[int]:
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
        try:
            return self.window_types[_key]
        except KeyError:
            valid_keys = "  |  ".join([f"{k}::{v.display_name}" for k, v in self.window_types.items()])
            msg = (
                f"Window Type: '{_key}' not found in project collection? "
                f"Valid window-types include only: {valid_keys}."
            )
            raise KeyError(msg)

    def get_window_types_by_name(self, _name: str) -> list[PhxConstructionWindow]:
        """Returns a list of PhxConstructionWindow with the specified name.

        CAUTION: Multiple window types can have the same name.
        Use the .get_window_type() and use the 'key' to get an exact window type.
        """
        return [window_type for window_type in self.window_types.values() if window_type.display_name == _name]

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

    def add_vent_sched_to_collection(self, vent_sched: ventilation.PhxScheduleVentilation) -> None:
        """Add a new Ventilation schedule to the project's collection."""
        self.utilization_patterns_ventilation.add_new_util_pattern(vent_sched)

    def add_occupancy_sched_to_collection(self, vent_sched: occupancy.PhxScheduleOccupancy | None) -> None:
        """Add a new Occupancy schedule to the project's collection."""
        self.utilization_patterns_occupancy.add_new_util_pattern(vent_sched)

    def add_lighting_sched_to_collection(self, lighting_sched: lighting.PhxScheduleLighting | None) -> None:
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
