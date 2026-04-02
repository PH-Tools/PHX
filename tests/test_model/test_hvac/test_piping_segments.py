import pytest
from ph_units.converter import convert

from PHX.model.enums.hvac import PhxHotWaterPipingInchDiameterType
from PHX.model.geometry import PhxLineSegment, PhxVertix
from PHX.model.hvac.piping import PhxHotWaterPipingMaterial, PhxPipeSegment


def test_PhxPipeSegment_to_wufi_diameter_type():
    geom = PhxLineSegment(PhxVertix(0, 0, 0), PhxVertix(0, 0, 1))

    seg = PhxPipeSegment(
        identifier="test",
        display_name="test",
        geometry=geom,
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        diameter_m=0.0254,
        insulation_thickness_m=0.0254,
        insulation_conductivity=0.04,
        insulation_reflective=True,
        insulation_quality=None,
        daily_period=24,
    )

    diameter_inches = convert(seg.diameter_mm, "MM", "IN") or 0.0
    assert PhxHotWaterPipingInchDiameterType.nearest_key(diameter_inches) == PhxHotWaterPipingInchDiameterType._1_0_0_IN


def test_PhxPipeSegment_heat_loss_coefficient_1():
    geom = PhxLineSegment(PhxVertix(0, 0, 0), PhxVertix(0, 0, 1))

    seg = PhxPipeSegment(
        identifier="test",
        display_name="test",
        geometry=geom,
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        diameter_m=0.0254,
        insulation_thickness_m=0.0254,
        insulation_conductivity=0.04,
        insulation_reflective=True,
        insulation_quality=None,
        daily_period=24,
    )

    k2 = seg._solve_for_pipe_heat_loss_coeff()
    assert k2 == pytest.approx(0.18920200481210636)


def test_PhxPipeSegment_heat_loss_coefficient_2():
    geom = PhxLineSegment(PhxVertix(0, 0, 0), PhxVertix(0, 0, 1))

    seg = PhxPipeSegment(
        identifier="test",
        display_name="test",
        geometry=geom,
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        diameter_m=0.0254,
        insulation_thickness_m=0.0254,
        insulation_conductivity=0.04,
        insulation_reflective=False,
        insulation_quality=None,
        daily_period=24,
    )

    k2 = seg._solve_for_pipe_heat_loss_coeff()
    assert k2 == pytest.approx(0.21003911131648087)
