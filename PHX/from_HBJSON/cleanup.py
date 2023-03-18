# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions used to cleanup / optimize Honeybee-Rooms before outputting to WUFI"""

from collections import defaultdict
from typing import List, Dict
from functools import reduce


try:  # import the core honeybee dependencies
    from honeybee.typing import clean_ep_string
except ImportError as e:
    raise ImportError("\nFailed to import honeybee:\n\t{}".format(e))

try:
    from honeybee import room, face
    from honeybee.properties import FaceProperties
    from honeybee_energy import shw
    from honeybee.boundarycondition import Outdoors, Ground, Surface
except ImportError as e:
    raise ImportError("\nFailed to import honeybee:\n\t{}".format(e))

try:
    from honeybee_energy.load import people, equipment, infiltration
    from honeybee_energy.load.infiltration import Infiltration
    from honeybee_energy.properties.room import RoomEnergyProperties
except ImportError as e:
    raise ImportError("\nFailed to import honeybee_energy:\n\t{}".format(e))

try:
    from honeybee_ph.properties.room import RoomPhProperties
    from honeybee_ph.foundations import PhFoundation
except ImportError as e:
    raise ImportError("\nFailed to import honeybee_ph:\n\t{}".format(e))

try:
    from honeybee_energy_ph.properties.load.equipment import ElectricEquipmentPhProperties
    from honeybee_energy_ph.properties.hot_water.hw_system import SHWSystemPhProperties
    from honeybee_energy_ph.properties.load.people import PeoplePhProperties, PhDwellings
except ImportError as e:
    raise ImportError("\nFailed to import honeybee_energy_ph:\n\t{}".format(e))

try:
    from PHX.model import project
except ImportError as e:
    raise ImportError("\nFailed to import PHX:\n\t{}".format(e))


def _dup_face(_hb_face: face.Face) -> face.Face:
    """Duplicate a Honeybee Face and all it's properties.

    Arguments:
    ----------
        *_hb_face: (face.Face) The face to copy

    Returns:
    --------
        * (face.Face): The duplicate face.
    """

    new_face = _hb_face.duplicate() # type: face.Face # type: ignore
    new_face._properties._duplicate_extension_attr(_hb_face._properties)

    # -- Note, this is required if the user has set custom .energy constructions
    # -- or other custom face-specific attributes
    # -- Duplicate any extensions like .ph, .energy or .radiance
    face_prop: FaceProperties = _hb_face.properties  # type: ignore
    for extension_name in face_prop._extension_attributes:
        # -- use try except to avoid the bug introduced in HB v1.5
        # TODO: fix Honeybee and then remove this try...except...
        try:
            original_extension = getattr(_hb_face._properties, f"_{extension_name}", None)
            new_extension = original_extension.duplicate()  # type: ignore
            setattr(new_face._properties, f"_{extension_name}", new_extension)
        except:
            pass

    return new_face


def _get_thermal_envelope_faces(
    _hb_room: room.Room, _all_room_ids: List[str]
) -> List[face.Face]:
    """Return a list of all the thermal-envelope faces for a Honeybee Room.

    This will include all the 'Outdoor', 'Ground' and 'Adiabatic' faces.
    If an 'Surface' faces are found, they will only be included IF they do NOT
    have exposure to another HB-Room in the set. This will omit any 'interior'
    surfaces, but will retain any surfaces which are exposed to an HB-Room which
    is part of another set (building segment). ie: the floor of a residential
    tower which is exposed to the ceiling of a commercial podium.

    Arguments:
    ----------
        *_hb_room: (room.Room) The room to get the faces from.
        * _all_room_ids: List[str] The list of all the room-group (building segment) IDs

    Returns:
    --------
        * (List[face.Face]) A List of all the thermal boundary faces.
    """

    exposed_faces: List[face.Face] = []
    for original_face in _hb_room.faces:

        # -- If it is a Surface exposure, but the face's adjacent zone is NOT part of
        # -- the room group, it must be exposed to another zone (ie: the floor surface
        # -- of a residential tower exposed to the commercial zone below). So
        face_bc = original_face.boundary_condition
        if isinstance(face_bc, Surface):
            adjacent_room_name = face_bc.boundary_condition_objects[-1]
            if adjacent_room_name in _all_room_ids:
                continue

        exposed_faces.append(_dup_face(original_face))

    return exposed_faces


