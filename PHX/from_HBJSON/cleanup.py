# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions used to cleanup / optimize Honeybee-Rooms before outputting to WUFI"""

import logging
from typing import Dict, List, Optional, Set

try:  # import the core honeybee dependencies
    from honeybee import face, room
    from honeybee.boundarycondition import Ground, Outdoors, Surface
    from honeybee.properties import FaceProperties
    from honeybee.typing import clean_ep_string
    from honeybee_energy import shw
except ImportError as e:
    raise ImportError("\nFailed to import honeybee:\n\t{}".format(e))

try:
    from honeybee_energy.load import equipment, infiltration, people, process
    from honeybee_energy.load.infiltration import Infiltration
    from honeybee_energy.properties.face import FaceEnergyProperties
    from honeybee_energy.properties.room import RoomEnergyProperties
except ImportError as e:
    raise ImportError("\nFailed to import honeybee_energy:\n\t{}".format(e))

try:
    from honeybee_ph.foundations import PhFoundation
    from honeybee_ph.properties.room import RoomPhProperties
except ImportError as e:
    raise ImportError("\nFailed to import honeybee_ph:\n\t{}".format(e))

try:
    from honeybee_energy_ph.load.ph_equipment import PhEquipment
    from honeybee_energy_ph.properties.load.equipment import ElectricEquipmentPhProperties
    from honeybee_energy_ph.properties.load.people import PeoplePhProperties, PhDwellings
    from honeybee_energy_ph.properties.load.process import ProcessPhProperties
except ImportError as e:
    raise ImportError("\nFailed to import honeybee_energy_ph:\n\t{}".format(e))

try:
    from PHX.from_HBJSON.cleanup_merge_faces import merge_hb_faces
    from PHX.model import project
except ImportError as e:
    raise ImportError("\nFailed to import PHX:\n\t{}".format(e))

try:
    from honeybee_ph_utils import face_tools
except ImportError as e:
    raise ImportError("\nFailed to import honeybee_ph_utils:\n\t{}".format(e))

logger = logging.getLogger()


def _dup_face(_hb_face: face.Face) -> face.Face:
    """Duplicate a Honeybee Face and all it's properties.

    Arguments:
    ----------
        *_hb_face: (face.Face) The face to copy

    Returns:
    --------
        * (face.Face): The duplicate face.
    """

    new_face: face.Face = _hb_face.__copy__()
    new_face._properties._duplicate_extension_attr(_hb_face._properties)

    # -- Note, this is required if the user has set custom .energy constructions
    # -- or other custom face-specific attributes
    # -- Duplicate any extensions like .ph, .energy or .radiance
    face_prop: Optional[FaceProperties] = _hb_face._properties
    if not face_prop:
        return new_face

    for extension_name in face_prop._extension_attributes:
        # -- Use try...except... to avoid the bug introduced in HB v1.5
        # TODO: fix Honeybee and then remove this try...except...
        try:
            original_extension = getattr(_hb_face._properties, f"_{extension_name}", None)
            if not original_extension:
                continue
            new_extension = original_extension.__copy__()
            setattr(new_face._properties, f"_{extension_name}", new_extension)
        except:
            pass

    return new_face


def _get_thermal_envelope_faces(_hb_room: room.Room, _all_room_ids: List[str]) -> List[face.Face]:
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

        # -- Copy the Face, but be sure to set the construction explicitly
        # -- We have to do this to make sure we don't lose any face-constructions
        # -- which are being applied by 'Construction Sets'.
        dup_face = _dup_face(original_face)
        original_face_prop_e: FaceEnergyProperties = getattr(original_face.properties, "energy")
        dup_face_prop_e: FaceEnergyProperties = getattr(dup_face.properties, "energy")
        dup_face_prop_e.construction = original_face_prop_e.construction
        exposed_faces.append(dup_face)

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

    return sum(fc.area for fc in _hb_room.faces if isinstance(fc.boundary_condition, (Outdoors, Ground)))


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
        room.properties.energy.people.properties.ph.dwellings  # type: ignore
        for room in _hb_rooms
        if room.properties.energy.people  # type: ignore
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
        hb_room_prop_energy: RoomEnergyProperties = getattr(hb_room.properties, "energy")
        hb_ppl_obj = hb_room_prop_energy.people

        # -- Sometimes there is no 'People'
        if hb_ppl_obj is None:
            continue

        hbph_people_prop_ph: PeoplePhProperties = getattr(hb_ppl_obj.properties, "ph")
        total_ph_bedrooms += int(hbph_people_prop_ph.number_bedrooms)
        total_ph_people += float(hbph_people_prop_ph.number_people)
        total_hb_people += hb_ppl_obj.people_per_area * hb_room.floor_area

    # -------------------------------------------------------------------------
    # -- Build up the new People object's attributes
    total_floor_area = sum(rm.floor_area for rm in _hb_rooms)
    new_hb_prop_energy: RoomEnergyProperties = getattr(_hb_rooms[0].properties, "energy")
    if not new_hb_prop_energy.people:
        raise ValueError(f"Error: No 'people' found on room: {_hb_rooms[0].display_name}?")
    new_hb_ppl: people.People = new_hb_prop_energy.people.__copy__()
    new_hb_ppl_prop_ph: PeoplePhProperties = getattr(new_hb_ppl.properties, "ph")
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
        room_prop_energy: RoomEnergyProperties = getattr(room.properties, "energy")
        room_infil_m3_s = room_infil_exposed_area * room_prop_energy.infiltration.flow_per_exterior_area

        total_exposed_area += room_infil_exposed_area
        total_m3_s += room_infil_m3_s

    # -- Set the new Infiltration Object's attr to the weighted average
    reference_room = _hb_rooms[0]
    reference_room_prop_energy: RoomEnergyProperties = getattr(reference_room.properties, "energy")
    new_infil: Infiltration = reference_room_prop_energy.infiltration.duplicate()  # type: ignore
    try:
        new_infil.flow_per_exterior_area = total_m3_s / total_exposed_area
    except ZeroDivisionError:
        new_infil.flow_per_exterior_area = 0.0

    return new_infil


