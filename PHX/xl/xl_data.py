# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Basic datatypes and data-structures relevant for Excel read/write."""

import string
from typing import Dict, List, Optional, Tuple, Union

from ph_units import converter

xl_writable = Optional[Union[str, float, int, List, Tuple]]
xl_range_single_value = Union[str, float, int, None]
xl_range_list1D_value = Union[List[str], List[float], List[int], List[None]]
xl_range_list2D_value = Union[List[List[str]], List[List[float]], List[List[int]], List[List[None]]]
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
        input_unit: Optional[str] = None,
        target_unit: Optional[str] = None,
        range_color: Optional[Tuple[int, int, int]] = None,
        font_color: Optional[Tuple[int, int, int]] = None,
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
    def xl_row_number(self) -> int:
        return int([_ for _ in self.xl_range if _.isdigit()][0])

    @property
    def xl_col_number(self) -> int:
        return xl_ord(self.xl_range)

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
        if self.font_color and self.range_color:
            return True
        return False

    @property
    def value_is_iterable(self) -> bool:
        """Return True is the item's value is a List or Tuple"""
        return isinstance(self.write_value, (List, Tuple))

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

    def __init__(self, _items: List[XlItem]):
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
    def write_value(self) -> List[xl_writable]:
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
        for item in self.items:
            if item.font_color or item.range_color:
                return True
        return False

    @property
    def value_is_iterable(self) -> bool:
        """Return True."""
        return True

    def __len__(self) -> int:
        return len(self._items)


def merge_xl_item_row(
    _xl_items: List[XlItem],
) -> Union[List[XlItem], List[XLItem_List], List[Union[XlItem, XLItem_List]]]:
    """Merge a List of XLItems into rows, where possible."""

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
    d: Dict[str, Union[XlItem, XLItem_List]] = {}
    for item in items_sorted:
        if item.xl_range_base not in d.keys():
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
