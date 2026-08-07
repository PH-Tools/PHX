"""Anchor synthetic occupancy fixtures against real Grasshopper component output."""

from statistics import mean

import pytest

from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import (
    OCCUPANCY_CORPUS_CASES,
    OCCUPANCY_SCENARIO_DIR,
    build_rooms,
    load_hb_model,
    room_specs_from_rooms,
)


def _load_rooms(_filename: str):
    return list(load_hb_model(OCCUPANCY_SCENARIO_DIR / _filename).rooms)


@pytest.mark.parametrize(("filename", "apply_set_occupancy"), OCCUPANCY_CORPUS_CASES)
def test_fixture_builder_matches_real_component_output(filename: str, apply_set_occupancy: bool):
    """The synthetic builder reproduces all six committed GH exports' People state."""
    actual_rooms = _load_rooms(filename)
    specs = room_specs_from_rooms(actual_rooms)
    avg_occ_rate = mean(actual_rooms[0].properties.energy.people.occupancy_schedule.values())
    rebuilt_rooms = build_rooms(
        specs,
        avg_occ_rate=avg_occ_rate,
        people_per_area=actual_rooms[0].properties.energy.people.people_per_area,
        apply_set_occupancy=apply_set_occupancy,
    )

    assert [room.properties.energy.people.properties.ph.number_people for room in rebuilt_rooms] == [
        room.properties.energy.people.properties.ph.number_people for room in actual_rooms
    ]
    assert [room.properties.energy.people.people_per_area for room in rebuilt_rooms] == pytest.approx(
        [room.properties.energy.people.people_per_area for room in actual_rooms]
    )


def test_group_uniform_density_invariant():
    """Case 03: one dwelling has one group-uniform density despite per-room people."""
    rooms = _load_rooms("03_single_dwelling_set_occupancy.hbjson")
    avg_occ_rate = mean(rooms[0].properties.energy.people.occupancy_schedule.values())
    expected_density = 7 / avg_occ_rate / 400

    assert [room.properties.energy.people.properties.ph.number_people for room in rooms] == [0, 1, 2, 4]
    assert [room.properties.energy.people.people_per_area for room in rooms] == pytest.approx([expected_density] * 4)


def test_untagged_rooms_normalize_per_room():
    """Case 04: without a dwelling tag, Set Occupancy normalizes each Room."""
    rooms = _load_rooms("04_no_dwelling_set_occupancy.hbjson")
    avg_occ_rate = mean(rooms[0].properties.energy.people.occupancy_schedule.values())

    assert [room.properties.energy.people.people_per_area for room in rooms] == pytest.approx(
        [number_people / avg_occ_rate / 100 for number_people in (0, 1, 2, 4)]
    )


def test_separate_dwellings_normalize_independently():
    """Case 05: two dwellings on equal geometry retain different group densities."""
    rooms = _load_rooms("05_multiple_dweling_set_occupancy.hbjson")
    avg_occ_rate = mean(rooms[0].properties.energy.people.occupancy_schedule.values())
    densities_by_dwelling: dict[str, set[float]] = {}
    for room in rooms:
        people = room.properties.energy.people
        dwelling_id = str(people.properties.ph.dwellings.identifier)
        densities_by_dwelling.setdefault(dwelling_id, set()).add(people.people_per_area)

    assert len(densities_by_dwelling) == 2
    assert sorted(next(iter(values)) for values in densities_by_dwelling.values()) == pytest.approx(
        sorted((1 / avg_occ_rate / 200, 6 / avg_occ_rate / 200))
    )
