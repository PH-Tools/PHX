# -*- Python Version: 3.10 -*-

"""Basic datatypes and data-structures relevant for Excel read/write."""

import datetime
import math
import string
from typing import Any, Optional, Union

from ph_units import converter

xl_writable = Optional[str | float | int | list | tuple]
xl_range_single_value = Union[str, float, int, None]
xl_range_list1D_value = Union[list[str], list[float], list[int], list[None]]
xl_range_list2D_value = Union[list[list[str]], list[list[float]], list[list[int]], list[list[None]]]
xl_range_value = Union[xl_range_single_value, xl_range_list1D_value, xl_range_list2D_value]


def xl_ord(_col: str) -> int:
    """ord() which supports excel columns beyond Z (AA, AB, ...)"""
    num = 0
    for c in _col.upper():
        if c in string.ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord("A")) + 1
    return num + 64


def xl_chr(_i: int) -> str:
    """chr() which supports excel columns beyond Z (AA, AB, ...)"""
    letters = ""
    num = _i - 64
    while num:
        mod = (num - 1) % 26
        letters += chr(mod + 65)
        num = (num - 1) // 26
    return "".join(reversed(letters))


def xl_col_num_as_chr(_i: int) -> str:
    """Return the character for an Excel Column Num (1-based).
    ie: 1->"A", 2->"B", etc..
    """
    return xl_chr(_i + 64)


def col_offset(_col: str, _offset: int) -> str:
    """Return a column character, offset from the base by a specified amount."""
    base = xl_ord(_col)
    new = base + _offset
    return xl_chr(new)


class XlItem:
    """A single XLItem which can be written out to a specific XL Range."""

    def __init__(
        self,
        sheet_name: str,
        xl_range: str,
        write_value: xl_writable,
        input_unit: str | None = None,
        target_unit: str | None = None,
        range_color: tuple[int, int, int] | None = None,
        font_color: tuple[int, int, int] | None = None,
    ):
        self.sheet_name = sheet_name
        self.xl_range = xl_range
        self._write_value = write_value
        self.input_unit = input_unit
        self.target_unit = target_unit
        self.xl_range_base = xl_range
        self.range_color = range_color
        self.font_color = font_color

    @property
    def xl_anchor_cell(self) -> str:
        """The range's top-left (anchor) cell. ie: 'A1:D10' -> 'A1', 'L41' -> 'L41'."""
        return self.xl_range.split(":")[0]

    @property
    def xl_row_number(self) -> int:
        # -- Parse the anchor cell only: joining digits across a multi-cell
        # -- range would fold the end-row in (ie: 'A1:D10' -> 110).
        # -- Note: was previously int(first-digit-char), so 'L41' gave 4 and
        # -- 'L41' vs 'L48' compared as the same row in merge_xl_item_row.
        return int("".join(_ for _ in self.xl_anchor_cell if _.isdigit()))

    @property
    def xl_col_number(self) -> int:
        return xl_ord(self.xl_anchor_cell)

    @property
    def xl_col_alpha(self) -> str:
        return xl_chr(self.xl_col_number)

    @property
    def write_value(self) -> xl_writable:
        # -- Try to convert the unit (SI/IP)

        if not self.input_unit or not self.target_unit:
            return self._write_value

        if isinstance(self._write_value, (tuple, list)):
            return [converter.convert(v, self.input_unit, self.target_unit) for v in self._write_value]
        else:
            return converter.convert(self._write_value, self.input_unit, self.target_unit)

    @property
    def has_color(self) -> bool:
        """Return True if the Item has font or background color values."""
        return bool(self.font_color and self.range_color)

    @property
    def value_is_iterable(self) -> bool:
        """Return True is the item's value is a List or Tuple"""
        return isinstance(self.write_value, (list, tuple))

    def __str__(self):
        return f"{self.__class__.__name__}({self.sheet_name}, {self.xl_range}, {self.write_value})"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(sheet_name={self.sheet_name}, range={self.xl_range}, value={self.write_value})"
        )

    def __len__(self) -> int:
        try:
            return len(self.write_value)  # type: ignore
        except:
            return 0


