# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP 'Components' worksheet."""

from __future__ import annotations

from dataclasses import dataclass

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model.component_frame import FrameRow
from PHX.PHPP.phpp_model.component_glazing import GlazingRow
from PHX.PHPP.phpp_model.component_vent import VentilatorRow
from PHX.PHPP.sheet_io.io_exceptions import ResolveComponentIDException
from PHX.xl import xl_app
from PHX.xl.xl_data import col_offset, merge_xl_item_rows, xl_chr, xl_ord


@dataclass
class ExistingGlazingTypeData:
    """Stores name, g-value, and U-value for an existing PHPP glazing type."""

    name: str
    g_value: Unit
    u_value: Unit

    @property
    def key(self) -> str:
        return f"{self.name}-{self.g_value}-{self.u_value}"


class Glazings:
    """Reads and writes glazing component data in the PHPP 'Components' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Components):
        self.xl = _xl
        self.shape = _shape
        self._section_header_row: int | None = None
        self._section_first_entry_row: int | None = None
        self._section_last_entry_row: int | None = None
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

    def find_section_last_entry_row(self, _start_row: int | None = None) -> int:
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

    def get_glazing_phpp_id_by_name(self, _name: str, _use_cache: bool = False) -> str | None:
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

    def get_all_glazing_types(self) -> list[ExistingGlazingTypeData]:
        """Return a set of all glazing types in the Glazing input section."""
        glazing_types: dict[str, ExistingGlazingTypeData] = {}
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
    """Reads and writes frame component data in the PHPP 'Components' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Components):
        self.xl = _xl
        self.shape = _shape
        self._section_header_row: int | None = None
        self._section_first_entry_row: int | None = None
        self._section_last_entry_row: int | None = None
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
        """Return the row number of the 'Frames' section header."""
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.frames.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        # -- The data begins at '_row_start', so enumerate from there: the
        # -- caller wants a worksheet row number, not an index into the block.
        for i, val in enumerate(xl_data, start=_row_start):
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

    def find_section_last_entry_row(self, _start_row: int | None = None) -> int:
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

        # -- The data begins at '_start_row', which is NOT the section start
        # -- once the search has recursed into the next 500-row block.
        for i, val in enumerate(xl_data, start=_start_row):
            if not val:
                return i - 1

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
    """Reads and writes ventilator component data in the PHPP 'Components' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Components):
        self.xl = _xl
        self.shape = _shape
        self.cache: dict[str, str] = {}
        self._section_header_row: int | None = None
        self._section_first_entry_row: int | None = None
        self._section_last_entry_row: int | None = None

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

    def find_section_last_entry_row(self, _start_row: int | None = None) -> int:
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

        # -- The data begins at '_start_row', which is NOT the section start
        # -- once the search has recursed into the next 500-row block.
        for i, val in enumerate(xl_data, start=_start_row):
            if not val:
                return i - 1

        return self.find_section_last_entry_row(_row_end)

    def find_section_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        """Return the row number of the 'Ventilators' section header."""
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.ventilators.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        # -- The data begins at '_row_start', so enumerate from there: the
        # -- caller wants a worksheet row number, not an index into the block.
        for i, val in enumerate(xl_data, start=_row_start):
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

    def get_ventilator_phpp_id_by_name(
        self,
        _name: str,
        _row_start: int | None = None,
        _row_end: int | None = None,
        _use_cache: bool = False,
    ) -> str:
        """Return the PHPP ID ("01ud-MyVentilator") of a Ventilator component, by name.

        The search is bounded to the ventilator entry section. PHPP resolves the
        'Addl vent' unit selection against the entry rows only
        ('Components!LQ13:MF914'), so a name matched in a header, label, or note
        row above the section could never resolve in the workbook anyway.

        Arguments:
        ----------
            * _name: (str) The Ventilator display-name to search for.
            * _row_start: (int | None) default=None. Overrides the first row
                searched. Defaults to the first entry row of the section.
            * _row_end: (int | None) default=None. Overrides the last row
                searched. Defaults to the last entry row of the section.
            * _use_cache: (bool) default=False. Re-use a previously resolved ID
                for this name instead of re-reading the worksheet. Safe once the
                ventilator section has been written, and worth it on the
                per-space write path, which asks for the same handful of names
                once per room.

        Returns:
        --------
            * (str): The PHPP ID of the Ventilator component.
        """
        if _use_cache and _name in self.cache:
            return self.cache[_name]

        name_col = str(self.shape.ventilators.inputs.display_name.column)
        row = self.xl.get_row_num_of_value_in_column(
            sheet_name=self.shape.name,
            row_start=_row_start or self.section_first_entry_row,
            row_end=_row_end or self.section_last_entry_row,
            col=name_col,
            find=_name,
        )

        if not row:
            raise Exception(
                f'Error: Cannot find a Ventilator component named: "{_name}" '
                f"in column {name_col} of the '{self.shape.name}' worksheet?"
            )

        phpp_id = self._build_ventilator_phpp_id(f"{col_offset(name_col, -1)}{row}", _name)
        self.cache[_name] = phpp_id
        return phpp_id

    def get_ventilator_phpp_id_by_row_num(self, _row_num: int) -> str:
        """Return the PHPP Ventilator ID ("01ud-MyVentilator", etc..) for the given row number."""
        name_col = str(self.shape.ventilators.inputs.display_name.column)
        id_name = self.xl.get_data(self.shape.name, f"{name_col}{_row_num}")
        id_col = str(self.shape.ventilators.inputs.id.column)
        return self._build_ventilator_phpp_id(f"{id_col}{_row_num}", str(id_name))

    def _build_ventilator_phpp_id(self, _id_address: str, _name: str) -> str:
        """Return "<prefix>-<name>", raising if the ID cell at '_id_address' is empty.

        Formatting an empty ID cell into the string would yield "None-<name>":
        a PHPP-unresolvable selection that raises nothing, shows no error on the
        'Ventilation' worksheet, and silently zeroes the unit's heat recovery.
        """
        prefix = self.xl.get_data(self.shape.name, _id_address)
        if prefix is None or not str(prefix).strip():
            raise ResolveComponentIDException(_name, self.shape.name, _id_address)
        return f"{prefix}-{_name}"


def _cell_has_value(_value: object) -> bool:
    """Return True when an Excel cell value represents a filled user entry."""
    return _value is not None and _value != ""


def _format_stale_rows(_row_numbers: list[int]) -> str:
    """Return a compact row-number label for a stale Components-section warning."""
    if len(_row_numbers) == 1:
        return f"row {_row_numbers[0]}"
    if len(_row_numbers) > 10:
        return f"rows {_row_numbers[0]}-{_row_numbers[-1]} ({len(_row_numbers)})"
    return f"rows {', '.join(str(row) for row in _row_numbers)}"


def _contiguous_row_groups(_row_numbers: list[int]) -> list[tuple[int, int]]:
    """Return inclusive contiguous row spans from sorted worksheet row numbers."""
    if not _row_numbers:
        return []

    groups: list[tuple[int, int]] = []
    start = previous = _row_numbers[0]
    for row in _row_numbers[1:]:
        if row == previous + 1:
            previous = row
            continue
        groups.append((start, previous))
        start = previous = row
    groups.append((start, previous))
    return groups


def _contiguous_column_groups(_columns: list[str]) -> list[tuple[str, str]]:
    """Return inclusive contiguous column spans from Excel column letters."""
    if not _columns:
        return []

    column_numbers = sorted({xl_ord(col) for col in _columns})
    groups: list[tuple[str, str]] = []
    start = previous = column_numbers[0]
    for column in column_numbers[1:]:
        if column == previous + 1:
            previous = column
            continue
        groups.append((xl_chr(start), xl_chr(previous)))
        start = previous = column
    groups.append((xl_chr(start), xl_chr(previous)))
    return groups


def _range_address(_col_start: str, _col_end: str, _row_start: int, _row_end: int) -> str:
    """Return an Excel range address for a column span and row span."""
    start = f"{_col_start}{_row_start}"
    end = f"{_col_end}{_row_end}"
    if start == end:
        return start
    return f"{start}:{end}"


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

    def write_glazings(self, _glazing_rows: list[GlazingRow], *, clear_stale: bool = False) -> None:
        """Write a list of GlazingRow objects to the PHPP "Components" worksheet.

        Warns if filled rows remain below the written block in the glazings section;
        pass clear_stale=True to blank those rows' input columns as well.
        """
        start = self.glazings.section_first_entry_row
        row_items = [
            row.create_xl_items(self.shape.name, _row_num=i) for i, row in enumerate(_glazing_rows, start=start)
        ]
        for item in merge_xl_item_rows(row_items):
            self.xl.write_xl_item(item)
        self._warn_or_clear_stale_rows(
            _section_name="glazings",
            _search_col=str(self.shape.glazings.inputs.description.column),
            _row_start=start + len(_glazing_rows),
            _row_end=self.glazings.section_last_entry_row,
            _clear_stale=clear_stale,
            _clear_columns=[
                str(self.shape.glazings.inputs.description.column),
                str(self.shape.glazings.inputs.g_value.column),
                str(self.shape.glazings.inputs.u_value.column),
            ],
        )

    def write_single_frame(self, _row_num: int, _frame_row: FrameRow) -> str:
        """Write a single FrameRow object to the PHPP "Components" worksheet.

        Return:
        ------
            * (str): The PHPP ID-name of the frame component written to the PHPP.
        """
        for item in _frame_row.create_xl_items(self.shape.name, _row_num=_row_num):
            self.xl.write_xl_item(item)
        return self.frames.get_frame_phpp_id_by_row_num(_row_num)

    def write_frames(self, _frame_row: list[FrameRow], *, clear_stale: bool = False) -> None:
        """Write a list of FrameRow objects to the PHPP "Components" worksheet.

        Warns if filled rows remain below the written block in the frames section;
        pass clear_stale=True to blank those rows' input columns as well.
        """
        start = self.frames.section_first_entry_row
        row_items = [row.create_xl_items(self.shape.name, _row_num=i) for i, row in enumerate(_frame_row, start=start)]
        for item in merge_xl_item_rows(row_items):
            self.xl.write_xl_item(item)
        self._warn_or_clear_stale_rows(
            _section_name="frames",
            _search_col=str(self.shape.frames.inputs.description.column),
            _row_start=start + len(_frame_row),
            _row_end=self.frames.section_last_entry_row,
            _clear_stale=clear_stale,
            _clear_columns=[
                str(self.shape.frames.inputs.description.column),
                str(self.shape.frames.inputs.u_value_left.column),
                str(self.shape.frames.inputs.u_value_right.column),
                str(self.shape.frames.inputs.u_value_bottom.column),
                str(self.shape.frames.inputs.u_value_top.column),
                str(self.shape.frames.inputs.width_left.column),
                str(self.shape.frames.inputs.width_right.column),
                str(self.shape.frames.inputs.width_bottom.column),
                str(self.shape.frames.inputs.width_top.column),
                str(self.shape.frames.inputs.psi_g_left.column),
                str(self.shape.frames.inputs.psi_g_right.column),
                str(self.shape.frames.inputs.psi_g_bottom.column),
                str(self.shape.frames.inputs.psi_g_top.column),
                str(self.shape.frames.inputs.psi_i_left.column),
                str(self.shape.frames.inputs.psi_i_right.column),
                str(self.shape.frames.inputs.psi_i_bottom.column),
                str(self.shape.frames.inputs.psi_i_top.column),
            ],
        )

    def write_single_ventilator(self, _row_num: int, _ventilator_row: VentilatorRow) -> str:
        """Write a single VentilatorRow object to the PHPP "Components" worksheet.

        Return:
        ------
            * (str): The PHPP ID-name of the ventilator component written to the PHPP.
        """
        for item in _ventilator_row.create_xl_items(self.shape.name, _row_num=_row_num):
            self.xl.write_xl_item(item)
        return self.ventilators.get_ventilator_phpp_id_by_row_num(_row_num)

    def write_ventilators(self, _ventilator_row: list[VentilatorRow], *, clear_stale: bool = False) -> None:
        """Write a list of VentilatorRow objects to the PHPP "Components" worksheet.

        Warns if filled rows remain below the written block in the ventilators section;
        pass clear_stale=True to blank those rows' input columns as well.
        """
        start = self.ventilators.section_first_entry_row
        row_items = [row.create_xl_items(self.shape.name, _row_num=i) for i, row in enumerate(_ventilator_row, start)]
        for item in merge_xl_item_rows(row_items):
            self.xl.write_xl_item(item)
        self._warn_or_clear_stale_rows(
            _section_name="ventilators",
            _search_col=str(self.shape.ventilators.inputs.display_name.column),
            _row_start=start + len(_ventilator_row),
            _row_end=self.ventilators.section_last_entry_row,
            _clear_stale=clear_stale,
            _clear_columns=[
                str(self.shape.ventilators.inputs.display_name.column),
                str(self.shape.ventilators.inputs.sensible_heat_recovery.column),
                str(self.shape.ventilators.inputs.latent_heat_recovery.column),
                str(self.shape.ventilators.inputs.electric_efficiency.column),
                str(self.shape.ventilators.inputs.frost_protection_reqd.column),
            ],
        )

    def _get_single_column_data_with_integrity_guard(
        self,
        _col: str,
        _row_start: int,
        _row_end: int,
    ) -> list[object]:
        """Read one column block, falling back per-cell if xlwings drops error cells."""
        data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=_col,
            _row_start=_row_start,
            _row_end=_row_end,
        )
        if not isinstance(data, list):
            data = [data]

        expected_len = _row_end - _row_start + 1
        if len(data) == expected_len:
            return list(data)

        return [self.xl.get_data(self.shape.name, f"{_col}{row}") for row in range(_row_start, _row_end + 1)]

    def _warn_or_clear_stale_rows(
        self,
        _section_name: str,
        _search_col: str,
        _row_start: int,
        _row_end: int,
        _clear_stale: bool,
        _clear_columns: list[str],
    ) -> None:
        """Warn about, and optionally clear, stale trailing Components rows."""
        if _row_start > _row_end:
            return

        data = self._get_single_column_data_with_integrity_guard(_search_col, _row_start, _row_end)
        stale_rows = [row for row, value in enumerate(data, start=_row_start) if _cell_has_value(value)]
        if not stale_rows:
            return

        self.xl.output(
            f"Warning: '{self.shape.name}' worksheet {_section_name} section contains stale "
            f"{_format_stale_rows(stale_rows)}. These are leftover entries from a previous export "
            "that should be cleared or verified."
        )

        if not _clear_stale:
            return

        for row_start, row_end in _contiguous_row_groups(stale_rows):
            for col_start, col_end in _contiguous_column_groups(_clear_columns):
                self.xl.clear_range_data(
                    self.shape.name,
                    _range_address(col_start, col_end, row_start, row_end),
                )
