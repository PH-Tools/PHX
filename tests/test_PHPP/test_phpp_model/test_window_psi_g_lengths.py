# -*- Python Version: 3.10 -*-

"""Tests for PHPP window psi-g length aggregation."""

import pytest

from PHX.model import components, constructions, geometry, project
from PHX.PHPP.phpp_app import PHPPConnection


def _rect_polygon(width: float, height: float) -> geometry.PhxPolygonRectangular:
    polygon = geometry.PhxPolygonRectangular(
        _display_name="window",
        _area=width * height,
        _center=geometry.PhxVertix(width / 2, height / 2, 0.0),
        normal_vector=geometry.PhxVector(0.0, 0.0, 1.0),
        plane=geometry.PhxPlane(
            geometry.PhxVector(0, 0, 1),
            geometry.PhxVertix(0, 0, 0),
            geometry.PhxVector(1, 0, 0),
            geometry.PhxVector(0, 1, 0),
        ),
    )
    polygon.vertix_lower_left = geometry.PhxVertix(0, 0, 0)
    polygon.vertix_lower_right = geometry.PhxVertix(width, 0, 0)
    polygon.vertix_upper_right = geometry.PhxVertix(width, height, 0)
    polygon.vertix_upper_left = geometry.PhxVertix(0, height, 0)
    return polygon


def test_collect_window_psi_g_lengths_uses_glazing_edge_lengths(reset_class_counters):
    window_type = constructions.PhxConstructionWindow()
    window_type.frame_left.width = 0.1
    window_type.frame_right.width = 0.2
    window_type.frame_bottom.width = 0.4
    window_type.frame_top.width = 0.3

    host = components.PhxComponentOpaque()
    aperture = components.PhxComponentAperture(_host=host)
    aperture.window_type = window_type

    element = components.PhxApertureElement(_host=aperture)
    element.polygon = _rect_polygon(width=2.0, height=3.0)
    aperture.add_element(element)
    host.add_aperture(aperture)

    phx_variant = project.PhxVariant()
    phx_variant.building.add_component(host)

    phx_project = project.PhxProject()
    phx_project.add_new_window_type(window_type)
    phx_project.add_new_variant(phx_variant)

    result = PHPPConnection._collect_window_psi_g_lengths(phx_project)

    assert result[window_type.identifier] == pytest.approx(
        {
            "psi_g_left": 2.3,
            "psi_g_right": 2.3,
            "psi_g_bottom": 1.7,
            "psi_g_top": 1.7,
        }
    )
