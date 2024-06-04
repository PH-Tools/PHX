import pathlib

from PHX.from_WUFI_XML.phx_converter import convert_WUFI_XML_to_PHX_project
from PHX.from_WUFI_XML.read_WUFI_XML_file import get_WUFI_XML_file_as_dict
from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject
from PHX.model.project import PhxProject


def test_read_xml_file(reset_class_counters) -> None:
    SOURCE_FILE = pathlib.Path("tests", "_reference_xml", "Multi_Room_Complete.xml")
    wufi_xml_data = get_WUFI_XML_file_as_dict(SOURCE_FILE)

    # -- make sure it returned something
    assert len(wufi_xml_data) > 1

    # -- make sure it has the right top-level keys
    for k in [
        "DataVersion",
        "UnitSystem",
        "ProgramVersion",
        "Scope",
        "DimensionsVisualizedGeometry",
        "ProjectData",
        "UtilisationPatternsVentilation",
        "UtilizationPatternsPH",
        "Variants",
        "Assemblies",
        "WindowTypes",
        "SolarProtectionTypes",
    ]:
        assert k in wufi_xml_data.keys()


def test_read_xml_and_convert_to_phx_project(reset_class_counters) -> None:
    SOURCE_FILE = pathlib.Path("tests", "_reference_xml", "Multi_Room_Complete.xml")
    wufi_xml_data = get_WUFI_XML_file_as_dict(SOURCE_FILE)
    wufi_xml_model = WUFIplusProject.model_validate(wufi_xml_data)
    phx_project = convert_WUFI_XML_to_PHX_project(wufi_xml_model)

    assert isinstance(phx_project, PhxProject)
