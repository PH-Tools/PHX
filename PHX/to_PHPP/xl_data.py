# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Basic datatypes / structures relevant for Excel"""

from typing import Union, Optional
import string

from ph_units.converter import convert

xl_writable = Optional[Union[str, float, int, list, tuple]]
xl_range_value = Optional[Union[str, float, int]]


class XlItem:
    __slots__ = ('sheet_name', 'xl_range', '_write_value', 'input_unit', 'target_unit')

    def __init__(self,
                sheet_name: str, 
                xl_range: str, 
                write_value: xl_writable, 
                input_unit: Optional[str]=None, 
                target_unit: Optional[str]=None
    ):
        self.sheet_name = sheet_name
        self.xl_range = xl_range
        self._write_value = write_value
        self.input_unit = input_unit
        self.target_unit = target_unit

    @property
    def write_value(self):
        # -- Try to convert the unit (SI/IP)
        
        if not self.input_unit or not self.target_unit:
            return self._write_value

        if isinstance(self._write_value, (tuple, list)):
            return [convert(v, self.input_unit, self.target_unit) for v in self._write_value]
        else:
            return convert(self._write_value, self.input_unit, self.target_unit)

    def __str__(self):
        return f'{self.__class__.__name__}({self.sheet_name}, {self.xl_range}, {self.write_value})'

    def __repr__(self):
        return f'{self.__class__.__name__}(sheet_name={self.sheet_name}, range={self.xl_range}, value={self.write_value})'


def xl_ord(_col: str) -> int:
    """ord() which supports excel columns beyond Z (AA, AB, ...)"""
    num = 0
    for c in _col.upper():
        if c in string.ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord('A')) + 1
    return num + 64


def xl_chr(_i: int) -> str:
    """chr() which supports excel columns beyond Z (AA, AB, ...)"""
    letters = ''
    num = _i - 64
    while num:
        mod = (num - 1) % 26
        letters += chr(mod + 65)
        num = (num - 1) // 26
    return ''.join(reversed(letters))


def col_offset(_col: str, _offset: int) -> str:
    """Return a column character, offset from the base by a specified amount."""
    base = xl_ord(_col)
    new = base + _offset
    return xl_chr(new)
