# -*- Python Version: 3.10 -*-

"""Focused tests for PHX.to_METr_JSON.metr_schemas."""

from PHX.model.constructions import PhxConstructionWindow, PhxWindowFrameElement
from PHX.to_METr_JSON.metr_schemas import _PhxConstructionWindow


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
