# -*- Python Version: 3.10 -*-

"""Tests for PHX.PHPP.phpp_model.vent_ducts.VentDuctRow."""

from pathlib import Path

import pytest

from PHX.model.enums.hvac import PhxVentDuctType
from PHX.model.geometry import PhxLineSegment, PhxVertix
from PHX.model.hvac.ducting import PhxDuctElement, PhxDuctSegment
from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.PHPP.phpp_model.vent_ducts import VentDuctRow

SHAPE_DIR = Path("PHX", "PHPP", "phpp_localization")


def _load_addnl_vent_shape(filename: str):
    return PhppShape.model_validate_json((SHAPE_DIR / filename).read_bytes()).ADDNL_VENT


def _segment(
    identifier: str,
    length_m: float,
    diameter_m: float,
    height_m: float | None,
    width_m: float | None,
    insulation_thickness_m: float,
    insulation_conductivity_wmk: float,
    insulation_reflective: bool,
) -> PhxDuctSegment:
    return PhxDuctSegment(
        identifier=identifier,
        display_name=identifier,
        geometry=PhxLineSegment(PhxVertix(), PhxVertix(length_m, 0, 0)),
        diameter_m=diameter_m,
        height_m=height_m,
        width_m=width_m,
        insulation_thickness_m=insulation_thickness_m,
        insulation_conductivity_wmk=insulation_conductivity_wmk,
        insulation_reflective=insulation_reflective,
    )


def _items_by_range(row: VentDuctRow, sheet_name: str = "Addl vent", row_num: int = 95):
    return {item.xl_range: item for item in row.create_xl_items(sheet_name, row_num)}


def test_round_supply_duct_writes_si_fields(reset_class_counters):
    duct = PhxDuctElement("supply", "Supply duct", 7)
    duct.add_segment(_segment("a", 2.0, 0.1, None, None, 0.02, 0.04, False))
    duct.add_segment(_segment("b", 6.0, 0.2, None, None, 0.04, 0.06, True))

    items = _items_by_range(VentDuctRow(_load_addnl_vent_shape("EN_10_6.json"), duct, 2))

    assert set(items) == {"D95", "E95", "H95", "I95", "J95", "L95", "M95", "R95"}
    assert items["D95"].write_value == 1
    assert items["E95"].write_value == pytest.approx(175.0)
    assert items["E95"].input_unit == items["E95"].target_unit == "MM"
    assert items["H95"].write_value == pytest.approx(35.0)
    assert items["I95"].write_value == pytest.approx(0.055)
    assert items["J95"].write_value == "x"
    assert items["L95"].write_value == pytest.approx(8.0)
    assert items["M95"].write_value == 1
    assert items["R95"].write_value == 1


def test_rectangular_exhaust_duct_writes_ip_fields(reset_class_counters):
    duct = PhxDuctElement("exhaust", "Exhaust duct", 8)
    duct.duct_type = PhxVentDuctType.EXHAUST
    duct.add_segment(_segment("a", 3.048, 0.0, 0.3048, 0.6096, 0.0254, 0.04, False))

    items = _items_by_range(VentDuctRow(_load_addnl_vent_shape("EN_10_6IP.json"), duct, 10))

    assert set(items) == {"D95", "F95", "G95", "H95", "I95", "L95", "N95", "Z95"}
    assert items["F95"].write_value == pytest.approx(24.0)
    assert items["F95"].input_unit == "MM"
    assert items["F95"].target_unit == "IN"
    assert items["G95"].write_value == pytest.approx(12.0)
    assert items["H95"].write_value == pytest.approx(1.0)
    assert items["I95"].input_unit == "W/MK"
    assert items["I95"].target_unit == "HR-FT2-F/BTU-IN"
    assert items["I95"].write_value == pytest.approx(3.605697725)
    assert items["L95"].write_value == pytest.approx(10.0)
    assert items["L95"].target_unit == "FT"
    assert items["N95"].write_value == 1
    assert items["Z95"].write_value == 1


@pytest.mark.parametrize("vent_unit_number", [0, 11])
def test_vent_unit_assignment_must_be_between_one_and_ten(vent_unit_number, reset_class_counters):
    duct = PhxDuctElement("supply", "Supply duct", 7)

    with pytest.raises(ValueError, match="phpp_vent_unit_number must be between 1 and 10"):
        VentDuctRow(_load_addnl_vent_shape("EN_10_6.json"), duct, vent_unit_number)
