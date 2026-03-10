# -*- Python Version: 3.10 -*-

"""Integration test: build PPP from example HBJSON model."""

import pathlib

import pytest

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.to_PPP import ppp_builder, ppp_txt_to_file

EXAMPLE_HBJSON = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "plans"
    / "ppp_exporter"
    / "honeybee-ph-example"
    / "example_honeybee_model.hbjson"
)


@pytest.fixture
def phx_project():
    """Load the example HBJSON and convert to PhxProject."""
    if not EXAMPLE_HBJSON.exists():
        pytest.skip(f"Example HBJSON not found: {EXAMPLE_HBJSON}")
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(EXAMPLE_HBJSON)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)
    return create_project.convert_hb_model_to_PhxProject(
        hb_model,
        _group_components=True,
        _merge_faces=False,
        _merge_spaces_by_erv=False,
        _merge_exhaust_vent_devices=False,
    )


def test_build_ppp_file_structure(phx_project):
    """Test that the generated PPP has the correct structure."""
    ppp_file = ppp_builder.build_ppp_file(phx_project)

    # Check total section count: 8 meta + 5 EBF + 14 surfaces + 8 TB + 9 windows
    # + 8 shading + 6 ventilation + 480 U-value + 3 user components + 5 overbuilt = 546
    assert len(ppp_file.sections) == 546

    # Check first section
    assert ppp_file.sections[0].name == "pppmeta_kopf"
    assert ppp_file.sections[0].rows == 5
    assert ppp_file.sections[0].cols == 1

    # Check end markers
    lines = ppp_file.to_lines()
    markers = [l for l in lines if "End of designPH" in l]
    assert len(markers) == 3

    # Check last section
    assert ppp_file.sections[-1].name == "Flaechen_Flaecheneingabe_eigener_Abzug_Ueberbaut"


def test_build_ppp_surfaces(phx_project):
    """Test that surfaces are correctly populated."""
    ppp_file = ppp_builder.build_ppp_file(phx_project)

    # Find surface names section
    name_section = next(s for s in ppp_file.sections if s.name == "Flaechen_Flaecheneingabe_Bauteil_Bezeichnung")
    assert name_section.rows == 100
    # Should have some actual names (not all dashes)
    actual_names = [v for v in name_section.values if v != "-"]
    assert len(actual_names) > 0

    # Find group section
    group_section = next(s for s in ppp_file.sections if s.name == "Flaechen_Flaecheneingabe_Zuordnung_zu_Gruppe")
    actual_groups = [v for v in group_section.values if v]
    assert len(actual_groups) > 0
    # All actual groups should be valid labels
    valid_prefixes = {"8-", "9-", "10-", "11-", "12-", "18-"}
    for g in actual_groups:
        assert any(g.startswith(p) for p in valid_prefixes), f"Invalid group: {g}"


def test_write_ppp_file(phx_project, tmp_path):
    """Test that the PPP file can be written to disk."""
    ppp_file = ppp_builder.build_ppp_file(phx_project)
    output = tmp_path / "test.ppp"
    ppp_txt_to_file.write_ppp_file(output, ppp_file)

    assert output.exists()
    # Read back and verify UTF-16LE encoding
    raw = output.read_bytes()
    assert raw[:2] == b"\xff\xfe"  # UTF-16LE BOM
