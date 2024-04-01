from typing import Any, Dict

from PHX.from_WUFI_XML.phx_schemas import _PhxProject
from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject
from PHX.model import project


def convert_WUFI_XML_to_PHX_project(
    _wufi_xml_project: WUFIplusProject,
) -> project.PhxProject:
    """Convert a WUFI-XML-Project object over to a PHX-Project."""
    phx_project = _PhxProject(_wufi_xml_project)
    return phx_project
