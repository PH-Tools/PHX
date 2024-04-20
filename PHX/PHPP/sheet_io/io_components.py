# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP 'Components' worksheet."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model.component_frame import FrameRow
from PHX.PHPP.phpp_model.component_glazing import GlazingRow
from PHX.PHPP.phpp_model.component_vent import VentilatorRow
from PHX.xl import xl_app
from PHX.xl.xl_data import col_offset


@dataclass
class ExistingGlazingTypeData:
    name: str
    g_value: Unit
    u_value: Unit

    @property
    def key(self) -> str:
        return f"{self.name}-{self.g_value}-{self.u_value}"


class Glazings:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Components):
        self.xl = _xl
        self.shape = _shape
        self._section_header_row: Optional[int] = None
        self._section_first_entry_row: Optional[int] = None
        self._section_last_entry_row: Optional[int] = None
        self.cache = {}

    @property
    def section_header_row(self) -> int:
        """Return the row number of the Glazings section header."""
        if not self._section_header_row:
            self._section_header_row = self.find_section_header_row()
        return self._section_header_row

    @property
    def section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the Glazing input section."""
        if not self._section_first_entry_row:
            self._section_first_entry_row = self.find_section_first_entry_row()
        return self._section_first_entry_row

    @property
    def section_last_entry_row(self) -> int:
        """Return the row number of the very last user-input entry row in the Glazing input section."""
        if not self._section_last_entry_row:
            self._section_last_entry_row = self.find_section_last_entry_row()
        return self._section_last_entry_row

    def find_section_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        """Return the row number of the Glazings section header."""
        # -- Note: this is done differently for glazing than everywhere else because
        # -- in PHPP10, there is a potential Excel formula error in cell IH9 where it
        # -- references the climate data. If the climate is NOT already set, this will
        # -- Error. Then because of a bug in MacOS AppleScript:
        # -- (https://github.com/xlwings/xlwings/issues/1924) XL-Wings will silently pass
        # -- by this cell, which then throws off the row count. Therefor to avoid,
        # -- just hard-coding the start row in this case.
        return self.shape.glazings.entry_start_row

    def find_section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the Glazing input section."""
        # -- Note: this is done differently for glazing than everywhere else because
        # -- in PHPP10, there is a potential Excel formula error in cell IH9 where it
        # -- references the climate data. If the climate is NOT already set, this will
        # -- Error. Then because of a bug in MacOS AppleScript:
        # -- (https://github.com/xlwings/xlwings/issues/1924) XL-Wings will silently pass
        # -- by this cell, which then throws off the row count. Therefor to avoid,
        # -- just hard-coding the start row in this case.

        return self.shape.glazings.entry_start_row

    def find_section_last_entry_row(self, _start_row: Optional[int] = None) -> int:
        """Return the last row of the glazing input section."""
        if not _start_row:
            _start_row = self.section_first_entry_row
        elif _start_row > 10_000:
            raise Exception(
                f"Error: Cannot find the last row in the '{self.shape.name}'"
                f"sheet, column {self.shape.glazings.entry_column}?"
            )

        _row_end = _start_row + 500
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.glazings.entry_column,
            _row_start=_start_row,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=_start_row):
            if not val:
                return i - 1
        else:
            return self.find_section_last_entry_row(_row_end)

    def find_first_empty_row(self) -> int:
        """Return the first empty row in the glazing input section."""
        search_col = str(self.shape.glazings.inputs.description.column)
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=search_col,
            _row_start=self.section_first_entry_row,
            _row_end=self.section_last_entry_row,
        )

        for i, val in enumerate(xl_data, start=self.section_first_entry_row):
            if not val:
                return i

        raise Exception(
            f"Error: Cannot find the first empty row in the '{self.shape.name}' sheet, column {search_col}?"
        )

    def get_glazing_phpp_id_by_name(self, _name: str, _use_cache: bool = False) -> Optional[str]:
        """Return the PHPP Glazing ID for the given name."""
        if _use_cache:
            try:
                return self.cache[_name]
            except KeyError:
                pass

        row = self.xl.get_row_num_of_value_in_column(
            sheet_name=self.shape.name,
            row_start=1,
            row_end=500,
            col=str(self.shape.glazings.inputs.description.column),
            find=_name,
        )

        if not row:
            return

        prefix = self.xl.get_data(
            self.shape.name,
            f"{col_offset(str(self.shape.glazings.inputs.description.column), -1)}{row}",
        )
        print(f"Getting PHPP Glazing PHPP-id for {_name}")
        name_with_id = f"{prefix}-{_name}"

        self.cache[_name] = name_with_id

        return name_with_id

    def get_glazing_phpp_id_by_row_num(self, _row_num: int) -> str:
        """Return the PHPP Glazing ID ("01ud-MyGlass", etc..) for the given row number."""
        id_col = str(self.shape.glazings.inputs.id.column)
        id_num = self.xl.get_data(self.shape.name, f"{id_col}{_row_num}")
        name_col = str(self.shape.glazings.inputs.description.column)
        id_name = self.xl.get_data(self.shape.name, f"{name_col}{_row_num}")
        return f"{id_num}-{id_name}"

    def get_all_glazing_types(self) -> List[ExistingGlazingTypeData]:
        """Return a set of all glazing types in the Glazing input section."""
        glazing_types: Dict[str, ExistingGlazingTypeData] = {}
        unit_type = str(self.shape.glazings.inputs.u_value.unit)
        start = f"{self.shape.glazings.inputs.description.column}{self.section_first_entry_row}"
        end = f"{self.shape.glazings.inputs.u_value.column}{self.section_last_entry_row}"

        data = self.xl.get_data(self.shape.name, f"{start}:{end}")

        if not data:
            return []

        for row in data:
            if "None" in row or None in row:
                continue

            exiting_glazing_type = ExistingGlazingTypeData(
                str(row[0]),
                Unit(row[1], "-"),
                Unit(row[2], unit_type),
            )
            glazing_types[exiting_glazing_type.key] = exiting_glazing_type

        return [glazing_types[k] for k in sorted(glazing_types.keys())]


