# -*- Python Version: 3.10 -*-

"""Tests for PHX.PHPP.phpp_model.vent_space.VentSpaceRow.

The 'Addl vent' room row's 'Area' column (G) is the room's TFA / iCFA share and its
'clear height' column (H) is the reference height PHPP multiplies that area by for
the ventilated volume Vv. Neither is the room's gross floor area or actual clear height.
"""

from pathlib import Path

import pytest

from PHX.model import spaces
from PHX.model.schedules.ventilation import PhxScheduleVentilation
from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.PHPP.phpp_model.vent_space import VentSpaceRow

SHAPE_DIR = Path("PHX", "PHPP", "phpp_localization")


def _load_addnl_vent_shape(filename: str):
    return PhppShape.model_validate_json((SHAPE_DIR / filename).read_bytes()).ADDNL_VENT


def _space(floor_area: float, weighted_floor_area: float, clear_height: float) -> spaces.PhxSpace:
    space = spaces.PhxSpace()
    space.display_name = "Living"
    space.floor_area = floor_area
    space.weighted_floor_area = weighted_floor_area
    space.clear_height = clear_height
    return space


def _items_by_range(space: spaces.PhxSpace, sheet_name: str = "Addl vent", row_num: int = 56):
    row = VentSpaceRow(_load_addnl_vent_shape("EN_10_6.json"), space, 1, PhxScheduleVentilation())
    return {item.xl_range: item for item in row.create_xl_items(sheet_name, row_num)}


def test_area_column_takes_the_weighted_floor_area(reset_class_counters):
    items = _items_by_range(_space(floor_area=20.0, weighted_floor_area=12.0, clear_height=3.2))

    assert items["G56"].write_value == pytest.approx(12.0)
    assert items["G56"].input_unit == items["G56"].target_unit == "M2"


def test_clear_height_column_takes_the_ventilation_reference_height(reset_class_counters):
    items = _items_by_range(_space(floor_area=20.0, weighted_floor_area=12.0, clear_height=3.2))

    assert items["H56"].write_value == pytest.approx(2.5)
    assert items["H56"].input_unit == items["H56"].target_unit == "M"


def test_a_space_with_no_weighted_area_writes_its_gross_area(reset_class_counters):
    # -- A WUFI import sets both areas from one cell; a source that never set the
    # -- weighted area must keep writing what it wrote before this column was corrected.
    items = _items_by_range(_space(floor_area=20.0, weighted_floor_area=0.0, clear_height=3.2))

    assert items["G56"].write_value == pytest.approx(20.0)


def test_a_custom_reference_height_is_written(reset_class_counters):
    space = _space(floor_area=20.0, weighted_floor_area=12.0, clear_height=3.2)
    space.ventilation_reference_height = 2.6

    items = _items_by_range(space)

    assert items["H56"].write_value == pytest.approx(2.6)
