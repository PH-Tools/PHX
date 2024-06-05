# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions to create a new PhxBuilding from Honeybee-Rooms"""

from functools import partial
from typing import Dict, List, Union

from honeybee import aperture, face, room
from honeybee_energy.construction import window, windowshade
from honeybee_energy.properties.aperture import ApertureEnergyProperties
from honeybee_energy.properties.face import FaceEnergyProperties
from honeybee_energy.properties.room import RoomEnergyProperties
from honeybee_energy_ph.properties.construction.opaque import OpaqueConstructionPhProperties
from honeybee_energy_ph.properties.construction.window import WindowConstructionPhProperties
from honeybee_energy_ph.properties.load.people import PeoplePhProperties
from honeybee_ph import space
from honeybee_ph.properties.aperture import AperturePhProperties
from honeybee_ph.properties.room import RoomPhProperties

from PHX.from_HBJSON import create_geometry
from PHX.from_HBJSON.create_rooms import create_room_from_space
from PHX.model import building, components, constructions
from PHX.model.enums.building import (
    ComponentColor,
    ComponentExposureExterior,
    ComponentFaceOpacity,
    ComponentFaceType,
    SpecificHeatCapacity,
    ThermalBridgeType,
)
from PHX.model.utilization_patterns import (
    UtilizationPatternCollection_Lighting,
    UtilizationPatternCollection_Occupancy,
    UtilizationPatternCollection_Ventilation,
)


def _hb_face_opacity_to_phx_enum(_hb_face: face.Face) -> ComponentFaceOpacity:
    mapping = {
        "Wall": ComponentFaceOpacity.OPAQUE,
        "RoofCeiling": ComponentFaceOpacity.OPAQUE,
        "Floor": ComponentFaceOpacity.OPAQUE,
        "AirBoundary": ComponentFaceOpacity.AIRBOUNDARY,
    }
    return mapping[str(_hb_face.type)]


def _hb_face_type_to_phx_enum(_hb_face: face.Face) -> ComponentFaceType:
    mapping = {
        "Wall": ComponentFaceType.WALL,
        "Floor": ComponentFaceType.FLOOR,
        "RoofCeiling": ComponentFaceType.ROOF_CEILING,
        "AirBoundary": ComponentFaceType.AIR_BOUNDARY,
    }
    return mapping[str(_hb_face.type)]


def _hb_ext_exposure_to_phx_enum(_hb_face: Union[face.Face, aperture.Aperture]) -> ComponentExposureExterior:
    mapping = {
        "Outdoors": ComponentExposureExterior.EXTERIOR,
        "Ground": ComponentExposureExterior.GROUND,
        "Surface": ComponentExposureExterior.SURFACE,
        "Adiabatic": ComponentExposureExterior.SURFACE,
    }
    return mapping[str(_hb_face.boundary_condition)]


def _hb_int_color_to_phx_enum(_hb_face: face.Face) -> ComponentColor:
    mapping = {
        "Wall": {
            "Outdoors": ComponentColor.EXT_WALL_OUTER,
            "Surface": ComponentColor.INNER_WALL,
            "Ground": ComponentColor.SURFACE_GROUND_CONTACT,
            "Adiabatic": ComponentColor.INNER_WALL,
        },
        "RoofCeiling": {
            "Outdoors": ComponentColor.SLOPED_ROOF_OUTER,
            "Surface": ComponentColor.CEILING,
            "Ground": ComponentColor.SURFACE_GROUND_CONTACT,
            "Adiabatic": ComponentColor.CEILING,
        },
        "Floor": {
            "Outdoors": ComponentColor.FLOOR,
            "Surface": ComponentColor.FLOOR,
            "Ground": ComponentColor.SURFACE_GROUND_CONTACT,
            "Adiabatic": ComponentColor.FLOOR,
        },
    }
    return mapping[str(_hb_face.type)][str(_hb_face.boundary_condition)]