class Frames:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Components):
        self.xl = _xl
        self.shape = _shape
        self._section_header_row: Optional[int] = None
        self._section_first_entry_row: Optional[int] = None
        self._section_last_entry_row: Optional[int] = None
        self.cache = {}

    @property
    def section_header_row(self) -> int:
        """Return the row number of the 'Frames' section header."""
        if not self._section_header_row:
            self._section_header_row = self.find_section_header_row()
        return self._section_header_row

    @property
    def section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the Frames input section."""
        if not self._section_first_entry_row:
            self._section_first_entry_row = self.find_section_first_entry_row()
        return self._section_first_entry_row

    @property
    def section_last_entry_row(self) -> int:
        """Return the row number of the very last user-input entry row in the Frames input section."""
        if not self._section_last_entry_row:
            self._section_last_entry_row = self.find_section_last_entry_row()
        return self._section_last_entry_row

    def find_section_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.frames.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )
        """Return the row number of the 'Frames' section header."""

        for i, val in enumerate(xl_data):
            if self.shape.frames.locator_string_header == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.frames.locator_string_header}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.frames.locator_col_header}?"
        )

    def find_section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the Frames input section."""
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.frames.locator_col_entry,
            _row_start=self.section_header_row,
            _row_end=self.section_header_row + 25,
        )

        for i, val in enumerate(xl_data, start=self.section_header_row):
            if val == self.shape.frames.locator_string_entry:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.frames.locator_string_entry}'"
            f"entry start on the 'Components' sheet, column {self.shape.frames.locator_col_entry}?"
        )

    def find_section_last_entry_row(self, _start_row: Optional[int] = None) -> int:
        """Return the last row of the Frames input section."""
        if not _start_row:
            _start_row = self.section_first_entry_row
        elif _start_row > 10_000:
            raise Exception(
                f"Error: Cannot find the last row in the '{self.shape.name}' sheet, column {self.shape.frames.locator_col_entry}?"
            )

        _row_end = _start_row + 500
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.frames.locator_col_entry,
            _row_start=_start_row,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=self.section_first_entry_row):
            if not val:
                return i - 1
        else:
            return self.find_section_last_entry_row(_row_end)

    def find_first_empty_row(self) -> int:
        """Return the first empty row in the frames input section."""
        search_col = str(self.shape.frames.inputs.description.column)
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=search_col,
            _row_start=self.section_first_entry_row,
            _row_end=self.section_last_entry_row,
        )

        for i, val in enumerate(xl_data, start=self.section_first_entry_row):
            if not val:
                return i

        raise Exception(
            f"Error: Cannot find the first empty row in the '{self.shape.name}' sheet, column {search_col}?"
        )

    def get_frame_phpp_id_by_name(
        self,
        _name: str,
        _row_start: int = 1,
        _row_end: int = 500,
        _use_cache: bool = False,
    ) -> str:
        """Return the PHPP ID of a Frame component by name."""
        # -- Try and use the Cached value first
        if _use_cache:
            try:
                return self.cache[_name]
            except KeyError:
                pass

        row = self.xl.get_row_num_of_value_in_column(
            sheet_name=self.shape.name,
            row_start=_row_start,
            row_end=_row_end,
            col=str(self.shape.frames.inputs.description.column),
            find=_name,
        )

        if not row:
            msg = (
                f'Error: Cannot find a Frame component named: "{_name}" in'
                f"column {self.shape.frames.inputs.description.column}?"
            )
            raise Exception(msg)
        prefix = self.xl.get_data(
            self.shape.name,
            f"{col_offset(str(self.shape.frames.inputs.description.column), -1)}{row}",
        )
        print(f"Getting PHPP Frame id for {_name}")
        name_with_id = f"{prefix}-{_name}"
        self.cache[_name] = name_with_id

        return name_with_id

    def get_frame_phpp_id_by_row_num(self, _row_num: int) -> str:
        """Return the PHPP Frame ID ("01ud-MyFrame", etc..) for the given row number."""
        id_col = str(self.shape.frames.inputs.id.column)
        id_num = self.xl.get_data(self.shape.name, f"{id_col}{_row_num}")
        name_col = str(self.shape.frames.inputs.description.column)
        id_name = self.xl.get_data(self.shape.name, f"{name_col}{_row_num}")
        return f"{id_num}-{id_name}"