class XLItem_List:
    """A list of XLItems which yield a list when 'write_value' is called.
    This will write the data our to the columns in the row.

    ie: A1=[12, 13, 14] --> A1=12, B1=13, C1=14

    This is helpful to speed up the XL writing, since writing a single list
    is much faster than writing several XlItems one at a time.
    """

    def __init__(self, _items: list[XlItem]):
        self._items = _items

    @property
    def items(self):
        return sorted(self._items, key=lambda i: i.xl_col_number)

    def validate_xl_item_range(self, _xl_item: XlItem) -> None:
        """Raise Exception if the XlItem being added has an invalid xl_range."""
        check_item = self.items[-1]
        if _xl_item.xl_col_number != check_item.xl_col_number + 1:
            msg = (
                f"\n\tError: The XlItem with xl_range: '{_xl_item.xl_range}' "
                f"cannot be added to the XlItem_List with item "
                f"ranges: '{[i.xl_range for i in self.items]}'. "
                "Ranges should be in order ie: A, B, C, etc.."
            )
            raise Exception(msg)

    def add_new_xl_item(self, _xl_item: XlItem) -> None:
        if self.items:
            self.validate_xl_item_range(_xl_item)

        self._items.append(_xl_item)

    @property
    def write_value(self) -> list[xl_writable]:
        return [_.write_value for _ in self.items]

    @property
    def sheet_name(self) -> str:
        return self.items[0].sheet_name

    @property
    def xl_range(self) -> str:
        return self.items[0].xl_range

    @property
    def xl_row_number(self) -> int:
        return self.items[0].xl_row_number

    @property
    def xl_col_number(self) -> int:
        return self.items[0].xl_col_number

    @property
    def xl_col_alpha(self) -> str:
        return self.items[0].xl_col_alpha

    @property
    def range_color(self):
        return self.items[0].range_color

    @property
    def font_color(self):
        return self.items[0].font_color

    @property
    def has_color(self) -> bool:
        """Return True if any of the Items has font or background color values."""
        return any(item.font_color or item.range_color for item in self.items)

    @property
    def value_is_iterable(self) -> bool:
        """Return True."""
        return True

    def __len__(self) -> int:
        return len(self._items)


def _group_width(_group: Union[XlItem, XLItem_List]) -> int:
    """Return the number of columns a merged row-group spans."""
    if isinstance(_group, XLItem_List):
        return len(_group)
    if _group.value_is_iterable:
        return len(_group.write_value)  # type: ignore
    return 1


def _group_row_values(_group: Union[XlItem, XLItem_List]) -> list:
    """Return a merged row-group's (unit-converted) values as a flat list."""
    if isinstance(_group, XLItem_List):
        return list(_group.write_value)
    if _group.value_is_iterable:
        return list(_group.write_value)  # type: ignore
    return [_group.write_value]


def _expand_to_xl_items(_row: list) -> list[XlItem]:
    """Flatten any XLItem_List entries in a row back to their base XlItems."""
    items: list[XlItem] = []
    for entry in _row:
        if isinstance(entry, XLItem_List):
            items.extend(entry.items)
        else:
            items.append(entry)
    return items


def _as_raw_write_element(_value: Any) -> Any:
    """Return a single value in the form the raw (converter-less) write path expects.

    Reproduces xlwings' macOS 'prepare_xl_data_element' for the types PHX writes:
    'None' and NaN become '' (which clears the cell), ints become floats
    (appscript packs large ints as SInt64, which Excel silently ignores - xlwings
    GH #227), and dates become datetimes. Strings, floats and bools pass through.
    """
    if _value is None:
        return ""
    if isinstance(_value, bool):  # -- must be tested before int
        return _value
    if isinstance(_value, int):
        return float(_value)
    if isinstance(_value, float) and math.isnan(_value):
        return ""
    if isinstance(_value, datetime.datetime):
        return _value.replace(tzinfo=None)
    if isinstance(_value, datetime.date):
        return datetime.datetime(_value.year, _value.month, _value.day)
    return _value


def prepare_raw_write(
    _xl_item: Union[XlItem, XLItem_List], _transpose: bool = False
) -> tuple[str, Any]:
    """Return the (full-range-address, raw-shaped-data) for a 'raw_value' write.

    The xlwings '.value' converter costs ~5x per write on macOS (one extra
    AppleEvent layer per op). Writing through 'range.raw_value' skips it, but
    then the shaping the converter normally does must happen here in Python:
    values are cleaned ('_as_raw_write_element'), 1D lists become one 2D row,
    transposition is applied, and the target address is expanded from the
    anchor cell to the full block extent (the converter does this by resizing
    the range - computing the address is free, resizing is not).

    Arguments:
    ----------
        * _xl_item: (XlItem | XLItem_List) The item to write. Must have a
            single-cell anchor 'xl_range' (ie: "L41", not "L41:N41").
        * _transpose: (bool) Transpose the value before writing (lists write
            down the column instead of across the row). Default=False.

    Returns:
    --------
        * (tuple[str, Any]): The full target range address and the write-ready
            data: a scalar for single-cell writes, or a shape-matching 2D list.
    """
    value = _xl_item.write_value

    if not isinstance(value, (list, tuple)):
        return _xl_item.xl_range, _as_raw_write_element(value)

    if value and isinstance(value[0], (list, tuple)):
        rows_2d = [list(row) for row in value]
    else:
        rows_2d = [list(value)]

    if _transpose:
        rows_2d = [list(row) for row in zip(*rows_2d)]

    n_cols = len(rows_2d[0])
    if any(len(row) != n_cols for row in rows_2d):
        raise ValueError(f"Cannot raw-write a ragged 2D value to '{_xl_item.xl_range}': {rows_2d}")

    rows_2d = [[_as_raw_write_element(v) for v in row] for row in rows_2d]

    if len(rows_2d) == 1 and n_cols == 1:
        return _xl_item.xl_range, rows_2d[0][0]

    end_col = xl_chr(_xl_item.xl_col_number + n_cols - 1)
    end_row = _xl_item.xl_row_number + len(rows_2d) - 1
    return f"{_xl_item.xl_range}:{end_col}{end_row}", rows_2d


