# -*- Python Version: 3.10 -*-

"""Tests for the PHPP 'U-values' surface-resistance selectors.

PHPP resolves each assembly block's Rsi/Rse from two selector cells (M10/M11 for
block '01ud'), reading only the leading digit of the selected string. Writing a
number instead makes PHPP take it verbatim, which drops the surface films from
every published U-value.

See: https://github.com/PH-Tools/PHX/issues/118
"""

import json
from pathlib import Path

import pytest

from PHX.model.constructions import PhxConstructionOpaque
from PHX.model.enums.building import ComponentExposureExterior, ComponentFaceType
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import uvalues_constructor

# -- The '01ud' block on a blank EN v10.6 sheet: header row 6, Rsi at M10, Rse at M11.
START_ROW = 6
RSI_RANGE = "M10"
RSE_RANGE = "M11"


def _make_shape() -> shape_model.UValues:
    """Load the real EN v10.6 shape so the column/offset data is correct."""
    json_path = Path(__file__).resolve().parents[3] / "PHX" / "PHPP" / "phpp_localization" / "EN_10_6.json"
    data = json.loads(json_path.read_text())
    return shape_model.UValues(**data["UVALUES"])


def _written_selectors(**kwargs) -> dict[str, str]:
    """Return {range: value} for the two surface-resistance cells of a block."""
    block = uvalues_constructor.ConstructorBlock(
        shape=_make_shape(),
        phx_construction=PhxConstructionOpaque(),
        **kwargs,
    )
    xl_items = {item.xl_range: item.write_value for item in block.create_xl_items("U-values", START_ROW)}
    return {RSI_RANGE: xl_items[RSI_RANGE], RSE_RANGE: xl_items[RSE_RANGE]}


def test_exterior_wall_selects_wall_and_outdoor_air() -> None:
    written = _written_selectors(
        face_type=ComponentFaceType.WALL,
        exposure_exterior=ComponentExposureExterior.EXTERIOR,
    )

    assert written == {RSI_RANGE: "2-Wall", RSE_RANGE: "1-Outdoor air"}


def test_roof_selects_roof() -> None:
    written = _written_selectors(
        face_type=ComponentFaceType.ROOF_CEILING,
        exposure_exterior=ComponentExposureExterior.EXTERIOR,
    )

    assert written == {RSI_RANGE: "1-Roof", RSE_RANGE: "1-Outdoor air"}


def test_ground_slab_selects_floor_and_ground() -> None:
    written = _written_selectors(
        face_type=ComponentFaceType.FLOOR,
        exposure_exterior=ComponentExposureExterior.GROUND,
    )

    assert written == {RSI_RANGE: "3-Floor", RSE_RANGE: "2-Ground"}


@pytest.mark.parametrize("exposure", [ComponentExposureExterior.SURFACE, ComponentExposureExterior(4)])
def test_exposure_to_another_zone_selects_ventilated(exposure) -> None:
    written = _written_selectors(face_type=ComponentFaceType.WALL, exposure_exterior=exposure)

    assert written == {RSI_RANGE: "2-Wall", RSE_RANGE: "3-Ventilated"}


def test_an_unreferenced_assembly_falls_back_to_wall_and_outdoor_air() -> None:
    """A Construction no Component uses still needs both selectors, or PHPP returns a blank U-value."""
    assert _written_selectors() == {RSI_RANGE: "2-Wall", RSE_RANGE: "1-Outdoor air"}
