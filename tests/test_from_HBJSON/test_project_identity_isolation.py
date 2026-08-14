from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from PHX.conversion import from_honeybee
from PHX.from_HBJSON import create_project, create_variant, read_HBJSON_file
from PHX.model.building import PhxZone
from PHX.model.project import PhxVariant
from PHX.to_METr_JSON.metr_builder import generate_metr_json_dict
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object

HBJSON_FIXTURE = Path(
    "tests",
    "reference_files",
    "from_grasshopper_tests",
    "hbjson",
    "Default_Model_Single_Zone.hbjson",
)
SECOND_HBJSON_FIXTURE = HBJSON_FIXTURE.with_name("Multi_Room_Complete.hbjson")


def _fresh_hb_model(path: Path = HBJSON_FIXTURE):
    source = read_HBJSON_file.read_hb_json_from_file(path)
    return read_HBJSON_file.convert_hbjson_dict_to_hb_model(source)


def _fresh_conversion(path: Path = HBJSON_FIXTURE):
    hb_model = _fresh_hb_model(path)
    return from_honeybee(hb_model)


def _legacy_conversion(path: Path = HBJSON_FIXTURE):
    return create_project.convert_hb_model_to_PhxProject(_fresh_hb_model(path))


def _identity_projection(phx_project) -> dict:
    variants = phx_project.variants
    components = [component for variant in variants for component in variant.building.all_components]
    polygons = [polygon for variant in variants for polygon in variant.building.polygons]
    vertices = [vertex for variant in variants for vertex in variant.graphics3D.vertices]
    devices = [
        device for variant in variants for collection in variant.mech_collections for device in collection.devices
    ]
    materials = {
        material.id_num
        for assembly in phx_project.assembly_types.values()
        for layer in assembly.layers
        for material in layer.materials
    }
    return {
        "variants": [item.id_num for item in variants],
        "zones": [[zone.id_num for zone in variant.zones] for variant in variants],
        "components": [item.id_num for item in components],
        "polygons": [item.id_num for item in polygons],
        "vertices": [item.id_num for item in vertices],
        "materials": sorted(materials),
        "assemblies": [item.id_num for item in phx_project.assembly_types.values()],
        "windows": [item.id_num for item in phx_project.window_types.values()],
        "shades": [item.id_num for item in phx_project.shade_types.values()],
        "vent_patterns": [item.id_num for item in phx_project.utilization_patterns_ventilation],
        "occ_patterns": [item.id_num for item in phx_project.utilization_patterns_occupancy],
        "lighting_patterns": [item.id_num for item in phx_project.utilization_patterns_lighting],
        "ph_building_data": [variant.phius_cert.ph_building_data.id_num for variant in variants],
        "mechanical_devices": [(type(item).__name__, item.id_num) for item in devices],
    }


def _conversion_result(path: Path) -> tuple[dict, str, dict]:
    phx_project = _fresh_conversion(path)
    return (
        _identity_projection(phx_project),
        generate_WUFI_XML_from_object(phx_project),
        generate_metr_json_dict(phx_project),
    )


def test_sequential_public_conversions_are_identity_isolated():
    first = _conversion_result(HBJSON_FIXTURE)
    second = _conversion_result(HBJSON_FIXTURE)

    assert second == first


def test_legacy_core_converter_matches_public_facade():
    assert _identity_projection(_legacy_conversion()) == _identity_projection(_fresh_conversion())


def test_parallel_conversions_match_sequential_project_baselines():
    paths = [HBJSON_FIXTURE, SECOND_HBJSON_FIXTURE]
    baselines = {path: _conversion_result(path) for path in paths}
    task_paths = paths * 4

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(_conversion_result, task_paths))

    assert results == [baselines[path] for path in task_paths]


def test_failed_conversion_does_not_leak_into_next_conversion(monkeypatch):
    baseline = _conversion_result(HBJSON_FIXTURE)
    real_from_hb_room = create_variant.from_hb_room

    def fail_after_allocating(*args, **kwargs):
        PhxVariant()
        raise RuntimeError("deliberate identity-scope failure")

    monkeypatch.setattr(create_variant, "from_hb_room", fail_after_allocating)
    with pytest.raises(RuntimeError, match="deliberate identity-scope failure"):
        _fresh_conversion()
    monkeypatch.setattr(create_variant, "from_hb_room", real_from_hb_room)

    assert _conversion_result(HBJSON_FIXTURE) == baseline


def test_project_mutation_scope_continues_owning_namespace():
    phx_project = _fresh_conversion()
    existing_zone_ids = {zone.id_num for variant in phx_project.variants for zone in variant.zones}
    owner = phx_project.variants[0].id_num

    with phx_project.identity_scope(owner=owner):
        first_new_zone = PhxZone()
        second_new_zone = PhxZone()

    assert first_new_zone.id_num not in existing_zone_ids
    assert second_new_zone.id_num == first_new_zone.id_num + 1
