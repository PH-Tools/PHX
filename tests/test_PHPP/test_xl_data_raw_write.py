"""Tests for 'xl_data.prepare_raw_write' - the T1.5 raw-write shaping shim.

The shim reproduces, in Python, what the xlwings '.value' converter does on
macOS before it hands data to appscript: element cleaning (None/NaN -> '',
int -> float, date -> datetime), 1D -> 2D shaping, transposition, and the
anchor-cell -> full-block address expansion the converter does by resizing.
"""

import datetime
import math

import pytest

from PHX.xl import xl_data

# -----------------------------------------------------------------------------
# -- Scalars


def test_scalar_string_passes_through():
    item = xl_data.XlItem("Sheet1", "L41", "some value")
    assert xl_data.prepare_raw_write(item) == ("L41", "some value")


def test_scalar_int_becomes_float():
    # -- appscript packs large ints as SInt64, which Excel ignores (xlwings GH #227)
    item = xl_data.XlItem("Sheet1", "L41", 42)
    address, data = xl_data.prepare_raw_write(item)
    assert address == "L41"
    assert data == 42.0
    assert isinstance(data, float)


def test_scalar_bool_stays_bool():
    item = xl_data.XlItem("Sheet1", "L41", True)
    address, data = xl_data.prepare_raw_write(item)
    assert data is True


def test_scalar_none_becomes_empty_string():
    item = xl_data.XlItem("Sheet1", "L41", None)
    assert xl_data.prepare_raw_write(item) == ("L41", "")


def test_scalar_nan_becomes_empty_string():
    item = xl_data.XlItem("Sheet1", "L41", math.nan)
    assert xl_data.prepare_raw_write(item) == ("L41", "")


def test_scalar_date_becomes_datetime():
    item = xl_data.XlItem("Sheet1", "L41", datetime.date(2026, 7, 15))
    address, data = xl_data.prepare_raw_write(item)
    assert data == datetime.datetime(2026, 7, 15)
    assert isinstance(data, datetime.datetime)


# -----------------------------------------------------------------------------
# -- 1D lists (one row across the columns)


def test_1d_list_expands_across_the_row():
    item = xl_data.XlItem("Sheet1", "L41", ["a", None, 3])
    address, data = xl_data.prepare_raw_write(item)
    assert address == "L41:N41"
    assert data == [["a", "", 3.0]]


def test_1d_list_transposed_expands_down_the_column():
    item = xl_data.XlItem("Sheet1", "L41", ["a", "b", "c"])
    address, data = xl_data.prepare_raw_write(item, _transpose=True)
    assert address == "L41:L43"
    assert data == [["a"], ["b"], ["c"]]


def test_single_item_list_collapses_to_a_scalar():
    item = xl_data.XlItem("Sheet1", "L41", [7])
    assert xl_data.prepare_raw_write(item) == ("L41", 7.0)


def test_column_beyond_z_expands_correctly():
    item = xl_data.XlItem("Sheet1", "AA5", [1, 2, 3])
    address, data = xl_data.prepare_raw_write(item)
    assert address == "AA5:AC5"


# -----------------------------------------------------------------------------
# -- 2D lists (blocks from 'merge_xl_item_rows')


def test_2d_block_expands_to_the_full_extent():
    item = xl_data.XlItem("Sheet1", "L41", [["a", "b", "c"], [1, None, 3]])
    address, data = xl_data.prepare_raw_write(item)
    assert address == "L41:N42"
    assert data == [["a", "b", "c"], [1.0, "", 3.0]]


def test_1x1_2d_block_collapses_to_a_scalar():
    item = xl_data.XlItem("Sheet1", "L41", [["only"]])
    assert xl_data.prepare_raw_write(item) == ("L41", "only")


def test_ragged_2d_block_raises_value_error():
    item = xl_data.XlItem("Sheet1", "L41", [["a", "b"], ["c"]])
    with pytest.raises(ValueError):
        xl_data.prepare_raw_write(item)


# -----------------------------------------------------------------------------
# -- Unit conversion happens before shaping


def test_unit_conversion_is_baked_into_the_raw_data():
    item = xl_data.XlItem("Sheet1", "L41", 1.0, input_unit="M", target_unit="MM")
    address, data = xl_data.prepare_raw_write(item)
    assert address == "L41"
    assert data == pytest.approx(1000.0)


# -----------------------------------------------------------------------------
# -- XLItem_List anchors


def test_xl_item_list_expands_from_its_first_item():
    items = xl_data.XLItem_List(
        [
            xl_data.XlItem("Sheet1", "B2", 1),
            xl_data.XlItem("Sheet1", "C2", 2),
            xl_data.XlItem("Sheet1", "D2", 3),
        ]
    )
    address, data = xl_data.prepare_raw_write(items)
    assert address == "B2:D2"
    assert data == [[1.0, 2.0, 3.0]]
