"""A Room whose Program has no HB Ventilation load still converts (e.g. extract-only restrooms)."""

import pytest
from honeybee.model import Model

from PHX.from_HBJSON import create_project
from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import NON_RES_FIXTURE, load_hb_model


def _model_with_one_room_without_ventilation() -> Model:
    """Return the non-res fixture with its first Room on a ProgramType that has no Ventilation."""
    hb_model = load_hb_model(NON_RES_FIXTURE)
    hb_room = hb_model.rooms[0]
    program = hb_room.properties.energy.program_type.duplicate()
    program.identifier = "no_ventilation_program"
    program.ventilation = None
    hb_room.properties.energy.program_type = program
    hb_room.properties.energy.ventilation = None  # -- clear any Room-level override
    assert hb_room.properties.energy.ventilation is None
    return hb_model


def test_room_without_ventilation_gets_zero_flow_and_a_registered_pattern():
    hb_model = _model_with_one_room_without_ventilation()
    space_names = {sp.full_name for sp in hb_model.rooms[0].properties.ph.spaces}

    project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True, _merge_faces=False)

    spaces = [
        sp
        for variant in project.variants
        for zone in variant.building.zones
        for sp in zone.spaces
        if sp.display_name in space_names
    ]
    assert spaces
    registered_id_nums = {pattern.id_num for pattern in project.utilization_patterns_ventilation}
    for sp in spaces:
        assert sp.ventilation.load.flow_supply == 0.0
        assert sp.ventilation.load.flow_extract == 0.0
        assert sp.ventilation.schedule.id_num in registered_id_nums


def test_space_extract_override_applies_on_room_without_ventilation():
    hb_model = _model_with_one_room_without_ventilation()
    hb_space = hb_model.rooms[0].properties.ph.spaces[0]
    hb_space.properties.ph._v_eta = 0.1  # m3/s

    project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True, _merge_faces=False)

    space = next(
        sp
        for variant in project.variants
        for zone in variant.building.zones
        for sp in zone.spaces
        if sp.display_name == hb_space.full_name
    )
    assert space.ventilation.load.flow_extract == pytest.approx(360.0)
    assert space.ventilation.load.flow_supply == 0.0
