# -*- Python Version: 3.10 -*-

"""End-to-end test: HBJSON → PHX → METr JSON, comparing against reference files."""

import json

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.to_METr_JSON import metr_builder
from tests.conftest import _reset_phx_class_counters


def test_metr_json_output_single_zone(to_metr_json_reference_cases) -> None:
    """Test that HBJSON → PHX → METr JSON produces valid, parseable JSON."""
    _reset_phx_class_counters()

    hbjson_file, metr_json_file = to_metr_json_reference_cases

    # -- Build the PHX Model from HBJSON
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(hbjson_file)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)
    phx_project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True, _merge_faces=True)

    # -- Generate METr JSON
    result_dict = metr_builder.generate_metr_json_dict(phx_project)

    # -- Verify it's a valid dict and can round-trip through JSON
    json_text = json.dumps(result_dict, indent=2)
    parsed = json.loads(json_text)

    # -- Basic structural checks
    assert isinstance(parsed, dict)
    assert "progVers" in parsed
    assert "lMaterial" in parsed
    assert "lAssembly" in parsed
    assert "lVariant" in parsed
    assert "lUtilVentPH" in parsed
    assert "lUtilNResPH" in parsed
    assert "timeProf" in parsed
    assert "projD" in parsed

    # -- Check materials were extracted
    assert len(parsed["lMaterial"]) > 0

    # -- Check assemblies reference valid material IDs
    material_ids = {m["id"] for m in parsed["lMaterial"]}
    for assembly in parsed["lAssembly"]:
        for layer in assembly["lLayer"]:
            assert layer["idMat"] in material_ids, (
                f"Assembly '{assembly['n']}' layer references material ID {layer['idMat']} "
                f"which is not in lMaterial (valid IDs: {material_ids})"
            )

    # -- Check at least one variant with geometry
    assert len(parsed["lVariant"]) > 0
    variant = parsed["lVariant"][0]
    assert "geom" in variant
    assert len(variant["geom"]["lIDXYZ"]) > 0
    assert len(variant["geom"]["lPoly"]) > 0

    # -- Load and compare with reference (structural comparison)
    with open(metr_json_file) as f:
        ref = json.load(f)

    # -- Compare top-level keys (our output should have all keys the reference has,
    # -- though we may be missing some that are in later phases)
    ref_top_keys = set(ref.keys())
    our_top_keys = set(parsed.keys())
    assert our_top_keys == ref_top_keys, (
        f"Top-level key mismatch.\n"
        f"  Missing from output: {ref_top_keys - our_top_keys}\n"
        f"  Extra in output: {our_top_keys - ref_top_keys}"
    )