def merge_shw_programs(_hb_rooms: List[room.Room]) -> shw.SHWSystem:
    """Merge together several HB-Room's Honeybee-Energy SHW System objects (if they exist).

    Arguments:
    ----------
        * _hb_rooms (List[room.Room]): The list of Honeybee Rooms to get the
            SHW System System from.

    Returns:
    --------
        * (shw.SHWSystem): A single new Honeybee-Energy SHW System Object.
    """

    # -- Find all the unique SHW Programs in the Model
    shw_programs: Set[shw.SHWSystem] = set()
    for room in _hb_rooms:
        room_prop_energy: RoomEnergyProperties = getattr(room.properties, "energy")
        if room_prop_energy.shw:
            shw_programs.add(room_prop_energy.shw)

    if len(shw_programs) > 1:
        print(f"Warning: More than one SHW Program Type found in the model.")

    return shw.SHWSystem(
        identifier=clean_ep_string("_default_shw_system_"),
        equipment_type="Electric_WaterHeater",
    )


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
        room_prop_energy: RoomEnergyProperties = getattr(room.properties, "energy")
        room_ee_prop = room_prop_energy.electric_equipment.properties
        room_ee_prop_ph: ElectricEquipmentPhProperties = getattr(room_ee_prop, "ph")

        # TODO: Deprecate...
        # -- Get the Equipment from the HB-Elec-Equip (old method < Jan 2025)
        for equip_key, equip in room_ee_prop_ph.equipment_collection.items():
            try:
                ph_equipment[equip_key].quantity += 1
            except KeyError:
                ph_equipment[equip_key] = equip

    # -- Calculate the total Watts of all of the HBE-Elec-Equipment in the rooms
    total_floor_area = sum(rm.floor_area for rm in _hb_rooms)
    total_watts = sum(
        (rm.floor_area * rm.properties.energy.electric_equipment.watts_per_area) for rm in _hb_rooms  # type: ignore
    )

    # -- Build a new HBE-Elec-Equip from the reference room, add all the PH-Equipment to it.
    reference_room = _hb_rooms[0]
    reference_room_prop_energy: RoomEnergyProperties = getattr(reference_room.properties, "energy")
    ref_room_ee: equipment.ElectricEquipment = reference_room_prop_energy.electric_equipment

    new_hb_equip: equipment.ElectricEquipment = ref_room_ee.duplicate()  # type: ignore
    new_hb_equip.watts_per_area = total_watts / total_floor_area
    new_hb_equip_prop_ph: ElectricEquipmentPhProperties = getattr(new_hb_equip.properties, "ph")
    new_hb_equip_prop_ph.equipment_collection.remove_all_equipment()

    for ph_item in ph_equipment.values():
        new_hb_equip_prop_ph.equipment_collection.add_equipment(ph_item)

    return new_hb_equip


def merge_process_loads(_hb_rooms: list[room.Room]) -> list[process.Process]:
    """Returns a new HB-Process-Obj with it's values set from a list of input HB-Rooms.

    Arguments:
    ----------
        * _hb_rooms (List[room.Room]): A list of the HB-Rooms to build the merged
            HB-Process object from.

    Returns:
    --------
        * (list[process.Process]): A list with new Honeybee Process objects with values merged from the HB-Rooms.
    """
    # -- Collect all the unique Process-Load/PH-Equipment in all the rooms.
    # -- Increase the quantity for each duplicate piece of equipment found
    ph_equipment: dict[str, process.Process] = {}
    for room in _hb_rooms:
        room_prop_energy: RoomEnergyProperties = getattr(room.properties, "energy")
        process_loads: tuple[process.Process] = room_prop_energy.process_loads

        # -- Get the Equipment from the HB-Process Load (new method > Jan 2025)
        for process_load in process_loads:
            process_prop_ph: ProcessPhProperties = getattr(process_load.properties, "ph")
            if equip := getattr(process_prop_ph, "ph_equipment", None):  # type: PhEquipment | None
                if equip.identifier in ph_equipment:
                    process_prop_ph: ProcessPhProperties = getattr(ph_equipment[equip.identifier].properties, "ph")
                    if process_prop_ph.ph_equipment:
                        process_prop_ph.ph_equipment.quantity += 1
                    else:
                        ph_equipment[equip.identifier] = process_load
                else:
                    ph_equipment[equip.identifier] = process_load

    return list(ph_equipment.values())


