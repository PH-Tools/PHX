# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions to create new Shade PhxComponents from HB-Model Orphaned-Shade Objects."""

import operator
from collections import defaultdict
from functools import reduce
from typing import List

try:
    from honeybee import model
    from honeybee.shade import Shade
except ImportError as e:
    raise ImportError("\nFailed to import Honeybee:\n\t{}".format(e))

try:
    from PHX.from_HBJSON import create_geometry
    from PHX.from_HBJSON.cleanup_merge_faces import merge_hb_shades
    from PHX.model import project
    from PHX.model.components import PhxComponentOpaque
    from PHX.model.enums.building import ComponentColor, ComponentExposureExterior, ComponentFaceOpacity
except ImportError as e:
    raise ImportError("\nFailed to import PHX:\n\t{}".format(e))

try:
    from honeybee_ph_utils import face_tools
except ImportError as e:
    raise ImportError("\nFailed to import honeybee_ph_utils:\n\t{}".format(e))


def create_new_component_from_orphaned_shade(
    _shade: Shade,
) -> PhxComponentOpaque:
    """Returns a new PHX-Component for based on the Honeybee-Shade.

    Arguments:
    ----------
        * _shade (shade.Shade): The Honeybee-Shade to base the new component on.

    Returns:
    --------
        * (components.PhxComponentOpaque): A new PHX-Component for the HB-Shade.
    """

    new_compo = PhxComponentOpaque()

    new_compo.display_name = _shade.display_name
    new_compo.face_opacity = ComponentFaceOpacity.OPAQUE
    new_compo.exposure_exterior = ComponentExposureExterior.EXTERIOR
    new_compo.exposure_interior = -1
    new_compo.color_interior = ComponentColor.EXT_WALL_INNER
    new_compo.color_exterior = ComponentColor.EXT_WALL_INNER

    # -- Polygons
    phx_polygon = create_geometry.create_PhxPolygon_from_hb_Face(_shade)
    new_compo.add_polygons(phx_polygon)

    return new_compo


def add_hb_model_shades_to_variant(
    _var: project.PhxVariant,
    _hb_model: model.Model,
    _merge_faces: bool,
    _tolerance: float,
    _angle_tolerance_degrees: float,
) -> None:
    """ "Create shading PhxComponents from an HB-model's orphaned shades and add to the PhxVariant.

    This will group shade-faces by display-name and create a single component for each named-group.

    Arguments:
    ----------
        * _var (project.Variant): The PhxVariant to add the Shading Objects to.
        * _hb_model (model.Model): The Honeybee-Model to get the orphaned shades from.

    Returns:
    --------
        * None
    """

    # -- Group HB-Shades by their Display Name
    hb_shade_groups: defaultdict[str, List[Shade]] = defaultdict(list)
    for hb_shade in _hb_model.orphaned_shades:
        hb_shade_groups[hb_shade.display_name].append(hb_shade)

    # -- Create new component(s) from the groups
    grouped_shade_components: List[PhxComponentOpaque] = []
    for hb_shade_group in hb_shade_groups.values():
        # -- Merge HB-Shade-Faces
        if _merge_faces:
            face_groups = face_tools.group_hb_faces(hb_shade_group, _tolerance, _angle_tolerance_degrees)
            hb_shade_group: List[Shade] = []
            for face_group in face_groups:
                hb_shade_group += merge_hb_shades(face_group, _tolerance, _angle_tolerance_degrees)

        phx_compos = (create_new_component_from_orphaned_shade(s) for s in hb_shade_group)
        merged_phx_component: PhxComponentOpaque = reduce(operator.add, phx_compos)
        merged_phx_component.display_name = hb_shade_group[0].display_name

        grouped_shade_components.append(merged_phx_component)

    # -- Add the new component(s) to the Variant
    for shade_component in grouped_shade_components:
        _var.building.add_components(shade_component)

    return None
