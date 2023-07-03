from typing import Any, Dict
from PHX.model import project
from PHX.from_WUFI_XML.phx_schemas import _PhxProject
from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject


def convert_WUFI_XML_to_PHX_project(_model: WUFIplusProject) -> project.PhxProject:
    phx_project = _PhxProject(_model)

    return phx_project
