# -*- Python Version: 3.10 -*-

"""Focused tests for PHX.to_METr_JSON.metr_schemas."""

import pytest

from PHX.model import elec_equip
from PHX.model.constructions import (
    PhxConstructionOpaque,
    PhxConstructionWindow,
    PhxLayer,
    PhxMaterial,
    PhxWindowFrameElement,
)
from PHX.to_METr_JSON.metr_schemas import _PhxConstructionOpaque, _PhxConstructionWindow, _PhxElectricalDevice


def test_window_frame_arrays_follow_metr_left_right_top_bottom_order(reset_class_counters):
    window = PhxConstructionWindow()
    window.frame_left = PhxWindowFrameElement(
        width=0.1,
        u_value=1.1,
        psi_glazing=0.01,
        psi_install=0.001,
    )
    window.frame_right = PhxWindowFrameElement(
        width=0.2,
        u_value=1.2,
        psi_glazing=0.02,
        psi_install=0.002,
    )
    window.frame_top = PhxWindowFrameElement(
        width=0.3,
        u_value=1.3,
        psi_glazing=0.03,
        psi_install=0.003,
    )
    window.frame_bottom = PhxWindowFrameElement(
        width=0.4,
        u_value=1.4,
        psi_glazing=0.04,
        psi_install=0.004,
    )

    result = _PhxConstructionWindow(window)

    assert result["lrtbFrW"] == [0.1, 0.2, 0.3, 0.4]
    assert result["lrtbFrU"] == [1.1, 1.2, 1.3, 1.4]
    assert result["lrtbGlPsi"] == [0.01, 0.02, 0.03, 0.04]
    assert result["lrtbFrPsi"] == [0.001, 0.002, 0.003, 0.004]


@pytest.mark.parametrize(
    "device_class",
    [elec_equip.PhxDeviceRefrigerator, elec_equip.PhxDeviceFreezer, elec_equip.PhxDeviceFridgeFreezer],
)
@pytest.mark.parametrize("wufi_norm, metr_ref_ed", [(1, 2), (2, 3)])  # WUFI Day/Year -> METr Day/Year
def test_fridge_type_ref_ed_follows_reference_energy_norm(reset_class_counters, device_class, wufi_norm, metr_ref_ed):
    device = device_class()
    device.reference_energy_norm = wufi_norm

    assert _PhxElectricalDevice(device)["refED"] == metr_ref_ed


def test_mixed_layer_writes_exchange_divisions_and_materials(reset_class_counters):
    insulation = PhxMaterial(display_name="insulation")
    stud = PhxMaterial(display_name="stud")
    layer = PhxLayer(thickness_m=0.18415)
    layer.set_material(insulation)
    layer.divisions.set_column_widths([0.18415, 0.0381, 0.3683, 0.0381, 0.18415])
    layer.divisions.add_new_row(1.0)
    layer.divisions.set_cell_material(1, 0, stud)
    layer.divisions.set_cell_material(3, 0, stud)
    assembly = PhxConstructionOpaque()
    assembly.layers = [layer]

    result = _PhxConstructionOpaque(assembly)["lLayer"][0]

    assert result["lExDivH"] == [0.18415, 0.0381, 0.3683, 0.0381, 0.18415]
    assert result["lExDivV"] == []  # -- a single row is omitted
    assert result["lExMat"] == [[1, 0, stud.id_num], [3, 0, stud.id_num]]
