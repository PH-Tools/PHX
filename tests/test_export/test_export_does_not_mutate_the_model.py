# -*- Python Version: 3.10 -*-

"""Serializing a PhxProject must not change it.

The ERV space-merge runs inside the WUFI and METr writers rather than during
conversion, so anything it mutates leaks back into the caller's model. That makes
a second export of the same project produce a different file from the first, and
it contaminates any other target written from the same project afterwards -- the
PHPP writer reads 'space.ventilation.load' off the *unmerged* source Spaces.
"""

from pathlib import Path

import pytest

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.model.project import PhxProject
from PHX.to_METr_JSON import metr_builder
from PHX.to_WUFI_XML import xml_builder

HBJSON_FIXTURE = Path("tests", "reference_files", "from_grasshopper_tests", "hbjson", "Multi_Room_Complete.hbjson")


@pytest.fixture
def merged_by_erv_project() -> PhxProject:
    """A project with '_merge_spaces_by_erv' on - the setting the GH component sends."""
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(read_HBJSON_file.read_hb_json_from_file(HBJSON_FIXTURE))
    return create_project.convert_hb_model_to_PhxProject(
        hb_model, _group_components=True, _merge_faces=True, _merge_spaces_by_erv=True
    )


def _space_airflows(_phx_project: PhxProject) -> list[tuple[float, float, float]]:
    return [
        (space.ventilation.load.flow_supply, space.ventilation.load.flow_extract, space.ventilation.load.flow_transfer)
        for variant in _phx_project.variants
        for zone in variant.zones
        for space in zone.spaces
    ]


def test_wufi_export_does_not_change_the_space_airflows(merged_by_erv_project: PhxProject) -> None:
    before = _space_airflows(merged_by_erv_project)

    xml_builder.generate_WUFI_XML_from_object(merged_by_erv_project)

    assert _space_airflows(merged_by_erv_project) == before


def test_metr_export_does_not_change_the_space_airflows(merged_by_erv_project: PhxProject) -> None:
    before = _space_airflows(merged_by_erv_project)

    metr_builder.generate_metr_json_dict(merged_by_erv_project)

    assert _space_airflows(merged_by_erv_project) == before


def test_wufi_export_is_repeatable(merged_by_erv_project: PhxProject) -> None:
    first = xml_builder.generate_WUFI_XML_from_object(merged_by_erv_project)
    second = xml_builder.generate_WUFI_XML_from_object(merged_by_erv_project)

    assert first == second


def test_metr_then_wufi_matches_wufi_alone(merged_by_erv_project: PhxProject) -> None:
    """Writing one project to two targets must not let the first contaminate the second."""
    wufi_alone = xml_builder.generate_WUFI_XML_from_object(merged_by_erv_project)

    metr_builder.generate_metr_json_dict(merged_by_erv_project)
    wufi_after_metr = xml_builder.generate_WUFI_XML_from_object(merged_by_erv_project)

    assert wufi_after_metr == wufi_alone


def test_export_does_not_rename_the_source_spaces(merged_by_erv_project: PhxProject) -> None:
    """The single-space branch of the merge sets 'display_name' from the vent unit."""
    before = [space.display_name for v in merged_by_erv_project.variants for z in v.zones for space in z.spaces]

    xml_builder.generate_WUFI_XML_from_object(merged_by_erv_project)

    after = [space.display_name for v in merged_by_erv_project.variants for z in v.zones for space in z.spaces]
    assert after == before
