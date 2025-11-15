# -*- Python Version: 3.10 -*-

"""Type-safe utility functions for accessing Honeybee energy properties.

This module provides wrapper functions with proper type hints to ensure that
None values are handled correctly. These functions are intentionally typed
to return non-Optional types, which forces calling code to handle None cases
explicitly, making type checkers report errors where None handling is missing.
"""

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from honeybee import aperture, face, room
    from honeybee_energy.load.equipment import ElectricEquipment
    from honeybee_energy.load.infiltration import Infiltration
    from honeybee_energy.load.people import People
    from honeybee_energy.load.ventilation import Ventilation
    from honeybee_energy.properties.aperture import ApertureEnergyProperties
    from honeybee_energy.properties.face import FaceEnergyProperties
    from honeybee_energy.properties.room import RoomEnergyProperties
    from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval
    from honeybee_energy.schedule.ruleset import ScheduleRuleset
    from honeybee_ph import space as hb_space

    # Type alias for schedule types
    HBESchedule = Union[ScheduleRuleset, ScheduleFixedInterval]


class MissingEnergyPropertiesError(Exception):
    """Raised when required energy properties are missing from a Honeybee object."""

    def __init__(self, obj_name: str, property_name: str):
        self.message = (
            f"Error: Honeybee object '{obj_name}' is missing required energy property: "
            f"'{property_name}'. Cannot proceed with PHX conversion."
        )
        super().__init__(self.message)


def get_room_energy_properties(hb_room: "room.Room") -> "RoomEnergyProperties":
    """Get energy properties from a Honeybee Room.

    This function returns the energy properties with a non-Optional type hint,
    which forces calling code to handle the case where energy properties might
    not exist. This makes type checkers report errors at call sites that don't
    handle None properly.

    Arguments:
    ----------
        * hb_room (room.Room): The Honeybee Room.

    Returns:
    --------
        * (RoomEnergyProperties): The room's energy properties.

    Raises:
    -------
        * MissingEnergyPropertiesError: If the room has no energy properties.
    """
    energy_props = getattr(hb_room.properties, "energy", None)
    if energy_props is None:
        raise MissingEnergyPropertiesError(hb_room.display_name, "energy")
    return energy_props


def get_face_energy_properties(hb_face: "face.Face") -> "FaceEnergyProperties":
    """Get energy properties from a Honeybee Face.

    Arguments:
    ----------
        * hb_face (face.Face): The Honeybee Face.

    Returns:
    --------
        * (FaceEnergyProperties): The face's energy properties.

    Raises:
    -------
        * MissingEnergyPropertiesError: If the face has no energy properties.
    """
    energy_props = getattr(hb_face.properties, "energy", None)
    if energy_props is None:
        raise MissingEnergyPropertiesError(hb_face.display_name, "energy")
    return energy_props


def get_aperture_energy_properties(hb_aperture: "aperture.Aperture") -> "ApertureEnergyProperties":
    """Get energy properties from a Honeybee Aperture.

    Arguments:
    ----------
        * hb_aperture (aperture.Aperture): The Honeybee Aperture.

    Returns:
    --------
        * (ApertureEnergyProperties): The aperture's energy properties.

    Raises:
    -------
        * MissingEnergyPropertiesError: If the aperture has no energy properties.
    """
    energy_props = getattr(hb_aperture.properties, "energy", None)
    if energy_props is None:
        raise MissingEnergyPropertiesError(hb_aperture.display_name, "energy")
    return energy_props


def get_space_energy_properties(hb_space: "hb_space.Space") -> "RoomEnergyProperties":
    """Get energy properties from a Honeybee-PH Space's host room.

    Arguments:
    ----------
        * hb_space (space.Space): The Honeybee-PH Space.

    Returns:
    --------
        * (RoomEnergyProperties): The host room's energy properties.

    Raises:
    -------
        * MissingEnergyPropertiesError: If the space has no host or the host has no energy properties.
    """
    if not hb_space.host:
        raise MissingEnergyPropertiesError(hb_space.display_name, "host")

    energy_props = getattr(hb_space.host.properties, "energy", None)
    if energy_props is None:
        raise MissingEnergyPropertiesError(f"{hb_space.display_name}.host ({hb_space.host.display_name})", "energy")
    return energy_props


