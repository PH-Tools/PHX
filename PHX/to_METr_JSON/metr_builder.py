# -*- Python Version: 3.10 -*-

"""Main entry point: converts a PhxProject into a METr JSON dict, then to JSON text."""

import json
from typing import Any

from PHX.to_METr_JSON import metr_converter


def generate_metr_json_dict(_phx_object: Any, _schema_name: str | None = None) -> dict:
    """Convert a PHX object into a METr JSON dict by looking up and calling its schema function.

    Arguments:
    ----------
        * _phx_object: The PHX object to convert (typically a PhxProject).
        * _schema_name: Optional explicit schema function name.

    Returns:
    --------
        * dict: The METr JSON representation.
    """
    schema_function = metr_converter.get_schema_function(_phx_object, _schema_name)
    return schema_function(_phx_object)


def generate_metr_json_text(_phx_object: Any, _schema_name: str | None = None) -> str:
    """Convert a PHX object into METr JSON text.

    Arguments:
    ----------
        * _phx_object: The PHX object to convert (typically a PhxProject).
        * _schema_name: Optional explicit schema function name.

    Returns:
    --------
        * str: The METr JSON as formatted text.
    """
    metr_dict = generate_metr_json_dict(_phx_object, _schema_name)
    return json.dumps(metr_dict, indent=2, ensure_ascii=False)
