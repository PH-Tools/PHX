# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions to create new Shade PhxComponents from HB-Model Orphaned-Shade Objects."""

from collections import defaultdict
from functools import reduce
import operator
from typing import List

from honeybee import model, shade

from PHX.model import components, project
from PHX.model.enums.building import (
    ComponentExposureExterior,
    ComponentFaceOpacity,
    ComponentColor,
)
from PHX.from_HBJSON import create_geometry


def create_new_component_from_orphaned_shade(
    _shade: shade.Shade,
) -> components.PhxComponentOpaque:
    """Returns a new PHX-Component for based on the Honeybee-Shade.

    Arguments:
    ----------
        * _shade (shade.Shade): The Honeybee-Shade to base the new component on.

    Returns:
    --------
        * (components.PhxComponentOpaque): A new PHX-Component for the HB-Shade.
    """

    new_compo = components.PhxComponentOpaque()

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
    _var: project.PhxVariant, _hb_model: model.Model
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

    # -- Group shades by their Display Name
    shade_groups = defaultdict(list)
    for hb_shade_face in _hb_model.orphaned_shades:
        shade_groups[hb_shade_face.display_name].append(
            create_new_component_from_orphaned_shade(hb_shade_face)
        )

    # -- Create new components from the groups
    grouped_shade_components: List[components.PhxComponentOpaque] = []
    for shade_group in shade_groups.values():
        merged_component = reduce(operator.add, shade_group)
        merged_component.display_name = shade_group[0].display_name
        grouped_shade_components.append(merged_component)

    for shade_component in grouped_shade_components:
        _var.building.add_components(shade_component)

    return None