def _get_room_exposed_face_area(_hb_room: room.Room) -> float:
    """Returns the total surface area for all the 'exposed' faces (Ground / Outdoors) of a HB-Room
    For Phius, infiltration-exposed surfaces include all, including 'Ground'
    unlike for Honeybee where only 'Outdoors' count as 'exposed'

    Arguments:
    ----------
        *_hb_room: (room.Room) The Honeybee Room to get the surfaces of.

    Returns:
    --------
        * (float) The total surface area.
    """

    return sum(
        fc.area
        for fc in _hb_room.faces
        if isinstance(fc.boundary_condition, (Outdoors, Ground))
    )


def all_unique_ph_dwelling_objects(_hb_rooms: List[room.Room]) -> List[PhDwellings]:
    """Return a list of all the unique PhDwelling objects from a set of HB-Rooms.
    
    Arguments:
    ----------
        * _hb_rooms (List[room.Room]): A list of the HB-Rooms
    
    Returns:
    --------
        * (List[PhDwellings])
    """
    dwellings = {
                room.properties.energy.people.properties.ph.dwellings #type: ignore
                for room in _hb_rooms
                if room.properties.energy.people # type: ignore
                } 
    return list(dwellings)


def merge_occupancies(_hb_rooms: List[room.Room]) -> people.People:
    """Returns a new HB-People-Obj with it's values set from a list of input HB-Rooms.

    Arguments:
    ----------
        * _hb_rooms (List[room.Room]): A list of the HB-Rooms to build the merged
            HB-People object from.

    Return:
    -------
        * (people.People): A new Honeybee People object with values merged from the HB-Rooms.
    """

    # -------------------------------------------------------------------------
    # Calculate the total dwelling-unit count. Ensure always at least 1 (even Non-Res)
    total_ph_dwellings = 0
    for dwelling_obj in all_unique_ph_dwelling_objects(_hb_rooms):
        total_ph_dwellings += int(dwelling_obj.num_dwellings)
    merged_ph_dwellings = PhDwellings(_num_dwellings=max(total_ph_dwellings, 1))

    # -------------------------------------------------------------------------
    # -- Merge all the Rooms
    total_ph_bedrooms = 0
    total_ph_people = 0.0
    total_hb_people = 0.0
    for hb_room in _hb_rooms:
        # -- Type Aliases
        hb_room_prop_energy: RoomEnergyProperties = hb_room.properties.energy  # type: ignore
        hb_ppl_obj = hb_room_prop_energy.people

        # -- Sometimes there is no 'People'
        if hb_ppl_obj is None:
            continue

        hbph_people_prop_ph: PeoplePhProperties = hb_ppl_obj.properties.ph  # type: ignore
        total_ph_bedrooms += int(hbph_people_prop_ph.number_bedrooms)
        total_ph_people += float(hbph_people_prop_ph.number_people)
        total_hb_people += hb_ppl_obj.people_per_area * hb_room.floor_area

    # -------------------------------------------------------------------------
    # -- Build up the new People object's attributes
    total_floor_area = sum(rm.floor_area for rm in _hb_rooms)
    new_hb_prop_energy = _hb_rooms[0].properties.energy  # type: RoomEnergyProperties # type: ignore
    new_hb_ppl = new_hb_prop_energy.people.duplicate()  # type: people.People # type: ignore
    new_hb_ppl_prop_ph = new_hb_ppl.properties.ph  # type: PeoplePhProperties # type: ignore
    new_hb_ppl.people_per_area = total_hb_people / total_floor_area
    new_hb_ppl_prop_ph.number_bedrooms = total_ph_bedrooms
    new_hb_ppl_prop_ph.number_people = total_ph_people
    new_hb_ppl_prop_ph.dwellings = merged_ph_dwellings

    return new_hb_ppl