def merge_xl_item_rows(_rows: list[list[XlItem]]) -> list[Union[XlItem, XLItem_List]]:
    """Merge per-row XlItems for CONSECUTIVE rows into 2D block XlItems.

    This is the section-level batcher: each input row is first merged into
    contiguous column-groups ('merge_xl_item_row'), and when every row shares
    the same column layout and the rows are consecutive, each column-group is
    stacked across the rows into a single 2D-valued XlItem — one write for the
    whole section instead of one write per cell (or per row).

    ie: rows at L41.. and L42.. each with groups (L:N), (T) become two XlItems:
    'L41'=[[...],[...]] and 'T41'=[[...],[...]].

    Items with font/range colors are never merged into blocks — they are
    returned as individual XlItems (the color-write path is per-cell).
    If the rows are not uniform or not consecutive, falls back to returning
    the per-row merged groups unchanged.

    Arguments:
    ----------
        * _rows: (list[list[XlItem]]) One list of XlItems per (single) row.
            Rows must be in top-to-bottom order. XLItem_List entries are
            accepted and re-flattened.

    Returns:
    --------
        * (list[XlItem | XLItem_List]): Items ready for 'write_xl_item()'.
    """
    rows = [_expand_to_xl_items(row) for row in _rows if row]
    if not rows:
        return []

    passthrough: list[XlItem] = [item for row in rows for item in row if item.has_color]
    plain_rows = [[item for item in row if not item.has_color] for row in rows]

    merged_rows = [merge_xl_item_row(row) if row else [] for row in plain_rows]

    def _fallback() -> list[Union[XlItem, XLItem_List]]:
        return [group for row in merged_rows for group in row] + passthrough

    # -- Every row must be on one sheet, on one row, with one column layout,
    # -- and the rows must be consecutive - otherwise write per-row as before.
    signatures = set()
    row_numbers = []
    for row_groups in merged_rows:
        if not row_groups:
            return _fallback()
        if len({group.sheet_name for group in row_groups}) != 1:
            return _fallback()
        if len({group.xl_row_number for group in row_groups}) != 1:
            return _fallback()
        signatures.add(tuple((group.xl_col_number, _group_width(group)) for group in row_groups))
        row_numbers.append(row_groups[0].xl_row_number)

    is_consecutive = row_numbers == list(range(row_numbers[0], row_numbers[0] + len(row_numbers)))
    if len(signatures) != 1 or not is_consecutive:
        return _fallback()

    # -- Stack each column-group across all the rows into one 2D-valued XlItem.
    # -- Values are already unit-converted here, so the block item carries none.
    sheet_name = merged_rows[0][0].sheet_name
    start_row = row_numbers[0]
    blocks: list[Union[XlItem, XLItem_List]] = []
    for group_i, first_row_group in enumerate(merged_rows[0]):
        values_2d = [_group_row_values(row_groups[group_i]) for row_groups in merged_rows]
        blocks.append(XlItem(sheet_name, f"{first_row_group.xl_col_alpha}{start_row}", values_2d))

    return blocks + passthrough


def merge_xl_item_row(
    _xl_items: list[XlItem],
) -> list[XlItem] | list[XLItem_List] | list[XlItem | XLItem_List]:
    """Merge a list of same-row XlItems into XLItem_List groups for faster batch writing."""

    # -- Make sure all XLItems are on the same sheet
    if len({item.sheet_name for item in _xl_items}) != 1:
        return _xl_items

    # -- Make sure all the XLItems are on the same row
    if len({item.xl_row_number for item in _xl_items}) != 1:
        return _xl_items

    items_sorted = sorted(_xl_items, key=lambda i: i.xl_col_number)

    # -- Set the 'base' for each item in the set, if its xl_range
    # -- column follows the one before it. ie: "A1, B1" will get joined.
    # -- but "A1, C1" will not get joined.
    for i, item in enumerate(items_sorted):
        preceding_item = items_sorted[i - 1]
        if item.xl_col_number == preceding_item.xl_col_number + 1:
            item.xl_range_base = preceding_item.xl_range_base

    # -- Merge the items together
    d: dict[str, XlItem | XLItem_List] = {}
    for item in items_sorted:
        if item.xl_range_base not in d:
            # -- Not in the dict yet, so just
            # -- add the XlItem to the dict
            d[item.xl_range_base] = item
        else:
            existing_item = d[item.xl_range_base]

            if isinstance(existing_item, XLItem_List):
                # -- If the existing item is already a list
                # -- add the new item to it
                existing_item.add_new_xl_item(item)
                d[item.xl_range_base] = existing_item
            elif isinstance(existing_item, XlItem):
                # -- If the existing item is just an item
                # -- first, transform it into a List item
                # -- and then add the new item to the list
                existing_item = XLItem_List([existing_item])
                existing_item.add_new_xl_item(item)
                d[item.xl_range_base] = existing_item
            else:
                msg = f"\n\tError: Unsupported type: '{type(existing_item)}'"
                raise Exception(msg)

    return list(d.values())
