# -*- Python Version: 3.10 -*-

"""Schema lookup: finds the appropriate METr JSON schema function for a given PHX object."""

from collections.abc import Callable
from typing import Any

from PHX.to_METr_JSON import metr_schemas


class NoMETrSchemaFoundError(Exception):
    def __init__(self, _schema_module, _phx_object, _schema_nm):
        self.message = (
            f'\n  Error: Cannot find a METr JSON schema for the object: "{_phx_object}"'
            f'\n  of type "{type(_phx_object)}" using the schema name: "{_schema_nm}"'
            f'\n  in file: "{_schema_module.__file__}". Please check the schemas.'
        )
        super().__init__(self.message)


def get_schema_function(_phx_object: Any, _schema_name: str | None = None) -> Callable[[Any], dict | list]:
    """Returns the appropriate METr JSON schema function for the PHX-object.

    Arguments:
    ----------
        * _phx_object: The PHX-Object to find the METr JSON schema for.
        * _schema_name: Optional explicit name of the schema function to use.
            If None, will use the object's class name preceded by an underscore.
            ie: "PhxProject" → "_PhxProject"

    Returns:
    --------
        * Callable: The schema function which returns a dict or list.
    """
    if _schema_name is None:
        _schema_name = f"_{_phx_object.__class__.__name__}"

    schema_function = getattr(metr_schemas, _schema_name, None)
    if not schema_function:
        raise NoMETrSchemaFoundError(metr_schemas, _phx_object, _schema_name)

    return schema_function