class Ventilators:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Components):
        self.xl = _xl
        self.shape = _shape
        self._section_header_row: Optional[int] = None
        self._section_first_entry_row: Optional[int] = None
        self._section_last_entry_row: Optional[int] = None

    @property
    def section_header_row(self) -> int:
        """Return the row number of the 'Ventilators' section header."""
        if not self._section_header_row:
            self._section_header_row = self.find_section_header_row()
        return self._section_header_row

    @property
    def section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the Ventilators input section."""
        if not self._section_first_entry_row:
            self._section_first_entry_row = self.find_section_first_entry_row()
        return self._section_first_entry_row

    @property
    def section_last_entry_row(self) -> int:
        """Return the row number of the very last user-input entry row in the Ventilators input section."""
        if not self._section_last_entry_row:
            self._section_last_entry_row = self.find_section_last_entry_row()
        return self._section_last_entry_row

    def find_section_last_entry_row(self, _start_row: Optional[int] = None) -> int:
        """Return the last row of the Ventilators input section."""
        if not _start_row:
            _start_row = self.section_first_entry_row
        elif _start_row > 10_000:
            raise Exception(
                f"Error: Cannot find the last row in the '{self.shape.name}' sheet, column {self.shape.ventilators.locator_col_entry}?"
            )

        _row_end = _start_row + 500
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.ventilators.locator_col_entry,
            _row_start=_start_row,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=self.section_first_entry_row):
            if not val:
                return i - 1
        else:
            return self.find_section_last_entry_row(_row_end)

    def find_section_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        """Return the row number of the 'Ventilators' section header."""
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.ventilators.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data):
            if self.shape.ventilators.locator_string_header == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.ventilators.locator_string_header}' header on the "
            f"'{self.shape.name}' sheet, column {self.shape.ventilators.locator_col_header}?"
        )

    def find_section_first_entry_row(self) -> int:
        """Return the first row of the Ventilators input section."""
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.ventilators.locator_col_entry,
            _row_start=self.section_header_row,
            _row_end=self.section_header_row + 25,
        )

        for i, val in enumerate(xl_data, start=self.section_header_row):
            if val == self.shape.ventilators.locator_string_entry:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.ventilators.locator_string_entry}' entry start on "
            f"the '{self.shape.name}' sheet, column {self.shape.ventilators.locator_col_entry}?"
        )

    def find_first_empty_row(self) -> int:
        """Return the first empty row in the Ventilators input section."""
        search_col = str(self.shape.ventilators.inputs.display_name.column)
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=search_col,
            _row_start=self.section_first_entry_row,
            _row_end=self.section_last_entry_row,
        )

        for i, val in enumerate(xl_data, start=self.section_first_entry_row):
            if not val:
                return i

        raise Exception(
            f"Error: Cannot find the first empty row in the '{self.shape.name}' sheet, column {search_col}?"
        )

    def get_ventilator_phpp_id_by_name(self, _name: str, _row_start: int = 1, _row_end: int = 500) -> str:
        """Return the PHPP ID of a Ventilator component by name."""
        row = self.xl.get_row_num_of_value_in_column(
            sheet_name=self.shape.name,
            row_start=_row_start,
            row_end=_row_end,
            col=str(self.shape.ventilators.inputs.display_name.column),
            find=_name,
        )

        if not row:
            raise Exception(
                f'Error: Cannot find a Ventilator component named: "{_name}"]'
                f"in column {self.shape.ventilators.inputs.display_name.column}?"
            )

        prefix = self.xl.get_data(
            self.shape.name,
            f"{col_offset(str(self.shape.ventilators.inputs.display_name.column), -1)}{row}",
        )
        return f"{prefix}-{_name}"

    def get_ventilator_phpp_id_by_row_num(self, _row_num: int) -> str:
        """Return the PHPP Ventilator ID ("01ud-MyVentilator", etc..) for the given row number."""
        id_col = str(self.shape.ventilators.inputs.id.column)
        id_num = self.xl.get_data(self.shape.name, f"{id_col}{_row_num}")
        name_col = str(self.shape.ventilators.inputs.display_name.column)
        id_name = self.xl.get_data(self.shape.name, f"{name_col}{_row_num}")
        return f"{id_num}-{id_name}"


class Components:
    """IO Controller for PHPP "Components" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, shape: shape_model.Components):
        self.xl = _xl
        self.shape = shape
        self.glazings = Glazings(self.xl, self.shape)
        self.frames = Frames(self.xl, self.shape)
        self.ventilators = Ventilators(self.xl, self.shape)

    @property
    def first_empty_glazing_row_num(self) -> int:
        """Return the row number of the first empty row in the Glazings section."""
        return self.glazings.find_first_empty_row()

    @property
    def first_empty_frame_row_num(self) -> int:
        """Return the row number of the first empty row in the Frames section."""
        return self.frames.find_first_empty_row()

    def write_single_glazing(self, _row_num: int, _glazing_row: GlazingRow) -> str:
        """Write a single GlazingRow object to the PHPP "Components" worksheet.

        Return:
        ------
            * (str): The PHPP ID-name of the glazing component written to the PHPP.
        """

        for item in _glazing_row.create_xl_items(self.shape.name, _row_num=_row_num):
            self.xl.write_xl_item(item)
        return self.glazings.get_glazing_phpp_id_by_row_num(_row_num)

    def write_glazings(self, _glazing_rows: List[GlazingRow]) -> None:
        """Write a list of GlazingRow objects to the PHPP "Components" worksheet."""
        for i, glazing_row in enumerate(_glazing_rows, start=self.glazings.section_first_entry_row):
            self.write_single_glazing(i, glazing_row)

    def write_single_frame(self, _row_num: int, _frame_row: FrameRow) -> str:
        """Write a single FrameRow object to the PHPP "Components" worksheet.

        Return:
        ------
            * (str): The PHPP ID-name of the frame component written to the PHPP.
        """
        for item in _frame_row.create_xl_items(self.shape.name, _row_num=_row_num):
            self.xl.write_xl_item(item)
        return self.frames.get_frame_phpp_id_by_row_num(_row_num)

    def write_frames(self, _frame_row: List[FrameRow]) -> None:
        """Write a list of FrameRow objects to the PHPP "Components" worksheet."""
        start = self.frames.section_first_entry_row
        for i, frame_row in enumerate(_frame_row, start=start):
            self.write_single_frame(i, frame_row)

    def write_single_ventilator(self, _row_num: int, _ventilator_row: VentilatorRow) -> str:
        """Write a single VentilatorRow object to the PHPP "Components" worksheet.

        Return:
        ------
            * (str): The PHPP ID-name of the ventilator component written to the PHPP.
        """
        for item in _ventilator_row.create_xl_items(self.shape.name, _row_num=_row_num):
            self.xl.write_xl_item(item)
        return self.ventilators.get_ventilator_phpp_id_by_row_num(_row_num)

    def write_ventilators(self, _ventilator_row: List[VentilatorRow]) -> None:
        """Write a list of VentilatorRow objects to the PHPP "Components" worksheet."""
        start = self.ventilators.section_first_entry_row
        for i, ventilator_row in enumerate(_ventilator_row, start):
            self.write_single_ventilator(i, ventilator_row)