def get_room_infiltration(hb_room: "room.Room") -> "Infiltration":
    """Get infiltration from a Honeybee Room's energy properties.

    Arguments:
    ----------
        * hb_room (room.Room): The Honeybee Room.

    Returns:
    --------
        * (Infiltration): The room's infiltration object.

    Raises:
    -------
        * MissingEnergyPropertiesError: If infiltration is not defined.
    """
    energy_props = get_room_energy_properties(hb_room)
    if energy_props.infiltration is None:
        raise MissingEnergyPropertiesError(hb_room.display_name, "infiltration")
    return energy_props.infiltration


def get_room_ventilation(hb_room: "room.Room") -> "Ventilation":
    """Get ventilation from a Honeybee Room's energy properties.

    Arguments:
    ----------
        * hb_room (room.Room): The Honeybee Room.

    Returns:
    --------
        * (Ventilation): The room's ventilation object.

    Raises:
    -------
        * MissingEnergyPropertiesError: If ventilation is not defined.
    """
    energy_props = get_room_energy_properties(hb_room)
    if energy_props.ventilation is None:
        raise MissingEnergyPropertiesError(hb_room.display_name, "ventilation")
    return energy_props.ventilation


def get_room_people(hb_room: "room.Room") -> "People":
    """Get people from a Honeybee Room's energy properties.

    Arguments:
    ----------
        * hb_room (room.Room): The Honeybee Room.

    Returns:
    --------
        * (People): The room's people object.

    Raises:
    -------
        * MissingEnergyPropertiesError: If people is not defined.
    """
    energy_props = get_room_energy_properties(hb_room)
    if energy_props.people is None:
        raise MissingEnergyPropertiesError(hb_room.display_name, "people")
    return energy_props.people


def get_room_electric_equipment(hb_room: "room.Room") -> "ElectricEquipment":
    """Get electric equipment from a Honeybee Room's energy properties.

    Arguments:
    ----------
        * hb_room (room.Room): The Honeybee Room.

    Returns:
    --------
        * (ElectricEquipment): The room's electric equipment object.

    Raises:
    -------
        * MissingEnergyPropertiesError: If electric equipment is not defined.
    """
    energy_props = get_room_energy_properties(hb_room)
    if energy_props.electric_equipment is None:
        raise MissingEnergyPropertiesError(hb_room.display_name, "electric_equipment")
    return energy_props.electric_equipment


def get_ventilation_schedule(hb_room: "room.Room") -> "HBESchedule":
    """Get ventilation schedule from a Honeybee Room's energy properties.

    Arguments:
    ----------
        * hb_room (room.Room): The Honeybee Room.

    Returns:
    --------
        * (HBESchedule): The room's ventilation schedule.

    Raises:
    -------
        * MissingEnergyPropertiesError: If ventilation or schedule is not defined.
    """
    ventilation = get_room_ventilation(hb_room)
    if ventilation.schedule is None:
        raise MissingEnergyPropertiesError(hb_room.display_name, "ventilation.schedule")
    return ventilation.schedule


def get_people_schedule(hb_room: "room.Room") -> "HBESchedule":
    """Get people occupancy schedule from a Honeybee Room's energy properties.

    Arguments:
    ----------
        * hb_room (room.Room): The Honeybee Room.

    Returns:
    --------
        * (HBESchedule): The room's people occupancy schedule.

    Raises:
    -------
        * MissingEnergyPropertiesError: If people or occupancy schedule is not defined.
    """
    people = get_room_people(hb_room)
    if people.occupancy_schedule is None:
        raise MissingEnergyPropertiesError(hb_room.display_name, "people.occupancy_schedule")
    return people.occupancy_schedule


def get_lighting_schedule(hb_room: "room.Room") -> "HBESchedule":
    """Get lighting schedule from a Honeybee Room's energy properties.

    Arguments:
    ----------
        * hb_room (room.Room): The Honeybee Room.

    Returns:
    --------
        * (HBESchedule): The room's lighting schedule.

    Raises:
    -------
        * MissingEnergyPropertiesError: If lighting or schedule is not defined.
    """
    energy_props = get_room_energy_properties(hb_room)
    if energy_props.lighting is None:
        raise MissingEnergyPropertiesError(hb_room.display_name, "lighting")
    if energy_props.lighting.schedule is None:
        raise MissingEnergyPropertiesError(hb_room.display_name, "lighting.schedule")
    return energy_props.lighting.schedule