def merge_infiltrations(_hb_rooms: List[room.Room]) -> infiltration.Infiltration:
    """Returns a new HB-Infiltration-Obj with it's values set from a list of input HB-Rooms.

    Arguments:
    ----------
        * _hb_rooms (List[room.Room]): A list of the HB-Rooms to build the merged
            HB-Infiltration object from.

    Return:
    -------
        * (infiltration.Infiltration): A new Honeybee Infiltration object
            with values merged from the HB-Rooms.
    """

    # -- Calculate the total airflow per room, total exposed area per room
    total_m3_s = 0.0
    total_exposed_area = 0.0
    for room in _hb_rooms:
        room_infil_exposed_area = _get_room_exposed_face_area(room)
        room_prop_energy: RoomEnergyProperties = room.properties.energy  # type: ignore
        room_infil_m3_s = (
            room_infil_exposed_area * room_prop_energy.infiltration.flow_per_exterior_area
        )

        total_exposed_area += room_infil_exposed_area
        total_m3_s += room_infil_m3_s

    # -- Set the new Infiltration Object's attr to the weighted average
    reference_room = _hb_rooms[0]
    reference_room_prop_energy: RoomEnergyProperties = reference_room.properties.energy  # type: ignore
    new_infil: Infiltration = reference_room_prop_energy.infiltration.duplicate()  # type: ignore
    try:
        new_infil.flow_per_exterior_area = total_m3_s / total_exposed_area
    except ZeroDivisionError:
        new_infil.flow_per_exterior_area = 0.0

    return new_infil


def merge_shw(_hb_rooms: List[room.Room]) -> shw.SHWSystem:
    """Merge together several HB-Room's Honeybee-Energy SHW System objects (if they exist).

    Arguments:
    ----------
        * _hb_rooms (List[room.Room]): The list of Honeybee Rooms to get the
            SHW System System from.

    Returns:
    --------
        * (shw.SHWSystem): A single new Honeybee-Energy SHW System Object.
    """

    # -- Find the first HBE SHWSystem System in the list of HB-Rooms, and use that as the 'base'
    for room in _hb_rooms:
        room_prop_energy: RoomEnergyProperties = room.properties.energy  # type: ignore
        if room_prop_energy.shw:
            new_shw: shw.SHWSystem = room_prop_energy.shw.duplicate()
            break
    else:
        # -- If no SHWSystem found anywhere, return a new default HBE SHWSystem System
        return shw.SHWSystem(
            identifier=clean_ep_string("_default_shw_system_"),
            equipment_type="Electric_WaterHeater",
        )

    # -- Merge the SHWSystemPhProperties and then apply it to the new HBE SHWSystem System
    shw_props: List[SHWSystemPhProperties] = [
        hb_room.properties.energy.shw.properties.ph  # type: ignore
        for hb_room in _hb_rooms
        if hb_room.properties.energy.shw  # type: ignore
    ]

    new_prop = reduce(lambda a, b: a + b, shw_props)
    new_shw.properties._ph = new_prop  # type: ignore

    return new_shw


