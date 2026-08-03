# -*- Python Version: 3.10 -*-

"""Tests for PPP schema functions."""

import pytest

from PHX.model.components import PhxApertureElement, PhxComponentAperture, PhxComponentOpaque
from PHX.model.constructions import PhxConstructionWindow
from PHX.model.project import PhxProject, PhxVariant
from PHX.to_PPP.ppp_builder import _build_frame_map, _build_glazing_map
from PHX.to_PPP.ppp_schemas import (
    _pad_num,
    _pad_num_offset,
    _pad_text,
    overbuilt_sections,
    user_component_sections,
    window_sections,
)


def test_pad_text():
    result = _pad_text(["a", "b"], 5)
    assert result == ["a", "b", "-", "-", "-"]


def test_pad_num():
    result = _pad_num(["1", "2"], 4)
    assert result == ["1", "2", "", ""]


def test_pad_num_offset():
    result = _pad_num_offset(["1", "2"], 5)
    assert result == ["", "1", "2", "", ""]
    assert len(result) == 5


def test_overbuilt_sections():
    sections = overbuilt_sections()
    assert len(sections) == 5
    assert all(s.rows == 1 and s.cols == 1 for s in sections)


@pytest.mark.parametrize(
    ("psi_attribute", "frame_row_index", "expected_values"),
    [
        ("psi_install", 43, ("0.002500", "0.005000")),
        ("psi_glazing", 37, ("0.010000", "0.020000")),
    ],
)
def test_distinct_frame_psi_values_create_distinct_rows_and_window_references(
    psi_attribute: str,
    frame_row_index: int,
    expected_values: tuple[str, str],
):
    project = PhxProject()
    variant = PhxVariant()
    project.add_new_variant(variant)

    opaque_component = PhxComponentOpaque()
    variant.building.add_component(opaque_component)

    for index, psi_value in enumerate((0.01, 0.02), start=1):
        window_type = PhxConstructionWindow(display_name=f"Window type {index}")
        window_type.frame_type_display_name = "Shared frame"
        window_type.glazing_type_display_name = "Shared glazing"
        setattr(window_type.frame_left, psi_attribute, psi_value)
        project.add_new_window_type(window_type, f"window-type-{index}")

        aperture = PhxComponentAperture(opaque_component)
        aperture.set_window_type(window_type)
        element = PhxApertureElement(aperture)
        element.display_name = f"Window {index}"
        aperture.add_element(element)
        opaque_component.apertures.append(aperture)

    glazing_map = _build_glazing_map(project)
    frame_map = _build_frame_map(project)

    assert len(frame_map) == 2

    frame_section = next(
        section
        for section in user_component_sections(project, glazing_map, frame_map, {})
        if section.name == "Komponenten_user_Fensterrahmen"
    )
    assert frame_section.values[0] == "Shared frame"
    assert frame_section.values[44] == "Shared frame"
    assert frame_section.values[frame_row_index] == expected_values[0]
    assert frame_section.values[44 + frame_row_index] == expected_values[1]

    window_frame_section = next(
        section for section in window_sections(variant, {}, glazing_map, frame_map) if section.name == "Fenster_Rahmen"
    )
    assert window_frame_section.values[:2] == ["01ud-Shared frame", "02ud-Shared frame"]
