from PHX.from_WUFI_XML.phx_schemas import _PhxProject
from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject
from PHX.model import project
from PHX.model.identity import build_project_with_identities


def convert_WUFI_XML_to_PHX_project(
    _wufi_xml_project: WUFIplusProject,
) -> project.PhxProject:
    """Convert a WUFI-XML Pydantic project schema into a PHX-Project model.

    Arguments:
    ----------
        * _wufi_xml_project (WUFIplusProject): The parsed WUFI-XML project.

    Returns:
    --------
        * (project.PhxProject): A new PHX project with all data from the WUFI file.
    """
    return build_project_with_identities(lambda: _PhxProject(_wufi_xml_project))
