from pathlib import Path

from PHX.from_HBJSON import create_project, read_HBJSON_file


def test_opaque_assembly_uses_exterior_material_radiation_properties(reset_class_counters):
    file_path = Path("tests", "reference_files", "from_grasshopper_tests", "hbjson", "Default_Model_Single_Zone.hbjson")
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(file_path)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

    hb_face = hb_model.rooms[0].faces[0]
    hb_construction = hb_face.properties.energy.construction
    exterior_material = hb_construction.materials[0]
    exterior_material.unlock()
    exterior_material.solar_absorptance = 0.35
    exterior_material.thermal_absorptance = 0.82

    phx_project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True)
    phx_assembly = phx_project.assembly_types[hb_construction.identifier]

    assert phx_assembly.exterior_solar_absorptance == 0.35
    assert phx_assembly.exterior_thermal_emissivity == 0.82
