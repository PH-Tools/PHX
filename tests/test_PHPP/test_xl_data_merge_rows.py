# -*- Python Version: 3.10 -*-

"""Tests for xl_data.merge_xl_item_rows (T1.2/T1.3 section-block batching)."""

from PHX.xl import xl_data
from PHX.xl.xl_data import XlItem, XLItem_List, merge_xl_item_row, merge_xl_item_rows


def _surface_style_row(row: int, name: str, area: float) -> list[XlItem]:
    """A row like the Areas surfaces: contiguous L-N group, then isolated T."""
    return [
        XlItem("Areas", f"L{row}", name),
        XlItem("Areas", f"M{row}", "12-"),
        XlItem("Areas", f"N{row}", 1),
        XlItem("Areas", f"T{row}", area),
    ]


def test_uniform_consecutive_rows_become_column_blocks():
    rows = [_surface_style_row(41, "Wall-A", 10.0), _surface_style_row(42, "Wall-B", 20.0)]
    result = merge_xl_item_rows(rows)

    assert len(result) == 2  # one L-N block + one T block
    block_l, block_t = sorted(result, key=lambda i: i.xl_col_number)

    assert block_l.sheet_name == "Areas"
    assert block_l.xl_range == "L41"
    assert block_l.write_value == [["Wall-A", "12-", 1], ["Wall-B", "12-", 1]]

    assert block_t.xl_range == "T41"
    assert block_t.write_value == [[10.0], [20.0]]


def test_single_row_still_produces_blocks():
    result = merge_xl_item_rows([_surface_style_row(41, "Wall-A", 10.0)])
    assert len(result) == 2
    assert result[0].write_value == [["Wall-A", "12-", 1]]


def test_non_consecutive_rows_fall_back_to_per_row_groups():
    rows = [_surface_style_row(41, "Wall-A", 10.0), _surface_style_row(43, "Wall-B", 20.0)]  # gap at 42
    result = merge_xl_item_rows(rows)

    # -- fallback: 2 merged groups per row (L-N list + T item), nothing stacked
    assert len(result) == 4
    assert any(isinstance(item, XLItem_List) for item in result)
    assert not any(isinstance(item.write_value, list) and isinstance(item.write_value[0], list) for item in result)


def test_mismatched_row_schemas_fall_back():
    rows = [
        _surface_style_row(41, "Wall-A", 10.0),
        [XlItem("Areas", "L42", "Wall-B")],  # different column layout
    ]
    result = merge_xl_item_rows(rows)
    assert not any(isinstance(item.write_value, list) and isinstance(item.write_value[0], list) for item in result)


def test_colored_items_pass_through_individually():
    plain = [
        XlItem("Sheet1", "A1", 1),
        XlItem("Sheet1", "B1", 2),
    ]
    colored = XlItem("Sheet1", "D1", 3, range_color=(255, 0, 0), font_color=(0, 0, 0))
    rows = [
        plain + [colored],
        [
            XlItem("Sheet1", "A2", 4),
            XlItem("Sheet1", "B2", 5),
            XlItem("Sheet1", "D2", 6, range_color=(255, 0, 0), font_color=(0, 0, 0)),
        ],
    ]
    result = merge_xl_item_rows(rows)

    blocks = [item for item in result if isinstance(item.write_value, list) and isinstance(item.write_value[0], list)]
    passthrough = [item for item in result if item.has_color]
    assert len(blocks) == 1
    assert blocks[0].xl_range == "A1"
    assert blocks[0].write_value == [[1.0, 2.0], [4.0, 5.0]] or blocks[0].write_value == [[1, 2], [4, 5]]
    assert len(passthrough) == 2
    assert {item.xl_range for item in passthrough} == {"D1", "D2"}


def test_pre_merged_xl_item_list_rows_are_expanded_and_stacked():
    """Windows-style: create_xl_items already returns merge_xl_item_row output."""
    row_1 = merge_xl_item_row(
        [XlItem("Windows", "L23", 1), XlItem("Windows", "M23", "w-1"), XlItem("Windows", "R23", 0.9)]
    )
    row_2 = merge_xl_item_row(
        [XlItem("Windows", "L24", 1), XlItem("Windows", "M24", "w-2"), XlItem("Windows", "R24", 1.2)]
    )
    result = merge_xl_item_rows([row_1, row_2])  # type: ignore

    assert len(result) == 2
    block_l, block_r = sorted(result, key=lambda i: i.xl_col_number)
    assert block_l.xl_range == "L23"
    assert block_l.write_value == [[1, "w-1"], [1, "w-2"]]
    assert block_r.xl_range == "R23"
    assert block_r.write_value == [[0.9], [1.2]]


def test_unit_conversion_is_baked_into_block_values():
    rows = [
        [XlItem("Areas", "T41", 10.0, "M2", "FT2")],
        [XlItem("Areas", "T42", 20.0, "M2", "FT2")],
    ]
    (block,) = merge_xl_item_rows(rows)
    assert block.write_value[0][0] != 10.0  # converted
    assert round(block.write_value[0][0], 2) == 107.64
    assert round(block.write_value[1][0], 2) == 215.28


def test_empty_and_trivial_inputs():
    assert merge_xl_item_rows([]) == []
    assert merge_xl_item_rows([[], []]) == []


def test_blocks_write_correctly_through_xl_connection():
    """End-to-end: block items land per-cell exactly like the per-item path."""
    from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

    from PHX.xl.xl_app import XLConnection

    def run(items) -> dict:
        fake = FakeXLFramework(sheet_names=["Areas"])
        conn = XLConnection(xl_framework=fake)
        for item in items:
            conn.write_xl_item(item)
        return fake.written_state()

    rows = [_surface_style_row(41, "Wall-A", 10.0), _surface_style_row(42, "Wall-B", 20.0)]
    per_item_state = run([item for row in rows for item in row])
    rows = [_surface_style_row(41, "Wall-A", 10.0), _surface_style_row(42, "Wall-B", 20.0)]
    merged_state = run(merge_xl_item_rows(rows))

    assert merged_state == per_item_state


def test_merge_rows_output_type_is_writable():
    """Every returned item must expose the write_xl_item interface."""
    rows = [_surface_style_row(41, "A", 1.0), _surface_style_row(43, "B", 2.0)]  # fallback path
    for item in xl_data.merge_xl_item_rows(rows):
        assert hasattr(item, "sheet_name")
        assert hasattr(item, "xl_range")
        _ = item.write_value
        _ = item.has_color
        _ = item.value_is_iterable
