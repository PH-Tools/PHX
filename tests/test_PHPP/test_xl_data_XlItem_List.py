import pytest

from PHX.xl import xl_data


def test_xl_item_merge_none():
    items = []
    items_merged = xl_data.merge_xl_item_row(items)
    assert len(items_merged) == 0


def test_xl_item_different_sheets_do_not_merge():
    item_a = xl_data.XlItem("example_A", "A1", 12)
    item_b = xl_data.XlItem("example_B", "B1", 12)
    item_c = xl_data.XlItem("example_C", "C1", 12)
    items = [item_a, item_b, item_c]

    items_merged = xl_data.merge_xl_item_row(items)
    assert len(items_merged) == 3


def test_xl_item_different_rows_do_not_merge():
    item_a = xl_data.XlItem("example", "A1", 12)
    item_b = xl_data.XlItem("example", "B2", 12)
    item_c = xl_data.XlItem("example", "C3", 12)
    items = [item_a, item_b, item_c]

    items_merged = xl_data.merge_xl_item_row(items)
    assert len(items_merged) == 3


def test_xl_item_merge_single_group():
    items = [
        xl_data.XlItem("example", "L1", 12),
        xl_data.XlItem("example", "M1", 12),
        xl_data.XlItem("example", "N1", 12),
        xl_data.XlItem("example", "O1", 12),
    ]

    items_merged = xl_data.merge_xl_item_row(items)
    assert len(items_merged) == 1
    assert items_merged[0].xl_col_alpha == "L"
    assert items_merged[0].xl_col_number == xl_data.xl_ord("L")


def test_xl_item_merge_2_groups():
    items = [
        xl_data.XlItem("example", "AA1", 12),
        xl_data.XlItem("example", "AB1", 12),
        xl_data.XlItem("example", "BC1", 12),
        xl_data.XlItem("example", "BD1", 12),
    ]

    items_merged = xl_data.merge_xl_item_row(items)
    assert len(items_merged) == 2
    assert items_merged[0].xl_col_alpha == "AA"
    assert items_merged[0].xl_col_number == xl_data.xl_ord("AA")

    assert items_merged[1].xl_col_alpha == "BC"
    assert items_merged[1].xl_col_number == xl_data.xl_ord("BC")


def test_xl_item_merge_3_groups_in_order():
    items = [
        xl_data.XlItem("example", "E1", 12),
        xl_data.XlItem("example", "Q1", 12),
        xl_data.XlItem("example", "AZ1", 12),
        xl_data.XlItem("example", "BA1", 12),
    ]

    items_merged = xl_data.merge_xl_item_row(items)
    assert len(items_merged) == 3
    assert items_merged[0].xl_col_alpha == "E"
    assert items_merged[0].xl_col_number == xl_data.xl_ord("E")

    assert items_merged[1].xl_col_alpha == "Q"
    assert items_merged[1].xl_col_number == xl_data.xl_ord("Q")

    assert items_merged[2].xl_col_alpha == "AZ"
    assert items_merged[2].xl_col_number == xl_data.xl_ord("AZ")


def test_xl_item_merge_3_groups_out_of_order():
    items = [
        xl_data.XlItem("example", "AZ1", 12),
        xl_data.XlItem("example", "BA1", 12),
        xl_data.XlItem("example", "E1", 12),
        xl_data.XlItem("example", "Q1", 12),
    ]

    items_merged = xl_data.merge_xl_item_row(items)
    assert len(items_merged) == 3

    assert items_merged[0].xl_col_alpha == "E"
    assert items_merged[0].xl_col_number == xl_data.xl_ord("E")

    assert items_merged[1].xl_col_alpha == "Q"
    assert items_merged[1].xl_col_number == xl_data.xl_ord("Q")

    assert items_merged[2].xl_col_alpha == "AZ"
    assert items_merged[2].xl_col_number == xl_data.xl_ord("AZ")


def test_manual_add_item():
    xl_list = xl_data.XLItem_List([])
    item_a = xl_data.XlItem("example_sheet", "A1", 12)
    xl_list.add_new_xl_item(item_a)

    assert item_a in xl_list.items

    item_b = xl_data.XlItem("example_sheet", "B1", 12)
    xl_list.add_new_xl_item(item_b)

    assert item_b in xl_list.items

    item_c = xl_data.XlItem("example_sheet", "C1", 12)
    xl_list.add_new_xl_item(item_c)

    assert item_c in xl_list.items


def test_manual_add_item_exception():
    xl_list = xl_data.XLItem_List([])
    item_a = xl_data.XlItem("example_sheet", "A1", 12)
    xl_list.add_new_xl_item(item_a)

    assert item_a in xl_list.items

    item_b = xl_data.XlItem("example_sheet", "D1", 12)
    with pytest.raises(Exception):
        xl_list.add_new_xl_item(item_b)


def test_XlItem_List():
    items = [
        xl_data.XlItem("example", "L1", 12),
        xl_data.XlItem("example", "M1", 12),
        xl_data.XlItem("example", "N1", 12),
        xl_data.XlItem("example", "O1", 12),
    ]

    item_list = xl_data.XLItem_List(_items=[])
    for item in xl_data.merge_xl_item_row(items):
        item_list.add_new_xl_item(item)

    assert item_list.write_value == [[12, 12, 12, 12]]
    assert item_list.sheet_name == "example"
    assert item_list.xl_range == "L1"
    assert item_list.xl_row_number == 1
    assert item_list.xl_col_number == 76
    assert item_list.xl_col_alpha == "L"
