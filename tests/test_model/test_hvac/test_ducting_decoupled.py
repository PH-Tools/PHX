# -*- Python Version: 3.10 -*-

"""Tests verifying ducting model classes work with PhxLineSegment (no ladybug_geometry)."""

import pytest

from PHX.model.geometry import PhxLineSegment, PhxVertix
from PHX.model.hvac.ducting import PhxDuctElement, PhxDuctSegment


def test_duct_segment_length(reset_class_counters):
    seg = PhxDuctSegment(
        identifier="test",
        display_name="test",
        geometry=PhxLineSegment(PhxVertix(0, 0, 0), PhxVertix(0, 0, 1)),
        diameter_m=0.0254,
        height_m=None,
        width_m=None,
        insulation_thickness_m=0.0254,
        insulation_conductivity_wmk=0.04,
        insulation_reflective=True,
    )
    assert seg.length == pytest.approx(1.0)


def test_duct_element_length(reset_class_counters):
    seg = PhxDuctSegment(
        identifier="test",
        display_name="test",
        geometry=PhxLineSegment(PhxVertix(0, 0, 0), PhxVertix(0, 0, 3)),
        diameter_m=0.0254,
        height_m=None,
        width_m=None,
        insulation_thickness_m=0.0254,
        insulation_conductivity_wmk=0.04,
        insulation_reflective=True,
    )

    ele = PhxDuctElement("test_id", "test_name", 1)
    ele.add_segment(seg)

    assert ele.length_m == pytest.approx(3.0)
    assert ele.diameter_mm == pytest.approx(25.4)
    assert ele.insulation_thickness_mm == pytest.approx(25.4)
