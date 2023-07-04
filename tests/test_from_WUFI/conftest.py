from pathlib import Path
import pytest
from PHX.from_HBJSON import read_HBJSON_file, create_project
from PHX.from_WUFI_XML.read_WUFI_XML_file import get_WUFI_XML_file_as_dict
from PHX.from_WUFI_XML.phx_converter import convert_WUFI_XML_to_PHX_project
from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject

from PHX.model.project import PhxProject


@pytest.fixture
def create_phx_project_from_hbjson() -> PhxProject:
    # -- Build the PhxProject from the HBJSON file
    SOURCE_HBJSON_FILE = Path("tests", "_source_hbjson", "Multi_Room_Complete.hbjson")
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(SOURCE_HBJSON_FILE)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)
    phx_project_hbjson = create_project.convert_hb_model_to_PhxProject(
        hb_model, _group_components=True, _merge_faces=True
    )
    return phx_project_hbjson


@pytest.fixture
def create_phx_project_from_wufi_xml() -> PhxProject:
    # --- Build the PhxProject from the WUFI XML file
    SOURCE_XML_FILE = Path("tests", "_reference_xml", "Multi_Room_Complete.xml")
    wufi_xml_data = get_WUFI_XML_file_as_dict(SOURCE_XML_FILE)
    wufi_xml_model = WUFIplusProject.parse_obj(wufi_xml_data)
    phx_project = convert_WUFI_XML_to_PHX_project(wufi_xml_model)
    return phx_project
