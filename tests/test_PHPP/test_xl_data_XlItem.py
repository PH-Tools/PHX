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
