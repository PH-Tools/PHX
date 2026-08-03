# -*- Python Version: 3.10 -*-

"""Tests for the PHPP Additional Ventilation duct-section locator."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.PHPP.sheet_io.io_addnl_vent import VentDucts

SHAPE_DIR = Path("PHX", "PHPP", "phpp_localization")
SHAPE_FILENAMES = (
    "EN_9_6A.json",
    "EN_9_7IP.json",
    "EN_10_3.json",
    "EN_10_4A.json",
    "EN_10_4IP.json",
    "EN_10_6.json",
    "EN_10_6IP.json",
)


def _load_addnl_vent_shape(filename: str):
    return PhppShape.model_validate_json((SHAPE_DIR / filename).read_bytes()).ADDNL_VENT


def test_duct_header_search_includes_phpp_10_6_row_86():
    shape = _load_addnl_vent_shape("EN_10_6.json")
    xl = Mock()
    xl.get_single_column_data.return_value = [None] * 85 + ["Round duct diameter"]

    header_row = VentDucts(xl, shape).find_section_header_row()

    assert header_row == 86
    xl.get_single_column_data.assert_called_once_with(
        _sheet_name="Addl vent",
        _col="E",
        _row_start=1,
        _row_end=300,
    )


@pytest.mark.parametrize("shape_filename", SHAPE_FILENAMES)
@pytest.mark.parametrize(
    "marker",
    (
        "Additional lines",
        "Additional rows: please select full rows above, and compy and insert them multiple times.",
    ),
)
def test_duct_end_search_matches_additional_row_markers(shape_filename, marker):
    shape = _load_addnl_vent_shape(shape_filename)
    xl = Mock()
    xl.get_single_column_data.return_value = [None] * 20 + [marker]
    ducts = VentDucts(xl, shape)
    ducts.section_first_entry_row = 95

    last_entry_row = ducts.find_section_last_entry_row()

    assert last_entry_row == 114
    xl.get_single_column_data.assert_called_once_with(
        _sheet_name=shape.name,
        _col="D",
        _row_start=95,
        _row_end=195,
    )
