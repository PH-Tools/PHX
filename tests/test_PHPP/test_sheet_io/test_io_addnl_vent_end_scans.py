# -*- Python Version: 3.10 -*-

"""End-of-section scans for user-extended PHPP Additional Ventilation blocks."""

import pytest

from PHX.PHPP.sheet_io.io_addnl_vent import ROW_SEARCH_LIMIT, Spaces, VentDucts, VentUnits
from PHX.xl.xl_app import XLConnection
from tests.test_PHPP.test_sheet_io.conftest import load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework


def _connect(_seed: dict[str, object]) -> tuple[XLConnection, object]:
    shape = load_shape().ADDNL_VENT
    fake_xl = FakeXLFramework(sheet_names=[shape.name], seed={shape.name: _seed})
    return XLConnection(xl_framework=fake_xl), shape


def _numbered_rows(_start: int, _count: int) -> dict[str, int]:
    return {f"C{row}": row - _start + 1 for row in range(_start, _start + _count)}


def test_units_block_extended_past_the_first_read_is_measured():
    xl, shape = _connect(_numbered_rows(70, 60))
    units = VentUnits(xl, shape)
    units._section_first_entry_row = 70

    assert units.find_section_last_entry_row() == 129


def test_duct_block_extended_past_the_first_read_is_measured():
    xl, shape = _connect({"D215": "Additional rows: please select full rows above"})
    ducts = VentDucts(xl, shape)
    ducts.section_first_entry_row = 95

    assert ducts.find_section_last_entry_row() == 214


def test_rooms_block_extended_past_the_first_read_is_measured():
    xl, shape = _connect(_numbered_rows(31, 80))
    rooms = Spaces(xl, shape)
    rooms.section_first_entry_row = 31

    assert rooms.find_section_last_entry_row() == 110


def test_units_scan_raises_when_no_end_is_found_before_the_limit():
    xl, shape = _connect(_numbered_rows(70, ROW_SEARCH_LIMIT))
    units = VentUnits(xl, shape)
    units._section_first_entry_row = 70

    with pytest.raises(Exception, match=f"before row {ROW_SEARCH_LIMIT}"):
        units.find_section_last_entry_row()
