# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions to build PHX 'RoomVentilation' entities from Honeybee-PH Spaces"""

from typing import Optional

from honeybee import room
from honeybee_energy.properties.room import RoomEnergyProperties
from honeybee_ph import space
from honeybee_ph.properties.room import get_ph_prop_from_room
from honeybee_ph.properties.space import get_ph_prop_from_space
from honeybee_ph_utils.occupancy import hb_room_ppl_per_area
from honeybee_ph_utils.ventilation import hb_room_vent_flowrates
from honeybee_phhvac.properties.room import get_ph_hvac_from_space

from PHX.model import spaces
from PHX.model.utilization_patterns import (
    UtilizationPatternCollection_Lighting,
    UtilizationPatternCollection_Occupancy,
    UtilizationPatternCollection_Ventilation,
)


def calc_space_ventilation_flow_rate(_space: space.Space) -> float:
    """Calculate and return the total peak ventilation flow rate for a Space.

    This function will determine the peak flow by-person, by-area, by-zone, and by-ach
    and return the sum of all four flow-rate types.

    Arguments:
    ----------
        * _space (space.Space): The Honeybee-PH Space to use as the source.

    Returns:
    --------
        * (float)
    """
    # Type Aliases
    host: Optional[room.Room] = _space.host
    if not host:
        raise ValueError(f"The Honeybee-PH Space {_space.display_name} is missing a host-HB-Room.")

    host_room_prop_ph = get_ph_prop_from_room(host)
    (
        flow_per_person,
        flow_per_area,
        air_changes_per_hour,
        flow_per_zone,
    ) = hb_room_vent_flowrates(host)
    # TODO: Unweighted or weighted? Which is right?
    ref_flr_area = _space.floor_area

    # -- Basic flow rates
    m3s_by_occupancy = ref_flr_area * hb_room_ppl_per_area(host) * flow_per_person
    m3s_by_area = ref_flr_area * flow_per_area

    # -- Figure out % of the HB-Room that the Space represents
    # -- For the Flow-by-Zone and Flow-by_ACH, need to calc the Room total flow
    # -- and then calc the % of that total that this one space represents.
    hb_room_total_space_fa = host_room_prop_ph.total_space_floor_area
    space_percent_of_total = ref_flr_area / hb_room_total_space_fa

    m3s_by_ach = (air_changes_per_hour * space_percent_of_total) / 3_600
    m3s_by_zone = flow_per_zone * space_percent_of_total

    return (m3s_by_occupancy + m3s_by_area + m3s_by_zone + m3s_by_ach) * 3_600


def _get_energy_properties_from_space(_space: space.Space) -> RoomEnergyProperties:
    """Return the "energy" Properties of a Honeybee-PH Space's host Room."""
    if not _space.host:
        raise ValueError(f"The Honeybee-PH Space {_space.display_name} is missing a host-HB-Room.")
    return getattr(_space.host.properties, "energy")


def create_room_from_space(
    _space: space.Space,
    _vent_sched_collection: UtilizationPatternCollection_Ventilation,
    _occ_sched_collection: UtilizationPatternCollection_Occupancy,
    _lighting_sched_collection: UtilizationPatternCollection_Lighting,
) -> spaces.PhxSpace:
    """Create a new RoomVentilation object with attributes based on a Honeybee-PH Space

    Arguments:
    ----------
        * _space (space.Space): The Honeybee-PH Space to use as the source.
        * _vent_sched_collection (UtilizationPatternCollection_Ventilation): A collection of
            ventilation schedules to use for the new PHX-Room.
        * _occ_sched_collection (UtilizationPatternCollection_Occupancy): A collection of
            occupancy schedules to use for the new PHX-Room.

    Returns:
    --------
        * (ventilation.RoomVentilation): The new PHX-Room with attributes based on the Honeybee Space.
    """
    # -- Type Aliases
    host_room_prop_energy = _get_energy_properties_from_space(_space)
    hbe_vent = host_room_prop_energy.ventilation
    hbe_vent_sched = hbe_vent.schedule
    hbe_occ = host_room_prop_energy.people
    hbe_lighting = host_room_prop_energy.lighting
    space_ph_hvac = get_ph_hvac_from_space(_space)
    space_prop_ph = get_ph_prop_from_space(_space)

    # -- Build the new PHX Space
    new_room = spaces.PhxSpace()

    new_room.display_name = _space.full_name
    new_room.wufi_type = _space.wufi_type
    new_room.quantity = _space.quantity
    new_room.floor_area = _space.floor_area
    new_room.weighted_floor_area = _space.weighted_floor_area
    new_room.clear_height = _space.avg_clear_height
    new_room.net_volume = _space.net_volume

    # -- Set the Room's Ventilation attributes
    new_room.ventilation.schedule = _vent_sched_collection[hbe_vent_sched.identifier]
    space_peak_flow_rate = calc_space_ventilation_flow_rate(_space)
    new_room.ventilation.load.flow_supply = space_peak_flow_rate
    new_room.ventilation.load.flow_extract = space_peak_flow_rate

    # -- TODO: FIX THIS TO A BETTER TECHNIQUE SOMEDAY, OVERRIDE WITH LOCAL INFO, IF ANY
    if space_prop_ph and space_prop_ph._v_sup is not None:
        new_room.ventilation.load.flow_supply = space_prop_ph._v_sup * 3_600

    if space_prop_ph and space_prop_ph._v_eta is not None:
        new_room.ventilation.load.flow_extract = space_prop_ph._v_eta * 3_600

    if space_prop_ph and space_prop_ph._v_tran is not None:
        new_room.ventilation.load.flow_transfer = space_prop_ph._v_tran * 3_600

    # -- Keep the Ventilation Equipment ID-Numbers aligned
    if space_ph_hvac and space_ph_hvac.ventilation_system:
        new_room.vent_unit_id_num = space_ph_hvac.ventilation_system.id_num
        new_room.vent_unit_display_name = space_ph_hvac.ventilation_system.display_name

    # -- Keep the new room's Occupancy reference aligned with the HB-Room's
    if hbe_occ:
        occ_sched_id = hbe_occ.occupancy_schedule.identifier
        new_room.occupancy.schedule = _occ_sched_collection[occ_sched_id]

    # -- Keep the new room's Lighting reference aligned with the HB-Room's
    if hbe_lighting:
        lighting_sched_id = hbe_lighting.schedule.identifier
        new_room.lighting.schedule = _lighting_sched_collection[lighting_sched_id]
        new_room.lighting.load.installed_w_per_m2 = hbe_lighting.watts_per_area

    return new_room
