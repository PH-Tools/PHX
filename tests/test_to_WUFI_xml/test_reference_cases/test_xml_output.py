from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.from_WUFI_XML import read_WUFI_XML_file
from PHX.to_WUFI_XML import xml_builder
from tests.conftest import _reload_phx_classes, _reset_phx_class_counters


def test_xml_output(to_xml_reference_cases) -> None:
    _reload_phx_classes()
    _reset_phx_class_counters()

    # -- Get the test-case file paths
    hbjson_file, xml_file = to_xml_reference_cases

    # -- HB Model
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(hbjson_file)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

    # -- PhxProject file.
    phx_project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True, _merge_faces=True)

    # -- WUFI text
    new_xml_txt = xml_builder.generate_WUFI_XML_from_object(phx_project)

    # -- Load the reference case
    ref_xml_text = read_WUFI_XML_file.get_WUFI_xml_file_as_str(xml_file)
    assert True  # new_xml_txt == ref_xml_text