def _hb_ext_color_to_phx_enum(_hb_face: face.Face) -> ComponentColor:
    mapping = {
        "Wall": {
            "Outdoors": ComponentColor.EXT_WALL_OUTER,
            "Surface": ComponentColor.INNER_WALL,
            "Ground": ComponentColor.EXT_WALL_OUTER,
            "Adiabatic": ComponentColor.INNER_WALL,
        },
        "RoofCeiling": {
            "Outdoors": ComponentColor.SLOPED_ROOF_INNER,
            "Surface": ComponentColor.CEILING,
            "Ground": ComponentColor.SURFACE_GROUND_CONTACT,
            "Adiabatic": ComponentColor.CEILING,
        },
        "Floor": {
            "Outdoors": ComponentColor.FLOOR,
            "Surface": ComponentColor.FLOOR,
            "Ground": ComponentColor.SURFACE_GROUND_CONTACT,
            "Adiabatic": ComponentColor.FLOOR,
        },
    }
    return mapping[str(_hb_face.type)][str(_hb_face.boundary_condition)]


def _get_hb_aperture_construction(_hb_aperture) -> window.WindowConstruction:
    """Return the Construction of the Aperture."""
    if hasattr(_hb_aperture.construction, "window_construction"):
        # -- its a WindowConstructionShade, so pull out the normal construction
        return _hb_aperture.construction.window_construction
    else:
        return _hb_aperture.construction


def create_component_from_hb_aperture(
    _host_compo: components.PhxComponentOpaque,
    _hb_aperture: aperture.Aperture,
    _hb_room: room.Room,
    _window_type_dict: Dict[str, constructions.PhxConstructionWindow],
    _tolerance: float = 0.001,
) -> building.PhxComponentAperture:
    """Create a new Transparent (window) Component based on a Honeybee Aperture.

    Arguments:
    ----------
        * _host (components.PhxComponentOpaque): The Aperture's parent opaque component.
        * _hb_aperture (aperture.Aperture): The Honeybee-Aperture to use as the source.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.
        * _window_type_dict (Dict[str, constructions.PhxConstructionWindow]): The Window Type dict.

    Returns:
    --------
        * (building.PhxComponentAperture): A new Transparent (window) Component.
    """

    # -- Type Aliases
    hb_ap_prop_energy: ApertureEnergyProperties = getattr(_hb_aperture.properties, "energy")
    hb_ap_prop_ph: AperturePhProperties = getattr(_hb_aperture.properties, "ph")
    hb_room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    hb_ap_const = _get_hb_aperture_construction(hb_ap_prop_energy)

    # -- Create new Aperture
    phx_ap = components.PhxComponentAperture(_host=_host_compo)
    phx_ap.display_name = _hb_aperture.display_name
    phx_ap.exposure_interior = hb_room_prop_ph.id_num
    phx_ap.window_type = _window_type_dict[hb_ap_const.identifier]
    phx_ap.variant_type_name = hb_ap_prop_ph.variant_type
    phx_ap._install_depth = hb_ap_prop_ph.install_depth
    monthly_fac = getattr(hb_ap_prop_ph, "default_monthly_shading_correction_factor", 1.0)
    phx_ap.default_monthly_shading_correction_factor = monthly_fac

    # -- Create new Aperture Element (Sash)
    new_phx_ap_element = components.PhxApertureElement(_host=phx_ap)
    new_phx_ap_element.display_name = _hb_aperture.display_name
    new_phx_ap_element.polygon = create_geometry.create_PhxPolygonRectangular_from_hb_Face(_hb_aperture, _tolerance)

    # -- Set the shading object dimensions, if there are any
    if hb_ap_prop_ph.shading_dimensions:
        shading_dims = hb_ap_prop_ph.shading_dimensions
        new_phx_ap_element.shading_dimensions.h_hori = shading_dims.h_hori
        new_phx_ap_element.shading_dimensions.d_hori = shading_dims.d_hori
        new_phx_ap_element.shading_dimensions.o_reveal = shading_dims.o_reveal
        new_phx_ap_element.shading_dimensions.d_reveal = shading_dims.d_reveal
        new_phx_ap_element.shading_dimensions.o_over = shading_dims.o_over
        new_phx_ap_element.shading_dimensions.d_over = shading_dims.d_over
    new_phx_ap_element.winter_shading_factor = hb_ap_prop_ph.winter_shading_factor
    new_phx_ap_element.summer_shading_factor = hb_ap_prop_ph.summer_shading_factor

    phx_ap.add_elements((new_phx_ap_element,))

    return phx_ap


