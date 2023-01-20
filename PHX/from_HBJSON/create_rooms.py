# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions to build PHX 'RoomVentilation' entities from Honeybee-PH Spaces"""

from honeybee import room
from honeybee_energy.properties.room import RoomEnergyProperties

from honeybee_ph import space
from honeybee_ph.properties.room import RoomPhProperties
from honeybee_ph.properties.space import SpacePhProperties

from honeybee_energy_ph.properties.hvac.idealair import IdealAirSystemPhProperties
from honeybee_energy_ph.properties.ruleset import ScheduleRulesetPhProperties

from honeybee_ph_utils.occupancy import hb_room_ppl_per_area
from honeybee_ph_utils.ventilation import hb_room_vent_flowrates

from PHX.model import spaces
from PHX.model.utilization_patterns import UtilizationPatternCollection_Ventilation


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
    host_room: room.Room = _space.host  # type: ignore
    host_room_prop_ph: RoomPhProperties = host_room.properties.ph  # type: ignore

    (
        flow_per_person,
        flow_per_area,
        air_changes_per_hour,
        flow_per_zone,
    ) = hb_room_vent_flowrates(host_room)
    # TODO: Unweighted or weighted? Which is right?
    ref_flr_area = _space.floor_area

    # -- Basic flow rates
    m3s_by_occupancy = ref_flr_area * hb_room_ppl_per_area(host_room) * flow_per_person
    m3s_by_area = ref_flr_area * flow_per_area

    # -- Figure out % of the HB-Room that the Space represents
    # -- For the Flow-by-Zone and Flow-by_ACH, need to calc the Room total flow
    # -- and then calc the % of that total that this one space represents.
    hb_room_total_space_fa = host_room_prop_ph.total_space_floor_area
    space_percent_of_total = ref_flr_area / hb_room_total_space_fa

    m3s_by_ach = (air_changes_per_hour * space_percent_of_total) / 3_600
    m3s_by_zone = flow_per_zone * space_percent_of_total

    return (m3s_by_occupancy + m3s_by_area + m3s_by_zone + m3s_by_ach) * 3_600


def create_room_from_space(
    _space: space.Space,
    _vent_sched_collection: UtilizationPatternCollection_Ventilation,
) -> spaces.PhxSpace:
    """Create a new RoomVentilation object with attributes based on a Honeybee-PH Space

    Arguments:
    ----------
        * _space (space.Space): The Honeybee-PH Space to use as the source.

    Returns:
    --------
        * (ventilation.RoomVentilation): The new PHX-Room with attributes based on the Honeybee Space.
    """
    # -- Type Aliases
    host_room_prop_energy: RoomEnergyProperties = _space.host.properties.energy  # type: ignore
    hbe_vent = host_room_prop_energy.ventilation
    hbe_vent_sched = hbe_vent.schedule
    hbe_vent_sched_prop_ph: ScheduleRulesetPhProperties = hbe_vent_sched.properties.ph  # type: ignore
    space_prop_ph: SpacePhProperties = _space.properties.ph  # type: ignore
    hbe_hvac = host_room_prop_energy.hvac
    hbe_hvac_prop_ph: IdealAirSystemPhProperties = hbe_hvac.properties.ph  # type: ignore

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
    if space_prop_ph._v_sup is not None:
        new_room.ventilation.load.flow_supply = space_prop_ph._v_sup * 3_600

    if space_prop_ph._v_eta is not None:
        new_room.ventilation.load.flow_extract = space_prop_ph._v_eta * 3_600

    if space_prop_ph._v_tran is not None:
        new_room.ventilation.load.flow_transfer = space_prop_ph._v_tran * 3_600

    # -- Keep the Ventilation Equipment ID-Numbers aligned
    if hbe_hvac_prop_ph.ventilation_system:
        new_room.vent_unit_id_num = hbe_hvac_prop_ph.ventilation_system.id_num

    return new_room
