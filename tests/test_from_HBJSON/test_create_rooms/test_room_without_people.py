"""A Model whose Rooms have Spaces but no HB People load still converts and exports (PHX#169)."""

from honeybee.model import Model

from PHX.from_HBJSON import create_project
from PHX.from_HBJSON.create_schedules import DEFAULT_OCC_PATTERN_IDENTIFIER
from PHX.to_METr_JSON import metr_builder
from PHX.to_WUFI_XML import xml_builder
from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import NON_RES_FIXTURE, load_hb_model


def _model_without_people(_room_count: int | None = None) -> Model:
    """Return the non-res fixture with its first Rooms (default: all) on a ProgramType that has no People."""
    hb_model = load_hb_model(NON_RES_FIXTURE)
    for hb_room in hb_model.rooms[:_room_count]:
        program = hb_room.properties.energy.program_type.duplicate()
        program.identifier = f"no_people_{program.identifier}"
        program.people = None
        hb_room.properties.energy.program_type = program
        hb_room.properties.energy.people = None  # -- clear any Room-level override
        assert hb_room.properties.energy.people is None
        assert hb_room.properties.ph.spaces
    return hb_model


def _convert(hb_model: Model):
    return create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True, _merge_faces=False)


def test_spaces_without_people_reference_a_registered_occupancy_pattern():
    project = _convert(_model_without_people())

    spaces = [sp for variant in project.variants for zone in variant.building.zones for sp in zone.spaces]
    assert spaces
    registered_id_nums = {pattern.id_num for pattern in project.utilization_patterns_occupancy}
    for sp in spaces:
        assert sp.occupancy.schedule.id_num in registered_id_nums
        assert sp.peak_occupancy == 0.0


def test_only_spaces_without_people_use_the_default_occupancy_pattern():
    hb_model = _model_without_people(_room_count=1)
    no_people_names = {sp.full_name for sp in hb_model.rooms[0].properties.ph.spaces}
    project = _convert(hb_model)

    spaces = [sp for variant in project.variants for zone in variant.building.zones for sp in zone.spaces]
    assert {sp.display_name for sp in spaces} > no_people_names
    registered_id_nums = {pattern.id_num for pattern in project.utilization_patterns_occupancy}
    for sp in spaces:
        assert sp.occupancy.schedule.id_num in registered_id_nums
        is_default = sp.occupancy.schedule.identifier == DEFAULT_OCC_PATTERN_IDENTIFIER
        assert is_default == (sp.display_name in no_people_names)


def test_model_without_people_writes_wufi_xml_and_metr_json():
    assert xml_builder.generate_WUFI_XML_from_object(_convert(_model_without_people()))
    assert metr_builder.generate_metr_json_dict(_convert(_model_without_people()))