def create_components_from_hb_face(
    _hb_face: face.Face,
    _hb_room: room.Room,
    _assembly_dict: Dict[str, constructions.PhxConstructionOpaque],
    _window_type_dict: Dict[str, constructions.PhxConstructionWindow],
    _tolerance: float = 0.001,
) -> components.PhxComponentOpaque:
    """Returns a new Opaque Component (and any child components) based on a Honeybee Face,

    Arguments:
    ----------
        * _hb_face (face.Face): The Honeybee-Face to use as the source.
        * _hb_room (room.Room)L The Honeybee-Room to use as the source.
        * _assembly_dict (Dict[str, constructions.PhxConstructionOpaque]): The Assembly Type dict.
        * _window_type_dict (Dict[str, constructions.PhxConstructionWindow]): The Window Type dict.

    Returns:
    --------
        * (components.PhxComponentOpaque): The new Opaque Component.
    """

    # Type Aliases
    hb_face_prop_energy: FaceEnergyProperties = getattr(_hb_face.properties, "energy")
    hb_face_const = hb_face_prop_energy.construction
    if not hasattr(hb_face_const, "properties"):
        msg = f"Error: Face Construction: '{hb_face_const.display_name}' of type: '{type(hb_face_const)}' is missing a .properties attribute?"
        raise ValueError(msg)
    hb_face_const_prop_ph: OpaqueConstructionPhProperties = getattr(hb_face_const.properties, "ph")  # type: ignore
    hb_room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")

    # -- Build the new PHX Opaque Component
    opaque_compo = components.PhxComponentOpaque()
    opaque_compo.display_name = _hb_face.display_name

    opaque_compo.assembly = _assembly_dict[hb_face_prop_energy.construction.identifier]
    opaque_compo.assembly_type_id_num = hb_face_const_prop_ph.id_num

    opaque_compo.face_type = _hb_face_type_to_phx_enum(_hb_face)
    opaque_compo.face_opacity = _hb_face_opacity_to_phx_enum(_hb_face)
    opaque_compo.exposure_exterior = _hb_ext_exposure_to_phx_enum(_hb_face)
    opaque_compo.exposure_interior = hb_room_prop_ph.id_num
    opaque_compo.color_interior = _hb_int_color_to_phx_enum(_hb_face)
    opaque_compo.color_exterior = _hb_ext_color_to_phx_enum(_hb_face)

    # -- Create Polygon
    phx_polygon = create_geometry.create_PhxPolygon_from_hb_Face(_hb_face)
    opaque_compo.add_polygons(phx_polygon)

    # -- Create Child Apertures, register the Aperture with the Parent Compo
    for hb_aperture in _hb_face.apertures:
        phx_compo_aperture = create_component_from_hb_aperture(
            opaque_compo, hb_aperture, _hb_room, _window_type_dict, _tolerance
        )
        phx_polygon.add_child_poly_id(phx_compo_aperture.polygon_ids)
        opaque_compo.add_aperture(phx_compo_aperture)

    return opaque_compo


def create_components_from_hb_room(
    _hb_room: room.Room,
    _assembly_dict: Dict[str, constructions.PhxConstructionOpaque],
    _window_type_dict: Dict[str, constructions.PhxConstructionWindow],
    _tolerance: float = 0.001,
) -> List[components.PhxComponentOpaque]:
    """Create new Opaque and Transparent PHX-Components based on Honeybee-Room Faces.

    Arguments:
    ----------
        * _hb_room (room.Room): The honeybee-Room to use as the source.
        * _assembly_dict (Dict[str, constructions.PhxConstructionOpaque]): The Assembly Type dict.
        * _assembly_dict (Dict[str, constructions.PhxConstructionWindow]): The Window Type dict.

    Returns:
    --------
        * (List[components.PhxComponentOpaque]): A list of the new opaque PhxComponents.
    """
    return [
        create_components_from_hb_face(hb_face, _hb_room, _assembly_dict, _window_type_dict, _tolerance)
        for hb_face in _hb_room
    ]


def set_zone_occupancy(_hb_room: room.Room, zone: building.PhxZone) -> building.PhxZone:
    """Set the Zone's Residential Occupancy values."""
    # -- Type Aliases
    hb_room_energy_prop: RoomEnergyProperties = getattr(_hb_room.properties, "energy")
    hbph_people_prop: PeoplePhProperties = getattr(hb_room_energy_prop.people.properties, "ph")

    zone.res_occupant_quantity = hbph_people_prop.number_people
    zone.res_number_bedrooms = hbph_people_prop.number_bedrooms
    zone.res_number_dwellings = hbph_people_prop.number_dwelling_units

    return zone


