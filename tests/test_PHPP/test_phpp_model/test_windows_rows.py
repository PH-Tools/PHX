# -*- Python Version: 3.10 -*-

"""Tests for PHX.PHPP.phpp_model.windows_rows.WindowRow."""

from pathlib import Path

import pytest

from PHX.model import constructions, geometry
from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.PHPP.phpp_model.windows_rows import WindowRow
from PHX.xl import xl_data

SHAPE_DIR = Path("PHX", "PHPP", "phpp_localization")


def _load_shape(filename: str) -> PhppShape:
    return PhppShape.model_validate_json((SHAPE_DIR / filename).read_bytes())


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


def _construction() -> constructions.PhxConstructionWindow:
    construction = constructions.PhxConstructionWindow()
    construction.frame_left.psi_install = 0.01
    construction.frame_right.psi_install = 0.02
    construction.frame_bottom.psi_install = 0.03
    construction.frame_top.psi_install = 0.04
    return construction


def _expand_items(items):
    for item in items:
        if isinstance(item, xl_data.XLItem_List):
            yield from item.items
        else:
            yield item


@pytest.mark.parametrize(
    ("shape_filename", "target_unit", "conversion_factor"),
    [
        ("EN_10_4A.json", "W/MK", 1.0),
        ("EN_10_4IP.json", "BTU/HR-FT-F", 0.577789236),
        ("EN_10_6.json", "W/MK", 1.0),
        ("EN_10_6IP.json", "BTU/HR-FT-F", 0.577789236),
    ],
)
def test_window_row_writes_explicit_psi_install_to_physical_side_columns(
    reset_class_counters,
    shape_filename: str,
    target_unit: str,
    conversion_factor: float,
):
    shape = _load_shape(shape_filename)
    row = WindowRow(
        shape=shape.WINDOWS,
        phx_polygon=_rect_polygon(1.0, 2.0),
        phx_construction=_construction(),
        phpp_host_surface_id_name="host",
        phpp_id_frame="frame",
        phpp_id_glazing="glazing",
        phpp_id_variant_type="variant",
    )

    items = {item.xl_range: item for item in _expand_items(row.create_xl_items("Windows", 24))}
    expected = {"AN24": 0.01, "AO24": 0.02, "AQ24": 0.03, "AP24": 0.04}

    for xl_range, value in expected.items():
        assert items[xl_range]._write_value == pytest.approx(value)
        assert items[xl_range].input_unit == "W/MK"
        assert items[xl_range].target_unit == target_unit
        assert items[xl_range].write_value == pytest.approx(value * conversion_factor)


@pytest.mark.parametrize(
    "shape_filename",
    ["EN_10_4A.json", "EN_10_4IP.json", "EN_10_6.json", "EN_10_6IP.json"],
)
def test_components_psi_install_bottom_and_top_columns_match_phpp(shape_filename: str):
    frames = _load_shape(shape_filename).COMPONENTS.frames.inputs

    assert frames.psi_i_bottom.column == "KB"
    assert frames.psi_i_top.column == "KA"
