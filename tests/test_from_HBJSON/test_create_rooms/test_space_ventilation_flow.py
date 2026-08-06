import pytest
from honeybee.room import Room
from honeybee_energy.load.people import People
from honeybee_energy.load.ventilation import Ventilation
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_ph.space import Space, SpaceFloor, SpaceFloorSegment, SpaceVolume
from honeybee_ph_utils.ventilation import hb_room_peak_ventilation_airflow_total
from ladybug_geometry.geometry3d import Face3D, Point3D

from PHX.from_HBJSON.create_rooms import calc_space_ventilation_flow_rate


def _space_with_floor_area(_hb_room: Room, _floor_area: float, _x_offset: float = 0.0) -> Space:
    """Add a PH Space with a rectangular floor segment to a Honeybee Room."""
    segment = SpaceFloorSegment()
    if _floor_area:
        segment.geometry = Face3D(
            (
                Point3D(_x_offset, 0, 0),
                Point3D(_x_offset + _floor_area, 0, 0),
                Point3D(_x_offset + _floor_area, 1, 0),
                Point3D(_x_offset, 1, 0),
            )
        )

    floor = SpaceFloor()
    floor.add_floor_segment(segment)

    volume = SpaceVolume()
    volume.floor = floor

    ph_space = Space(_host=_hb_room)
    ph_space.add_new_volumes(volume)
    _hb_room.properties.ph.add_new_space(ph_space)
    return ph_space


def _room_with_ventilation(
    *,
    flow_per_person: float = 0.0,
    flow_per_area: float = 0.0,
    flow_per_zone: float = 0.0,
    air_changes_per_hour: float = 0.0,
) -> Room:
    """Build a 100 m2 / 300 m3 room with explicit People and Ventilation loads."""
    hb_room = Room.from_box("ventilation_test_room", 10, 10, 3)
    hb_room.properties.energy.people = People(
        "ventilation_test_people",
        0.1,
        ScheduleRuleset.from_constant_value("ventilation_test_occupancy", 1.0),
    )
    hb_room.properties.energy.ventilation = Ventilation(
        "ventilation_test_load",
        flow_per_person=flow_per_person,
        flow_per_area=flow_per_area,
        flow_per_zone=flow_per_zone,
        air_changes_per_hour=air_changes_per_hour,
    )
    return hb_room


def test_ach_flow_is_not_divided_by_3600_twice():
    """A 300 m3 room at 0.5 ACH must yield 150 m3/hr, not 0.042."""
    hb_room = _room_with_ventilation(air_changes_per_hour=0.5)
    ph_space = _space_with_floor_area(hb_room, 100.0)

    assert calc_space_ventilation_flow_rate(ph_space) == pytest.approx(150.0)


@pytest.mark.parametrize("space_floor_areas", [(100.0,), (20.0, 30.0)])
def test_space_flows_sum_to_room_total(space_floor_areas: tuple[float, ...]):
    """Space shares preserve the HB Room total even when Spaces do not tile it."""
    hb_room = _room_with_ventilation(
        flow_per_person=0.002,
        flow_per_area=0.0003,
        flow_per_zone=0.01,
        air_changes_per_hour=0.5,
    )
    ph_spaces = [_space_with_floor_area(hb_room, area, i * 25.0) for i, area in enumerate(space_floor_areas)]

    expected_room_flow_m3h = hb_room_peak_ventilation_airflow_total(hb_room) * 3_600
    actual_space_flow_m3h = sum(calc_space_ventilation_flow_rate(ph_space) for ph_space in ph_spaces)

    assert actual_space_flow_m3h == pytest.approx(expected_room_flow_m3h)


def test_zero_total_space_floor_area_returns_zero():
    """A Room whose Spaces sum to zero floor area must not raise ZeroDivisionError."""
    hb_room = _room_with_ventilation(air_changes_per_hour=0.5)
    ph_space = _space_with_floor_area(hb_room, 0.0)

    assert calc_space_ventilation_flow_rate(ph_space) == 0.0
