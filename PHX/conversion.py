# -*- Python Version: 3.10 -*-

"""Public live-object conversion from Honeybee to the transient PHX model.

Use :func:`from_honeybee` when a Honeybee model already exists in memory. HBJSON
file reading is a separate concern handled by :mod:`PHX.from_HBJSON`.
"""

from honeybee.model import Model

from PHX.from_HBJSON import create_project
from PHX.model.project import PhxProject

__all__ = ["MissingHoneybeePhPropertiesError", "from_honeybee"]


class MissingHoneybeePhPropertiesError(ValueError):
    """Required honeybee-ph properties are missing from a conversion input.

    Attributes:
        object_path (str): Path to the Honeybee object whose ``properties.ph``
            extension is missing.
    """

    def __init__(self, object_path: str) -> None:
        self.object_path = object_path
        super().__init__(
            f"Honeybee object at '{object_path}' is missing required honeybee-ph properties. "
            "Load honeybee-ph and attach the extension before PHX conversion."
        )


def _require_honeybee_ph_properties(hb_object: object, object_path: str) -> None:
    properties = getattr(hb_object, "properties", None)
    if properties is None or getattr(properties, "ph", None) is None:
        raise MissingHoneybeePhPropertiesError(object_path)


def from_honeybee(
    hb_model: Model,
    *,
    group_components: bool = True,
    merge_faces: bool | float = False,
    merge_spaces_by_erv: bool = False,
    merge_exhaust_vent_devices: bool = False,
) -> PhxProject:
    """Convert a live Honeybee model with honeybee-ph data to a PHX project.

    This public facade delegates to the established Honeybee conversion
    implementation. It performs no HBJSON serialization or file I/O.

    Arguments:
    ----------
        * hb_model (Model): Live Honeybee model carrying honeybee-ph extensions.

        * group_components (bool): Group components by assembly type.
            Default: True.

        * merge_faces (bool | float): Merge coplanar faces. ``True`` uses the
            Honeybee model tolerance; a float supplies an explicit tolerance.
            Default: False.

        * merge_spaces_by_erv (bool): Merge spaces served by the same ERV.
            Default: False.

        * merge_exhaust_vent_devices (bool): Merge exhaust ventilation devices
            within each output zone. Default: False.

    Returns:
    --------
        * (PhxProject): Complete transient PHX project.

    Raises:
    -------
        * TypeError: If ``hb_model`` is not a ``honeybee.model.Model``.
        * MissingHoneybeePhPropertiesError: If the model or one of its rooms is
            missing the required ``properties.ph`` extension.
    """
    if not isinstance(hb_model, Model):
        input_type = type(hb_model)
        raise TypeError(
            "hb_model must be honeybee.model.Model; " f"got {input_type.__module__}.{input_type.__qualname__}"
        )

    model_path = f"Model '{hb_model.identifier}' at model.properties.ph"
    _require_honeybee_ph_properties(hb_model, model_path)
    for room in hb_model.rooms:
        room_path = f"Room '{room.identifier}' at rooms['{room.identifier}'].properties.ph"
        _require_honeybee_ph_properties(room, room_path)

    return create_project.convert_hb_model_to_PhxProject(
        hb_model,
        _group_components=group_components,
        _merge_faces=merge_faces,
        _merge_spaces_by_erv=merge_spaces_by_erv,
        _merge_exhaust_vent_devices=merge_exhaust_vent_devices,
    )
