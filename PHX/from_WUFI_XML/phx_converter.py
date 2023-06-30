from typing import Any, Dict
from PHX.model import project
from PHX.from_WUFI_XML.phx_schemas import _PhxProject


def convert_WUFI_XML_to_PHX_project(_data: Dict[str, Any]) -> project.PhxProject:
    phx_project = _PhxProject(_data)

    return phx_project
