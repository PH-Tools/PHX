import pytest
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.polyline import LineSegment3D

from PHX.model.hvac.piping import PhxHotWaterPipingDiameter, PhxHotWaterPipingMaterial, PhxPipeElement, PhxPipeSegment


def test_empty_PhxPipeElement():
    o1 = PhxPipeElement(
        "test_identifier",
        "test_display_name",
    )

    assert not o1.segments


def test_add_single_segment_to_PhxPipeElement():
    # -- Segment
    p1, p2 = Point3D(0, 0, 0), Point3D(0, 0, 1)
    geom = LineSegment3D(p1, p2)

    seg = PhxPipeSegment(
        identifier="test",
        display_name="test-segment",
        geometry=geom,
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        pipe_diameter=PhxHotWaterPipingDiameter._1_0_0_IN,
        insulation_thickness_m=0.0254,
        insulation_conductivity=0.04,
        insulation_reflective=True,
        insulation_quality=None,
        daily_period=24,
    )

    # -- Element
    ele = PhxPipeElement("test_id", "test_name")
    ele.add_segment(seg)

    # --
    assert seg in ele.segments
    assert ele.length_m == 1
    assert ele.weighted_pipe_heat_loss_coefficient == pytest.approx(0.18920200481210636)
    assert ele.weighted_diameter_mm == 25.4


def test_add_multiple_segment_to_PhxPipeElement():
    # -- Segments
    p1, p2 = Point3D(0, 0, 0), Point3D(0, 0, 1)
    geom1 = LineSegment3D(p1, p2)

    seg1 = PhxPipeSegment(
        identifier="test1",
        display_name="test1",
        geometry=geom1,
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        pipe_diameter=PhxHotWaterPipingDiameter._1_0_0_IN,
        insulation_thickness_m=0.0100,
        insulation_conductivity=0.04,
        insulation_reflective=True,
        insulation_quality=None,
        daily_period=24,
    )
    seg2 = PhxPipeSegment(
        identifier="test2",
        display_name="test2",
        geometry=geom1,
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        pipe_diameter=PhxHotWaterPipingDiameter._1_0_0_IN,
        insulation_thickness_m=0.0200,
        insulation_conductivity=0.04,
        insulation_reflective=True,
        insulation_quality=None,
        daily_period=24,
    )
    seg3 = PhxPipeSegment(
        identifier="test3",
        display_name="test3",
        geometry=geom1,
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        pipe_diameter=PhxHotWaterPipingDiameter._1_0_0_IN,
        insulation_thickness_m=0.0400,
        insulation_conductivity=0.04,
        insulation_reflective=True,
        insulation_quality=None,
        daily_period=24,
    )

    # -- Element
    ele = PhxPipeElement("test_id", "test_name")
    ele.add_segment(seg1)
    ele.add_segment(seg2)
    ele.add_segment(seg3)

    # --
    assert seg1 in ele.segments
    assert seg2 in ele.segments
    assert seg3 in ele.segments
    assert ele.length_m == 3
    assert ele.weighted_pipe_heat_loss_coefficient == pytest.approx(0.21131471364804555)
    assert ele.weighted_diameter_mm == pytest.approx(25.399999999999995)
