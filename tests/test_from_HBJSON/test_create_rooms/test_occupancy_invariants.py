"""Implementation-independent occupancy-channel invariants."""

import pytest
from honeybee.model import Model

from PHX.from_HBJSON import cleanup, create_project
from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import (
    NON_RES_FIXTURE,
    OCCUPANCY_SCENARIO_DIR,
    RoomSpec,
    build_rooms,
    load_hb_model,
)


def test_gate_must_read_pre_merge_state():
    """The merged Room is residential; each Space host retains pre-merge state."""
    rooms = build_rooms(
        [
            RoomSpec("office_with_explicit_people", 100, 3, None),
            RoomSpec("office_with_program_people", 100, 0, None),
        ],
        avg_occ_rate=0.5,
        hb_program="2019::SmallOffice::OpenOffice",
        apply_set_occupancy=False,
    )
    merged = cleanup.merge_rooms(rooms, 0.01, 1.0, False)
    merged_people = merged.properties.energy.people.properties.ph

    assert merged_people.is_residential is True
    assert merged_people.number_people == pytest.approx(3.0)
    assert [
        space.host.properties.energy.people.properties.ph.number_people for space in merged.properties.ph.spaces
    ] == [
        3,
        0,
    ]
    assert [
        space.host.properties.energy.people.properties.ph.number_dwelling_units for space in merged.properties.ph.spaces
    ] == [
        0,
        0,
    ]

    project = create_project.convert_hb_model_to_PhxProject(Model("pre_merge_gate", rooms))
    assert (
        sum(
            space.peak_occupancy
            for variant in project.variants
            for zone in variant.building.zones
            for space in zone.spaces
        )
        > 0
    )


def test_untagged_rooms_are_each_their_own_group():
    """Serialized untagged Rooms share a default ID but must remain separate groups."""
    rooms = list(load_hb_model(NON_RES_FIXTURE).rooms[:2])
    rooms[0].properties.energy.people = rooms[0].properties.energy.people.duplicate()
    rooms[0].properties.energy.people.properties.ph.number_people = 3

    assert all(room.properties.energy.people.properties.ph.number_dwelling_units == 0 for room in rooms)
    assert len({room.properties.energy.people.properties.ph.dwellings.identifier for room in rooms}) == 1
    assert len({room.identifier for room in rooms}) == 2
    assert rooms[1].properties.energy.people.people_per_area > 0

    project = create_project.convert_hb_model_to_PhxProject(Model("untagged_groups", rooms))
    spaces = [space for variant in project.variants for zone in variant.building.zones for space in zone.spaces]
    assert spaces[0].peak_occupancy == 0
    assert spaces[1].peak_occupancy > 0


@pytest.mark.parametrize(
    "filename",
    (
        "01_no_dwelling_no_occupancy.hbjson",
        "02_single_dwelling_no_occupancy.hbjson",
        "03_single_dwelling_set_occupancy.hbjson",
        "04_no_dwelling_set_occupancy.hbjson",
        "05_multiple_dweling_set_occupancy.hbjson",
        "06_res_with_hallway.hbjson",
    ),
)
def test_occupancy_channels_are_mutually_exclusive(filename: str):
    """A zone-level occupant quantity and per-Space occupancy cannot coexist."""
    hb_model = load_hb_model(OCCUPANCY_SCENARIO_DIR / filename)
    project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True, _merge_faces=False)

    for variant in project.variants:
        for zone in variant.building.zones:
            if zone.res_occupant_quantity > 0:
                assert all(space.peak_occupancy == 0 for space in zone.spaces)
