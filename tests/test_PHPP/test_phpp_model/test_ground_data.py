# -*- Python Version: 3.10 -*-

"""Tests for the PHPP 'Ground' worksheet model: one PHX foundation as building-section-1 inputs.

See: https://github.com/PH-Tools/PHX/issues/120
"""

import pytest

from PHX.model import ground
from PHX.model.enums.foundations import FoundationType, PerimeterInsulationPosition
from PHX.model.phx_site import PhxGround
from PHX.PHPP.phpp_localization.shape_model import Ground as GroundShape
from PHX.PHPP.phpp_model.ground_data import GroundExportError, GroundFoundationBlock
from tests.test_PHPP.test_sheet_io.conftest import load_shape

HEADER_ROW = 22  # -- 'Floor slab type (select only one)' in the blank 10.6
SOIL_DEFAULTS = {"H9": 2.0, "H10": 2.0, "H53": 3.0, "H54": 0.05}


def _shape() -> GroundShape:
    return load_shape("EN_10_6.json").GROUND


def _cells(_foundation: ground.PhxFoundation, _soil: PhxGround | None = None) -> dict:
    block = GroundFoundationBlock(_shape(), _soil or PhxGround(), _foundation)
    return {item.xl_range: item.write_value for item in block.create_xl_items("Ground", HEADER_ROW)}


def _selectors(_marked: str) -> dict[str, str]:
    return {cell: "x" if cell == _marked else "" for cell in ("C24", "C30", "C33", "C40")}


def test_slab_on_grade():
    slab = ground.PhxSlabOnGrade()
    slab.floor_slab_exposed_perimeter_m = 18.0
    slab.perim_insulation_position = PerimeterInsulationPosition.HORIZONTAL
    slab.perim_insulation_width_or_depth_m = 1.2
    slab.perim_insulation_thickness_m = 0.1
    slab.perim_insulation_conductivity = 0.035
    slab.interior_wall_to_heated_area_m2 = 5.0
    slab.interior_wall_to_heated_u_value = 0.4

    assert _cells(slab) == {
        **SOIL_DEFAULTS,
        **_selectors("C24"),
        "H19": 18.0,
        "H25": 1.2,
        "H26": 0.1,
        "H27": 0.035,
        "P25": "x",
        "H28": 5.0,
        "P28": 0.4,
    }


def test_heated_basement_derives_the_below_grade_wall_area():
    basement = ground.PhxHeatedBasement()
    basement.floor_slab_exposed_perimeter_m = 40.0
    basement.slab_depth_below_grade_m = 2.5
    basement.basement_wall_u_value = 0.3

    assert _cells(basement) == {**SOIL_DEFAULTS, **_selectors("C30"), "H19": 40.0, "H31": 100.0, "P31": 0.3}


def test_unheated_basement_derives_both_wall_areas():
    basement = ground.PhxUnHeatedBasement()
    basement.floor_slab_exposed_perimeter_m = 40.0
    basement.basement_wall_height_above_grade_m = 0.5
    basement.slab_depth_below_grade_m = 2.0
    basement.basement_wall_uValue_above_grade = 0.6
    basement.basement_wall_uValue_below_grade = 0.4
    basement.interior_wall_to_heated_area_m2 = 12.0
    basement.interior_wall_to_heated_u_value = 0.35
    basement.basement_ventilation_ach = 0.2
    basement.floor_slab_u_value = 0.5
    basement.basement_volume_m3 = 150.0

    assert _cells(basement) == {
        **SOIL_DEFAULTS,
        **_selectors("C33"),
        "H19": 40.0,
        "H34": 20.0,
        "P34": 0.6,
        "H35": 80.0,
        "P35": 0.4,
        "H36": 12.0,
        "P36": 0.35,
        "H37": 0.2,
        "P37": 0.5,
        "H38": 150.0,
    }


def test_vented_crawlspace():
    crawlspace = ground.PhxVentedCrawlspace()
    crawlspace.crawlspace_floor_exposed_perimeter_m = 36.0
    crawlspace.crawlspace_floor_u_value = 0.8
    crawlspace.crawlspace_vent_opening_are_m2 = 0.6
    crawlspace.crawlspace_wall_height_above_grade_m = 0.4
    crawlspace.wind_velocity_at_10m_m_s = 5.0
    crawlspace.crawlspace_wall_u_value = 1.1
    crawlspace.wind_shield_factor = 0.02
    crawlspace.interior_wall_to_heated_area_m2 = 3.0
    crawlspace.interior_wall_to_heated_u_value = 0.4

    assert _cells(crawlspace) == {
        **SOIL_DEFAULTS,
        **_selectors("C40"),
        "H19": 36.0,
        "H41": 0.8,
        "P41": 0.6,
        "H42": 0.4,
        "P42": 5.0,
        "H43": 1.1,
        "P43": 0.02,
        "H44": 3.0,
        "P44": 0.4,
    }


def test_soil_heat_capacity_is_converted_to_mj_per_m3k():
    soil = PhxGround(ground_density=1800.0, ground_heat_capacity=850.0)

    assert _cells(ground.PhxSlabOnGrade(), soil)["H10"] == pytest.approx(1.53)


@pytest.mark.parametrize(
    "position, p25",
    [
        (PerimeterInsulationPosition.HORIZONTAL, "x"),
        (PerimeterInsulationPosition.VERTICAL, ""),
    ],
)
def test_insulation_orientation_writes_the_horizontal_check_only(position, p25):
    slab = ground.PhxSlabOnGrade()
    slab.perim_insulation_position = position

    cells = _cells(slab)

    assert cells["P25"] == p25
    assert "P26" not in cells


def test_an_unset_value_is_written_blank():
    slab = ground.PhxSlabOnGrade()
    slab.perim_insulation_width_or_depth_m = None

    assert _cells(slab)["H25"] == ""


@pytest.mark.parametrize("attr_name", ["slab_depth_below_grade_m", "basement_wall_u_value"])
def test_heated_basement_without_a_wall_below_grade_is_refused(attr_name):
    basement = ground.PhxHeatedBasement()
    basement.floor_slab_exposed_perimeter_m = 40.0
    setattr(basement, attr_name, 0.0)

    with pytest.raises(GroundExportError, match="Ground!S31"):
        _cells(basement)


def test_bare_foundation_is_refused():
    with pytest.raises(GroundExportError, match="PhxFoundation"):
        _cells(ground.PhxFoundation())


def test_foundation_type_disagreeing_with_the_class_is_refused():
    slab = ground.PhxSlabOnGrade()
    slab.foundation_type_num = FoundationType.HEATED_BASEMENT

    with pytest.raises(GroundExportError, match="HEATED_BASEMENT"):
        _cells(slab)
