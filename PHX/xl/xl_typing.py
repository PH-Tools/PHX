# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""XL-App Protocol Classes."""

import pathlib
from typing import Optional, Dict, Tuple, Any, Callable

from PHX.xl import xl_data


class xl_Range_Font:
    def __init__(self):
        self.color: Optional[Tuple[int, ...]]


class xl_RangeColumns_Protocol:
    def __init__(self):
        ...

    def __len__(self) -> int:
        ...


class xl_CellRange_Protocol:
    def __init__(self):
        self.address: str


class xl_Range_Protocol:
    def __init__(self):
        self.value: xl_data.xl_range_value
        self.color: Optional[Tuple[int, ...]]
        self.font: xl_Range_Font = xl_Range_Font()
        self.columns: xl_RangeColumns_Protocol = xl_RangeColumns_Protocol()
        self.last_cell: xl_CellRange_Protocol
        self.row: int
        self.column: int
        self.rows: str

    def end(self, *args, **kwargs) -> "xl_Range_Protocol":
        return xl_Range_Protocol()

    def options(self, *args, **kwargs) -> "xl_Range_Protocol":
        return self

    def offset(self, row_offset: int = 0, column_offset: int = 0) -> "xl_Range_Protocol":
        return xl_Range_Protocol()


class xl_API_Protocol:
    def __init__(self, sheet):
        self.sheet: "xl_Sheet_Protocol" = sheet
        self.rows: Dict
        self.outline_object: Any

    def Rows(*args, **kwargs) -> Any:
        ...

    def unprotect(self) -> None:
        self.sheet.protected = False

    def Unprotect(self) -> None:
        self.sheet.protected = False


class xl_Sheet_Protocol:
    def __init__(self, name="Sheet1"):
        self.api = xl_API_Protocol(self)
        self.protected = True
        self._ranges: Dict[str, xl_Range_Protocol] = {}
        self.name: str = name

    def range(self, cell1: str, cell2: Optional[str] = None) -> xl_Range_Protocol:
        if cell1 in self._ranges.keys():
            return self._ranges[cell1]
        else:
            rng_obj = xl_Range_Protocol()
            self._ranges[cell1] = rng_obj
            return rng_obj

    def clear_contents(self) -> None:
        ...

    def clear_formats(self) -> None:
        ...

    def clear(self) -> None:
        ...

    def activate(self) -> None:
        ...

    def autofit(self, *args, **kwargs) -> None:
        ...

    def delete(self) -> None:
        ...


class xl_Sheets_Protocol:
    def __init__(self):
        self.storage: Dict[str, xl_Sheet_Protocol] = {}

    def __getitem__(self, _key) -> xl_Sheet_Protocol:
        return self.storage[_key]

    def add(
        self,
        name: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> xl_Sheet_Protocol:
        if name in self.storage.keys():
            return self.storage[str(name)]
        else:
            new_sheet = xl_Sheet_Protocol(name=str(name))
            self.storage[str(name)] = new_sheet
            return new_sheet

    def __iter__(self):
        for _ in self.storage.values():
            yield _

    def __contains__(self, key):
        return key in self.storage

    def __len__(self):
        return len(self.storage)


class xl_Book_Protocol:
    def __init__(self):
        self.name: str = ""
        self.fullname: str = ""
        self.app = xl_app_Protocol()
        self.sheets = xl_Sheets_Protocol()


class xl_Books_Protocol:
    def __init__(self):
        self.active = xl_Book_Protocol()
        self.count: int = 1

    def add(self) -> xl_Book_Protocol:
        ...

    def open(self, _p: pathlib.Path) -> xl_Book_Protocol:
        ...


class xl_app_Protocol:
    def __init__(self):
        self.screen_updating: bool = True
        self.display_alerts: bool = True
        self.calculation: str = "automatic"
        self.visible: bool = False

    def calculate(self) -> None:
        return None


class xl_apps_Protocol:
    def __init__(self):
        self.count: int = 1

    def add(self) -> xl_app_Protocol:
        ...


class xl_Framework_Protocol:
    def __init__(self):
        self.books: xl_Books_Protocol  # Mac
        self.Books: xl_Books_Protocol  # PC
        self.apps: xl_apps_Protocol  # Mac
        self.Apps: xl_apps_Protocol  # PC

    def Range(self, *args, **kwargs) -> xl_Range_Protocol:
        return xl_Range_Protocol()
