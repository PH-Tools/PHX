import pytest

from PHX.xl import xl_data


def test_XlItem():
    item = xl_data.XlItem("sheet_1", "A1", 100)

    assert str(item)
    assert repr(item)
    assert item.xl_col_alpha == "A"
    assert item.xl_col_number == 65
    assert item.xl_row_number == 1
    assert item.write_value == 100


def test_XlItem_covert_M():
    item = xl_data.XlItem("sheet_1", "A1", 100, "M", "FT")
    assert item.write_value == pytest.approx(328.084)

    item = xl_data.XlItem("sheet_1", "A1", 100, "M", "IN")
    assert item.write_value == pytest.approx(3937.008)

    item = xl_data.XlItem("sheet_1", "A1", 100, "M", "CM")
    assert item.write_value == pytest.approx(10_000)

    item = xl_data.XlItem("sheet_1", "A1", 100, "M", "MM")
    assert item.write_value == pytest.approx(100_000)


def test_XlItem_covert_FT():
    item = xl_data.XlItem("sheet_1", "A1", 100, "FT", "FT")
    assert item.write_value == pytest.approx(100)

    item = xl_data.XlItem("sheet_1", "A1", 100, "FT", "IN")
    assert item.write_value == pytest.approx(1_200)

    item = xl_data.XlItem("sheet_1", "A1", 100, "FT", "CM")
    assert item.write_value == pytest.approx(3_048)

    item = xl_data.XlItem("sheet_1", "A1", 100, "FT", "MM")
    assert item.write_value == pytest.approx(30_480)


def test_XlItem_list():
    item = xl_data.XlItem("sheet_1", "A1", [1, 2, 3, 4], "FT", "FT")
    assert item.write_value == [1, 2, 3, 4]


def test_XlItem_row_and_col_numbers_parse_the_anchor_cell_only():
    # -- single-cell anchors
    item = xl_data.XlItem("sheet_1", "L41", None)
    assert item.xl_anchor_cell == "L41"
    assert item.xl_row_number == 41
    assert item.xl_col_number == xl_data.xl_ord("L")
    assert item.xl_col_alpha == "L"

    # -- multi-cell ranges (ie: block-clears) must not fold the end-cell in:
    # -- 'A1:D10' previously gave row 110 and a column blended from 'A' + 'D'.
    item = xl_data.XlItem("sheet_1", "A1:D10", None)
    assert item.xl_anchor_cell == "A1"
    assert item.xl_row_number == 1
    assert item.xl_col_number == xl_data.xl_ord("A")
    assert item.xl_col_alpha == "A"