def check_room_has_spaces(_hb_room: room.Room) -> None:
    rm_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    if len(rm_prop_ph.spaces) == 0:
        print(f"Warning: Room '{_hb_room.display_name}' has no spaces?" " Merge may not work correctly")


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
        room_prop_ph: RoomPhProperties = getattr(rm.properties, "ph")
        foundations = room_prop_ph.ph_foundations
        for foundation in foundations:
            foundation_groups[foundation.identifier] = foundation

    # -- Warn if more than 3 of them
    if len(foundation_groups) > 3:
        room_prop_ph: RoomPhProperties = getattr(_hb_rooms[0].properties, "ph")
        name = room_prop_ph.ph_bldg_segment.display_name
        msg = (
            f"\tWarning: WUFI-Passive only allows 3 Foundation types. "
            f" {len(foundation_groups)} found on the Building Segment '"
            f"{name}'?"
        )
        print(msg)

    return foundation_groups


def merge_rooms(
    _hb_rooms: List[room.Room],
    _tolerance: float,
    _angle_tolerance_degrees: float,
    _merge_faces: bool = False,
) -> room.Room:
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

    # -------------------------------------------------------------------------
    # -- Try and merge the Faces to simplify the geometry
    if _merge_faces:
        logger.debug(f"Merging Faces with tolerance: {_tolerance}")
        face_groups = face_tools.group_hb_faces(exposed_faces, _tolerance, _angle_tolerance_degrees)
        merged_faces = []
        for face_group in face_groups:
            const_name = face_group[0].properties.energy.construction.display_name
            logger.debug(f"Merging {len(face_group)} Faces with Construction: {const_name}")
            merged_faces.extend(merge_hb_faces(face_group, _tolerance, _angle_tolerance_degrees))
        exposed_faces = merged_faces

    # -------------------------------------------------------------------------
    # Build the new room from the exposed (possibly merged) faces
    room_ph_prop: RoomPhProperties = getattr(reference_room.properties, "ph")
    new_room = room.Room(
        identifier=room_ph_prop.ph_bldg_segment.display_name,
        faces=exposed_faces,
    )

    # -------------------------------------------------------------------------
    # -- Set the new Merged-Room's properties.ph and
    # -- properties.energy to match the 'reference' room to start with, but leave
    # -- off the PH-Spaces so they don't get duplicated
    ref_rm_prop_ph: RoomPhProperties = getattr(reference_room.properties, "ph")
    new_rm_prop_ph: RoomPhProperties = getattr(new_room.properties, "ph")
    dup_ph_prop = ref_rm_prop_ph.duplicate(new_rm_prop_ph, include_spaces=False)
    dup_ph_prop._ph_foundations = merge_foundations(_hb_rooms)
    setattr(new_room._properties, "_ph", dup_ph_prop)

    ref_rm_prop_energy: RoomEnergyProperties = getattr(reference_room.properties, "energy")
    new_rm_prop_energy: RoomEnergyProperties = getattr(new_room.properties, "energy")
    dup_energy_prop = ref_rm_prop_energy.duplicate(new_rm_prop_energy)
    setattr(new_room._properties, "_energy", dup_energy_prop)

    # -------------------------------------------------------------------------
    # -- Then, collect all the spaces from the input rooms and add to the NEW room
    # -- NOTE: this has to be done AFTER the duplicate()
    # -- call, otherwise not all the spaces will transfer over properly.
    for hb_room in _hb_rooms:
        check_room_has_spaces(hb_room)

        rm_prop_ph: RoomPhProperties = getattr(hb_room.properties, "ph")
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

            new_rm_prop_ph: RoomPhProperties = getattr(new_room.properties, "ph")
            new_rm_prop_ph.add_new_space(existing_space)

    # -------------------------------------------------------------------------
    # -- Merge the hb_rooms' load values
    new_rm_prop_energy: RoomEnergyProperties = getattr(new_room.properties, "energy")
    new_rm_prop_energy.infiltration = merge_infiltrations(_hb_rooms)
    new_rm_prop_energy.people = merge_occupancies(_hb_rooms)
    new_rm_prop_energy.electric_equipment = merge_elec_equip(_hb_rooms)
    new_rm_prop_energy.shw = merge_shw_programs(_hb_rooms)
    new_rm_prop_energy.remove_process_loads()
    new_rm_prop_energy._process_loads = merge_process_loads(_hb_rooms)

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
                    # -- See if the vertex is already in the dict,
                    # --if so, use that one.
                    vertex_from_dict = unique_vertix_dict[vert.unique_key]
                    polygon.set_vertex(vertex_from_dict, i)
                except KeyError:
                    # -- If the vertex is not in the dict, add it.
                    unique_vertix_dict[vert.unique_key] = vert

    return _variant