def create_zones_from_hb_room(
    _hb_room: room.Room,
    _vent_sched_collection: UtilizationPatternCollection_Ventilation,
    _occ_sched_collection: UtilizationPatternCollection_Occupancy,
    _lighting_sched_collection: UtilizationPatternCollection_Lighting,
    _merge_spaces_by_erv: bool = False,
) -> building.PhxZone:
    """Create a new PHX-Zone based on a honeybee-Room.

    Arguments:
    ----------
        * _hb_room (room.Room): The honeybee-Room to use as the source.
        * _vent_sched_collection (UtilizationPatternCollection_Ventilation): The Ventilation Schedule Collection.
        * _occ_sched_collection (UtilizationPatternCollection_Occupancy): The Occupancy Schedule Collection.

    Returns:
    --------
        * (building.PhxZone): The new PHX-Zone object.
    """
    new_zone = building.PhxZone()

    new_zone.id_num = building.PhxZone._count
    new_zone.display_name = _hb_room.display_name

    # -- Sort the HB-Room's Spaces by their full_name
    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    sorted_spaces = sorted(room_prop_ph.spaces, key=lambda space: space.full_name)

    # -- Create a new WUFI-Space (Room) for each HBPH-Space
    _create_space = partial(
        create_room_from_space,
        _vent_sched_collection=_vent_sched_collection,
        _occ_sched_collection=_occ_sched_collection,
        _lighting_sched_collection=_lighting_sched_collection,
    )
    new_zone.spaces = [_create_space(sp) for sp in sorted_spaces]

    # -- Set Zone properties
    new_zone.volume_gross = _hb_room.volume
    new_zone.weighted_net_floor_area = sum((rm.weighted_floor_area for rm in new_zone.spaces))
    new_zone.volume_net = sum((rm.net_volume for rm in new_zone.spaces))
    new_zone.specific_heat_capacity = SpecificHeatCapacity(room_prop_ph.specific_heat_capacity.number)
    new_zone.merge_spaces_by_erv = _merge_spaces_by_erv

    # -- Set the Zone's Occupancy based on the merged HB room
    new_zone = set_zone_occupancy(_hb_room, new_zone)

    # -- Set the Zones' thermal bridges
    for phx_thermal_bridge in create_thermal_bridges_from_hb_room(_hb_room):
        new_zone.add_thermal_bridges(phx_thermal_bridge)

    # --  Set the ICFA / TFA Override Values
    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    new_zone.icfa_override = room_prop_ph.ph_bldg_segment.phius_certification.icfa_override
    new_zone.tfa_override = room_prop_ph.ph_bldg_segment.phi_certification.attributes.tfa_override

    return new_zone


def create_thermal_bridges_from_hb_room(
    _hb_room: room.Room,
) -> List[components.PhxComponentThermalBridge]:
    """Create a list of new PHX-ThermalBridges based on those found on a honeybee-Room.

    Arguments:
    ----------
        * _hb_room (room.Room): The honeybee-Room to use as the source.

    Returns:
    --------
        * (List[components.PhxComponentThermalBridge]): A list of the new Thermal Bridge objects.
    """

    # -- Type Aliases
    hb_room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")

    # -- Create all the new Thermal Bridges
    phx_thermal_bridges = []
    for thermal_bridge in sorted(
        hb_room_prop_ph.ph_bldg_segment.thermal_bridges.values(),
        key=lambda tb: tb.display_name,
    ):
        phx_tb = components.PhxComponentThermalBridge()
        phx_tb.display_name = thermal_bridge.display_name
        phx_tb.quantity = thermal_bridge.quantity
        phx_tb.group_type = ThermalBridgeType(thermal_bridge.group_type.number)
        phx_tb.identifier = str(thermal_bridge.identifier)
        phx_tb.psi_value = thermal_bridge.psi_value
        phx_tb.fRsi_value = thermal_bridge.fRsi_value
        phx_tb.length = thermal_bridge.length
        phx_thermal_bridges.append(phx_tb)

    return phx_thermal_bridges
