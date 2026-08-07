"""Regression tests for HB-style occupancy and lighting schedule fallbacks."""

from statistics import mean

import pytest
from honeybee.room import Room
from honeybee_energy.lib.scheduletypelimits import schedule_type_limit_by_identifier
from honeybee_energy.schedule.ruleset import ScheduleRuleset

from PHX.from_HBJSON import create_schedules
from PHX.from_HBJSON._type_utils import get_lighting_schedule, get_people_schedule
from PHX.model.schedules.occupancy import PhxScheduleOccupancy
from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import (
    GENERIC_OFFICE_OCCUPANCY_MEAN,
    NON_RES_FIXTURE,
    OCCUPANCY_SCENARIO_DIR,
    load_hb_model,
)


def _non_res_room() -> Room:
    """Return a Room whose stock HB schedules have no PH operating periods."""
    return load_hb_model(NON_RES_FIXTURE).rooms[0]


def _ph_style_hallway_room() -> Room:
    """Return the corpus Room carrying explicit PH occupancy and lighting periods."""
    model = load_hb_model(OCCUPANCY_SCENARIO_DIR / "06_res_with_hallway.hbjson")
    return next(room for room in model.rooms if room.display_name == "hallway")


@pytest.mark.parametrize(
    ("builder", "schedule_getter", "expected_factor"),
    (
        (create_schedules.build_occupancy_schedule_from_hb_room, get_people_schedule, GENERIC_OFFICE_OCCUPANCY_MEAN),
        (create_schedules.build_lighting_schedule_from_hb_room, get_lighting_schedule, 0.2917113364931507),
    ),
)
def test_no_ph_periods_uses_annual_mean(builder, schedule_getter, expected_factor):
    """A stock HB schedule becomes 0/24/365 with its annual mean as the factor."""
    hb_room = _non_res_room()
    hb_schedule = schedule_getter(hb_room)

    phx_schedule = builder(hb_room)

    assert phx_schedule is not None
    assert (phx_schedule.start_hour, phx_schedule.end_hour) == (0, 24)
    assert phx_schedule.annual_utilization_days == 365
    assert phx_schedule.relative_utilization_factor == pytest.approx(mean(hb_schedule.values()))
    assert phx_schedule.relative_utilization_factor == pytest.approx(expected_factor)


@pytest.mark.parametrize(
    ("builder", "schedule_getter", "expected"),
    (
        (
            create_schedules.build_occupancy_schedule_from_hb_room,
            get_people_schedule,
            (7, 18, 250.00020547945203, 0.09166666666666667),
        ),
        (
            create_schedules.build_lighting_schedule_from_hb_room,
            get_lighting_schedule,
            (6.5, 17.5, 250.00020547945203, 0.4583333333333333),
        ),
    ),
)
def test_ph_style_schedule_output_is_unchanged(builder, schedule_getter, expected):
    """A schedule with PH operating periods retains the pre-fallback output."""
    hb_room = _ph_style_hallway_room()
    hb_schedule = schedule_getter(hb_room)

    phx_schedule = builder(hb_room)

    assert phx_schedule is not None
    assert phx_schedule.identifier == hb_schedule.identifier
    assert phx_schedule.display_name == hb_schedule.display_name
    assert (
        phx_schedule.start_hour,
        phx_schedule.end_hour,
        phx_schedule.annual_utilization_days,
        phx_schedule.relative_utilization_factor,
    ) == pytest.approx(expected)


def test_annual_utilization_factor_is_preserved_across_shapes():
    """Equivalent explicit-window and 0/24/365 patterns have the same annual factor."""
    ph_style = PhxScheduleOccupancy(
        start_hour=7,
        end_hour=18,
        annual_utilization_days=250,
        relative_utilization_factor=1.0,
    )
    expected_factor = (11 * 250) / 8760

    hb_room = _non_res_room()
    people = hb_room.properties.energy.people
    people.unlock()
    people.occupancy_schedule = ScheduleRuleset.from_constant_value(
        "Office Workspace Open Equivalent",
        expected_factor,
        schedule_type_limit_by_identifier("Fractional"),
    )
    people.lock()

    hb_style = create_schedules.build_occupancy_schedule_from_hb_room(hb_room)

    assert hb_style is not None
    assert ph_style.annual_utilization_factor == pytest.approx(expected_factor)
    assert hb_style.annual_utilization_factor == pytest.approx(expected_factor)


@pytest.mark.parametrize(
    ("builder", "schedule_getter"),
    (
        (create_schedules.build_occupancy_schedule_from_hb_room, get_people_schedule),
        (create_schedules.build_lighting_schedule_from_hb_room, get_lighting_schedule),
    ),
)
def test_schedule_id_alignment_is_identical_across_branches(builder, schedule_getter):
    """HB- and PH-style schedules preserve names and align source/PHX id numbers."""
    results = []
    for hb_room in (_non_res_room(), _ph_style_hallway_room()):
        hb_schedule = schedule_getter(hb_room)
        phx_schedule = builder(hb_room)

        assert phx_schedule is not None
        assert phx_schedule.identifier == hb_schedule.identifier
        assert phx_schedule.display_name == hb_schedule.display_name
        assert phx_schedule.id_num == hb_schedule.properties.ph.id_num
        results.append(phx_schedule)

    assert results[0].id_num != results[1].id_num


def test_ph_style_predicates_return_false_when_loads_are_missing():
    """Missing People and Lighting loads are not classified as PH-style schedules."""
    hb_room = Room.from_box("No_Loads", 1, 1, 1)

    assert create_schedules._room_has_ph_style_occupancy(hb_room) is False
    assert create_schedules._room_has_ph_style_lighting(hb_room) is False
