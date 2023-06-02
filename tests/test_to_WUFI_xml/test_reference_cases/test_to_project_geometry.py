from PHX.from_HBJSON import read_HBJSON_file, create_project
import pytest


def test_all_aperture_areas_are_equivalent_after_conversion(to_xml_reference_cases):
    # -- Get the test-case file paths
    hbjson_file, xml_file = to_xml_reference_cases

    # -- HB Model
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(hbjson_file)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

    # -- Get all the apertures in the HB Model
    hb_model_aps = {
        ap.display_name: ap
        for room in hb_model.rooms
        for face in room.faces
        for ap in face.apertures
    }

    # -- PhxProject file.
    phx_project = create_project.convert_hb_model_to_PhxProject(
        hb_model, _group_components=True, _merge_faces=True
    )
    for variant in phx_project.variants:
        for ap_compo in variant.building.aperture_components:
            for element in ap_compo.elements:
                hb_ap = hb_model_aps[element.display_name]
                assert hb_ap.area == pytest.approx(element.area)