def merge_elec_equip(_hb_rooms: List[room.Room]) -> equipment.ElectricEquipment:
    """Returns a new HB-ElectricEquipment-Obj with it's values set from a list of input HB-Rooms.

    Arguments:
    ----------
        * _hb_rooms (List[room.Room]): A list of the HB-Rooms to build the merged
            HB-ElectricEquipment object from.

    Return:
    -------
        * (equipment.ElectricEquipment): A new Honeybee ElectricEquipment object
            with values merged from the HB-Rooms.
    """

    # -- Collect all the unique PH-Equipment in all the rooms.
    # -- Increase the quantity for each duplicate piece of equipment found.
    ph_equipment = {}
    for room in _hb_rooms:
        room_prop_energy: RoomEnergyProperties = room.properties.energy  # type: ignore
        room_ee_prop = room_prop_energy.electric_equipment.properties
        room_ee_prop_ph: ElectricEquipmentPhProperties = room_ee_prop.ph  # type: ignore

        for equip_key, equip in room_ee_prop_ph.equipment_collection.items():
            try:
                ph_equipment[equip_key].quantity += 1
            except KeyError:
                ph_equipment[equip_key] = equip

    # -- Calculate the total Watts of elec-equipment, total floor-area
    total_floor_area = sum(rm.floor_area for rm in _hb_rooms)
    total_watts = sum(
        (rm.floor_area * rm.properties.energy.electric_equipment.watts_per_area)  # type: ignore
        for rm in _hb_rooms
    )

    # -- Build a new HB-Elec-Equip from the reference room, add all the PH-Equipment to it.
    reference_room = _hb_rooms[0]
    reference_room_prop_energy: RoomEnergyProperties = reference_room.properties.energy  # type: ignore
    ref_room_ee: equipment.ElectricEquipment = (
        reference_room_prop_energy.electric_equipment
    )

    new_hb_equip: equipment.ElectricEquipment = ref_room_ee.duplicate()  # type: ignore
    new_hb_equip.watts_per_area = total_watts / total_floor_area
    new_hb_equip_prop_ph: ElectricEquipmentPhProperties = new_hb_equip.properties.ph  # type: ignore
    new_hb_equip_prop_ph.equipment_collection.remove_all_equipment()

    for ph_item in ph_equipment.values():
        new_hb_equip_prop_ph.equipment_collection.add_equipment(ph_item)

    return new_hb_equip


def check_room_has_spaces(_hb_room: room.Room) -> None:
    rm_prop_ph: RoomPhProperties = _hb_room.properties.ph  # type: ignore
    if len(rm_prop_ph.spaces) == 0:
        print(
            f"Warning: Room '{_hb_room.display_name}' has no spaces?"
            " Merge may not work correctly"
        )


def merge_foundations(_hb_rooms: List[room.Room]) -> Dict[str, PhFoundation]:
    """
    
    Arguments:
    ----------
        *
    
    Returns:
    --------
        *
    """

    # -- Group by Identifier
    foundation_groups = {}
    for rm in _hb_rooms:
        for foundation in rm.properties.ph.ph_foundations:
            foundation_groups[foundation.identifier] = foundation
    
    # -- Warn if more than 3 of them
    if len(foundation_groups) > 3:
        msg = f"\tWarning: WUFI-Passive only allows 3 Foundation types. "\
            f" {len(foundation_groups)} found on the Building Segment '"\
            f"{_hb_rooms[0].properties.ph.ph_bldg_segment.display_name}'?"
        print(msg)

    return foundation_groups


