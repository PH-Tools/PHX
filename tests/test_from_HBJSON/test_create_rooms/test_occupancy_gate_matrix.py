"""Per-Room regression matrix for the two mutually exclusive occupancy channels."""

from dataclasses import dataclass
from statistics import mean
from typing import Callable

import pytest
from honeybee.model import Model
from honeybee.room import Room

from PHX.from_HBJSON import create_project
from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import (
    GENERIC_OFFICE_PEOPLE_PER_M2,
    OCCUPANCY_CORPUS_CASES,
    OCCUPANCY_SCENARIO_DIR,
    RoomSpec,
    build_rooms,
    load_hb_model,
    room_specs_from_rooms,
)


@dataclass(frozen=True)
class OccupancyScenario:
    """Synthetic occupancy-gate case and its expected per-Room result."""

    name: str
    specs: list[RoomSpec]
    apply_set_occupancy: bool
    expected_peak_occupancies: list[float]
    prepare: Callable[[list[Room]], None] | None = None


def _remove_first_room_spaces(rooms: list[Room]) -> None:
    """Make the explicit-occupancy Room invisible to Space-derived indexes."""
    rooms[0].properties.ph._spaces = []


def _shrink_only_space(rooms: list[Room]) -> None:
    """Make the Space cover 25% of its Room floor to exercise Option B."""
    segment = rooms[0].properties.ph.spaces[0].volumes[0].floor.floor_segments[0]
    segment.geometry = segment.geometry.scale(0.5)


SYNTHETIC_SCENARIOS = (
    OccupancyScenario(
        "untagged_program_load",
        [RoomSpec("room_a", 100, 0, None)],
        False,
        [100 * GENERIC_OFFICE_PEOPLE_PER_M2],
    ),
    OccupancyScenario(
        "tagged_dwelling_without_explicit_occupancy",
        [RoomSpec("room_a", 100, 0, "A")],
        False,
        [100 * GENERIC_OFFICE_PEOPLE_PER_M2],
    ),
    OccupancyScenario(
        "one_dwelling_with_explicit_occupancy_on_subset",
        [RoomSpec("room_a", 100, 0, "A"), RoomSpec("room_b", 100, 2, "A")],
        True,
        [0.0, 0.0],
    ),
    OccupancyScenario(
        "untagged_rooms_after_set_occupancy",
        [RoomSpec("room_a", 100, 0, None), RoomSpec("room_b", 100, 2, None)],
        True,
        [0.0, 0.0],
    ),
    OccupancyScenario(
        "separate_dwellings_are_gated_independently",
        [
            RoomSpec("room_a", 100, 1, "A"),
            RoomSpec("room_b", 100, 0, "A"),
            RoomSpec("room_c", 100, 0, "B"),
        ],
        False,
        [0.0, 0.0, 100 * GENERIC_OFFICE_PEOPLE_PER_M2],
    ),
    OccupancyScenario(
        "untagged_rooms_are_gated_independently",
        [RoomSpec("room_a", 100, 1, None), RoomSpec("room_b", 100, 0, None)],
        False,
        [0.0, 100 * GENERIC_OFFICE_PEOPLE_PER_M2],
    ),
    OccupancyScenario(
        "explicit_room_without_a_space_still_suppresses_its_dwelling",
        [RoomSpec("room_a", 100, 2, "A"), RoomSpec("room_b", 100, 0, "A")],
        False,
        [0.0],
        _remove_first_room_spaces,
    ),
    OccupancyScenario(
        "non_tiling_space_preserves_the_room_total",
        [RoomSpec("room_a", 100, 0, None)],
        False,
        [100 * GENERIC_OFFICE_PEOPLE_PER_M2],
        _shrink_only_space,
    ),
)


def _convert_rooms(rooms: list[Room]):
    project = create_project.convert_hb_model_to_PhxProject(
        Model("occupancy_gate", rooms),
        _group_components=True,
        _merge_faces=False,
    )
    return [space for variant in project.variants for zone in variant.building.zones for space in zone.spaces]


@pytest.mark.parametrize("scenario", SYNTHETIC_SCENARIOS, ids=lambda scenario: scenario.name)
def test_synthetic_occupancy_gate_matrix(scenario: OccupancyScenario):
    """The group gate produces the expected value on every synthetic Room."""
    rooms = build_rooms(
        scenario.specs,
        avg_occ_rate=0.5,
        people_per_area=GENERIC_OFFICE_PEOPLE_PER_M2,
        apply_set_occupancy=scenario.apply_set_occupancy,
    )
    if scenario.prepare:
        scenario.prepare(rooms)

    spaces = _convert_rooms(rooms)

    assert [space.peak_occupancy for space in spaces] == pytest.approx(scenario.expected_peak_occupancies)


REAL_EXPECTED = {
    "01_no_dwelling_no_occupancy.hbjson": [5.65] * 4,
    "02_single_dwelling_no_occupancy.hbjson": [5.65] * 4,
    "03_single_dwelling_set_occupancy.hbjson": [0.0] * 4,
    "04_no_dwelling_set_occupancy.hbjson": [0.0] * 4,
    "05_multiple_dweling_set_occupancy.hbjson": [0.0] * 4,
    "06_res_with_hallway.hbjson": [0.0] * 5,
}
REAL_CASES = tuple((filename, apply, REAL_EXPECTED[filename]) for filename, apply in OCCUPANCY_CORPUS_CASES)


@pytest.mark.parametrize(("filename", "apply_set_occupancy", "expected"), REAL_CASES)
def test_real_grasshopper_scenario_matrix(filename: str, apply_set_occupancy: bool, expected: list[float]):
    """Real GH People/dwelling state yields the planned result on every reconstructed Space."""
    actual_rooms = list(load_hb_model(OCCUPANCY_SCENARIO_DIR / filename).rooms)
    specs = room_specs_from_rooms(actual_rooms)
    rooms = build_rooms(
        specs,
        avg_occ_rate=mean(actual_rooms[0].properties.energy.people.occupancy_schedule.values()),
        people_per_area=actual_rooms[0].properties.energy.people.people_per_area,
        apply_set_occupancy=apply_set_occupancy,
    )

    spaces = _convert_rooms(rooms)

    assert [space.peak_occupancy for space in spaces] == pytest.approx(expected, abs=0.001)
