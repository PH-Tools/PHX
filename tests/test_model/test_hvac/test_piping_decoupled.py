# -*- Python Version: 3.10 -*-

"""Tests verifying piping model classes work with PhxLineSegment (no ladybug_geometry)."""

import pytest

from PHX.model.geometry import PhxLineSegment, PhxVertix
from PHX.model.hvac.piping import PhxHotWaterPipingMaterial, PhxPipeElement, PhxPipeSegment


def _make_pipe_segment(length: float = 1.0, **kwargs) -> PhxPipeSegment:
    """Helper to create a PhxPipeSegment with PhxLineSegment geometry."""
    defaults = dict(
        identifier="test",
        display_name="test",
        geometry=PhxLineSegment(PhxVertix(0, 0, 0), PhxVertix(0, 0, length)),
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        diameter_m=0.0254,
        insulation_thickness_m=0.0254,
        insulation_conductivity=0.04,
        insulation_reflective=True,
        insulation_quality=None,
        daily_period=24,
    )
    defaults.update(kwargs)
    return PhxPipeSegment(**defaults)


def test_pipe_segment_length_from_phx_line_segment(reset_class_counters):
    seg = _make_pipe_segment(length=3.0)
    assert seg.length_m == pytest.approx(3.0)


def test_pipe_segment_heat_loss_reflective(reset_class_counters):
    seg = _make_pipe_segment(insulation_reflective=True)
    k = seg._solve_for_pipe_heat_loss_coeff()
    assert k == pytest.approx(0.18920200481210636)


def test_pipe_segment_heat_loss_non_reflective(reset_class_counters):
    seg = _make_pipe_segment(insulation_reflective=False)
    k = seg._solve_for_pipe_heat_loss_coeff()
    assert k == pytest.approx(0.21003911131648087)


def test_pipe_segment_from_length_classmethod(reset_class_counters):
    seg = PhxPipeSegment.from_length(
        display_name="test",
        length_m=5.0,
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        pipe_diameter_m=0.0254,
    )
    assert seg.length_m == pytest.approx(5.0)


def test_pipe_element_with_phx_geometry(reset_class_counters):
    seg = _make_pipe_segment(length=1.0)
    ele = PhxPipeElement("test_id", "test_name")
    ele.add_segment(seg)

    assert seg in ele.segments
    assert ele.length_m == pytest.approx(1.0)
    assert ele.weighted_pipe_heat_loss_coefficient == pytest.approx(0.18920200481210636)
    assert ele.weighted_diameter_mm == pytest.approx(25.4)


def test_pipe_element_multiple_segments(reset_class_counters):
    seg1 = _make_pipe_segment(identifier="s1", insulation_thickness_m=0.0100)
    seg2 = _make_pipe_segment(identifier="s2", insulation_thickness_m=0.0200)
    seg3 = _make_pipe_segment(identifier="s3", insulation_thickness_m=0.0400)

    ele = PhxPipeElement("test_id", "test_name")
    ele.add_segment(seg1)
    ele.add_segment(seg2)
    ele.add_segment(seg3)

    assert ele.length_m == pytest.approx(3.0)
    assert ele.weighted_pipe_heat_loss_coefficient == pytest.approx(0.21131471364804555)
    assert ele.weighted_diameter_mm == pytest.approx(25.4, rel=1e-3)
