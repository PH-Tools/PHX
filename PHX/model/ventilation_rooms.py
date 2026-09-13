# -*- Python Version: 3.10 -*-

"""Read-only Ventilation Room projections for WUFI-Passive and METr exports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from PHX.model.building import PhxZone
from PHX.model.spaces import PhxSpace, area_weighted_clear_height, spaces_are_not_addable


@dataclass(frozen=True)
class VentilationRoom:
    """A read-only Ventilation Room row derived from one or more Spaces.

    Attributes:
        display_name (str): Name written for the Ventilation Room.
        wufi_type (int): WUFI-Passive room-type code.
        quantity (int): Number of identical Ventilation Rooms represented by the row.
        weighted_floor_area (float): iCFA/TFA-weighted floor area in m2.
        clear_height (float): Area-weighted clear height in m.
        flow_supply (float): Supply airflow rate in m3/h.
        flow_extract (float): Extract airflow rate in m3/h.
        ventilation_pattern_id_num (int): ID Number of the Ventilation Utilization Pattern.
        ventilator_id_num (int | None): ID Number of the assigned Ventilator, or None when unassigned.
    """

    display_name: str
    wufi_type: int
    quantity: int
    weighted_floor_area: float
    clear_height: float
    flow_supply: float
    flow_extract: float
    ventilation_pattern_id_num: int
    ventilator_id_num: int | None


@dataclass(frozen=True)
class _VentilationRoomMergeState:
    """Values needed to reproduce the pairwise ``PhxSpace.__add__`` fold."""

    display_name: str
    vent_unit_display_name: str
    wufi_type: int
    quantity: int
    floor_area: float
    weighted_floor_area: float
    clear_height: float
    flow_supply: float
    flow_extract: float
    ventilation_pattern_id_num: int
    vent_unit_id_num: int | None


def _merge_state_from_space(_space: PhxSpace) -> _VentilationRoomMergeState:
    return _VentilationRoomMergeState(
        display_name=_space.display_name,
        vent_unit_display_name=_space.vent_unit_display_name,
        wufi_type=_space.wufi_type,
        quantity=_space.quantity,
        floor_area=_space.floor_area,
        weighted_floor_area=_space.weighted_floor_area,
        clear_height=_space.clear_height,
        flow_supply=_space.ventilation.load.flow_supply,
        flow_extract=_space.ventilation.load.flow_extract,
        ventilation_pattern_id_num=_space.ventilation.schedule.id_num,
        vent_unit_id_num=_space.vent_unit_id_num,
    )


def _merge_space_into_state(_state: _VentilationRoomMergeState, _space: PhxSpace) -> _VentilationRoomMergeState:
    # -- The merge state carries the attribute names these Space helpers read, so it stands in for a PhxSpace.
    state_as_space = cast(PhxSpace, _state)
    if spaces_are_not_addable(state_as_space, _space):
        raise ValueError(f"Space {_state.display_name} cannot be added to space {_space.display_name}.")

    return _VentilationRoomMergeState(
        display_name=_state.vent_unit_display_name,
        vent_unit_display_name=_state.vent_unit_display_name,
        wufi_type=_state.wufi_type,
        quantity=1,
        floor_area=_state.floor_area + _space.floor_area,
        weighted_floor_area=_state.weighted_floor_area + _space.weighted_floor_area,
        clear_height=area_weighted_clear_height(state_as_space, _space),
        flow_supply=_state.flow_supply + _space.ventilation.load.flow_supply,
        flow_extract=_state.flow_extract + _space.ventilation.load.flow_extract,
        ventilation_pattern_id_num=_state.ventilation_pattern_id_num,
        vent_unit_id_num=_state.vent_unit_id_num,
    )


def _room_from_space(_space: PhxSpace, _display_name: str) -> VentilationRoom:
    return VentilationRoom(
        display_name=_display_name,
        wufi_type=_space.wufi_type,
        quantity=_space.quantity,
        weighted_floor_area=_space.weighted_floor_area,
        clear_height=_space.clear_height,
        flow_supply=_space.ventilation.load.flow_supply,
        flow_extract=_space.ventilation.load.flow_extract,
        ventilation_pattern_id_num=_space.ventilation.schedule.id_num,
        ventilator_id_num=_space.vent_unit_id_num,
    )


def _room_from_merge_state(_state: _VentilationRoomMergeState) -> VentilationRoom:
    return VentilationRoom(
        display_name=_state.display_name,
        wufi_type=_state.wufi_type,
        quantity=_state.quantity,
        weighted_floor_area=_state.weighted_floor_area,
        clear_height=_state.clear_height,
        flow_supply=_state.flow_supply,
        flow_extract=_state.flow_extract,
        ventilation_pattern_id_num=_state.ventilation_pattern_id_num,
        ventilator_id_num=_state.vent_unit_id_num,
    )


def ventilation_rooms(_zone: PhxZone) -> list[VentilationRoom]:
    """Return read-only Ventilation Rooms derived from a Zone's ventilated Spaces.

    Arguments:
    ----------
        * _zone (PhxZone): The source Zone. When ``merge_spaces_by_erv`` is true,
            its Spaces are merged by Ventilation Assignment.

    Returns:
    --------
        * list[VentilationRoom]: One record per ventilated Space, or one per
            Ventilation Assignment when merging.
    """
    if not _zone.merge_spaces_by_erv:
        return [_room_from_space(space, space.display_name) for space in _zone.ventilated_spaces]

    rooms: list[VentilationRoom] = []
    for space_group in _zone.ventilated_spaces_grouped_by_erv:
        if len(space_group) == 1:
            space = space_group[0]
            rooms.append(_room_from_space(space, space.vent_unit_display_name))
            continue

        state = _merge_state_from_space(space_group[0])
        for space in space_group[1:]:
            state = _merge_space_into_state(state, space)
        rooms.append(_room_from_merge_state(state))

    return sorted(rooms, key=lambda room: room.display_name)