def merge_rooms(_hb_rooms: List[room.Room]) -> room.Room:
    """Merge together a group of Honeybee Rooms into a new single HB Room.

    This will ignore any 'interior' Honeybee-Faces with a 'Surface' boundary
    condition and will only keep the 'exposed' Honeybee Faces with boundary_conditions
    of 'Outdoors', 'Ground' and 'Adiabatic' to build the new Honeybee Room from.

    Arguments:
    ----------
        * _hb_rooms (list[room.Room]):

    Returns:
    --------
        * room.Room: The new Honeybee Room.
    """
    reference_room = _hb_rooms[0]

    # -------------------------------------------------------------------------
    # Collect all the HB-Room names for Surface adjacency checking
    all_hb_room_identifiers = [rm.identifier for rm in _hb_rooms]

    # -------------------------------------------------------------------------
    # -- Get only the 'exposed' thermal envelope faces to build a new HB-Room with
    exposed_faces = []
    for hb_room in _hb_rooms:
        exposed_faces += _get_thermal_envelope_faces(hb_room, all_hb_room_identifiers)

    new_room = room.Room(
        identifier=reference_room.properties.ph.ph_bldg_segment.display_name,  # type: ignore
        faces=exposed_faces,
    )

    # -------------------------------------------------------------------------
    # -- Set the new Merged-Room's properties.ph and
    # -- properties.energy to match the 'reference' room to start with, but leave
    # -- off the PH-Spaces so they don't get duplicated
    ref_rm_prop_ph: RoomPhProperties = reference_room.properties.ph  # type: ignore
    new_rm_prop_ph: RoomPhProperties = new_room.properties.ph  # type: ignore
    dup_ph_prop = ref_rm_prop_ph.duplicate(new_rm_prop_ph, include_spaces=False)
    dup_ph_prop._ph_foundations = merge_foundations(_hb_rooms)
    setattr(new_room._properties, "_ph", dup_ph_prop)

    ref_rm_prop_energy: RoomEnergyProperties = reference_room.properties.energy  # type: ignore
    new_rm_prop_energy: RoomEnergyProperties = new_room.properties.energy  # type: ignore
    dup_energy_prop = ref_rm_prop_energy.duplicate(new_rm_prop_energy)
    setattr(new_room._properties, "_energy", dup_energy_prop)

    # -------------------------------------------------------------------------
    # -- Then, collect all the spaces from the input rooms and add to the NEW room
    # -- NOTE: this has to be done AFTER the duplicate()
    # -- call, otherwise not all the spaces will transfer over properly.
    for hb_room in _hb_rooms:
        check_room_has_spaces(hb_room)

        rm_prop_ph: RoomPhProperties = hb_room.properties.ph  # type: ignore
        for existing_space in rm_prop_ph.spaces:
            # -- Preserve the space host HB-Room's .energy and .ph properties over
            # -- on the space itself. We need to do this cus' the host HB-Room is being
            # -- removed and we want to preserve HVAC and program info for the spaces.
            existing_space.properties._energy = hb_room.properties._energy.duplicate(  # type: ignore
                new_host=existing_space
            )
            # TODO: Verify that this can be removed without causing any issues?
            # Note: it it also wrong - RoomPhProperties are being applied over SpacePhProperties.
            # existing_space.properties._ph = hb_room.properties._ph.duplicate(
            #     new_host=existing_space)

            new_rm_prop_ph: RoomPhProperties = new_room.properties.ph  # type: ignore
            new_rm_prop_ph.add_new_space(existing_space)

    # -------------------------------------------------------------------------
    # -- Merge the hb_rooms' load values
    new_rm_prop_energy: RoomEnergyProperties = new_room.properties.energy  # type: ignore
    new_rm_prop_energy.infiltration = merge_infiltrations(_hb_rooms)
    new_rm_prop_energy.people = merge_occupancies(_hb_rooms)
    new_rm_prop_energy.electric_equipment = merge_elec_equip(_hb_rooms)
    new_rm_prop_energy.shw = merge_shw(_hb_rooms)

    # -------------------------------------------------------------------------
    # -- TODO: Can I merge together the surfaces as well?
    # -- For larger models, I think this will be important.... hmm....
    # -- Organize the surfaces by -> assembly / exposure / orientation (normal)

    return new_room


def weld_vertices(_variant: project.PhxVariant) -> project.PhxVariant:
    """
    Used to try and weld/unify the vertices of a variant.

    This is helpful to reduce the complexity / number of variants in a large
    model so that WUFI can actually open it.

    Arguments:
    ----------
        * _variant (project.Variant): The Variant object to weld the vertices for.

    Returns:
    --------
        * (project.Variant): The variant, with its vertix objects welded.

    """

    unique_vertix_dict = {}
    for component in _variant.building.all_components:
        for polygon in component.polygons:
            for i, vert in enumerate(polygon.vertices):
                try:
                    vert = polygon.vertices[i] = unique_vertix_dict[vert.unique_key]
                except KeyError:
                    unique_vertix_dict[vert.unique_key] = vert

    return _variant
