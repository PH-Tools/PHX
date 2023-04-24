# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP "Electricity non-res" worksheet."""

from __future__ import annotations
from typing import List, Optional, Generator, Tuple

from PHX.xl import xl_app, xl_data
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model.elec_non_res import ExistingLightingRow


class Lighting:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.ElecNonRes) -> None:
        self.xl = _xl
        self.shape = _shape
        self._section_header_row: Optional[int] = None
        self._section_first_entry_row: Optional[int] = None
        self._section_last_entry_row: Optional[int] = None

    @property
    def section_header_row(self) -> int:
        """Return the row number of the 'Lighting' section header."""
        if not self._section_header_row:
            self._section_header_row = self.find_section_header_row()
        return self._section_header_row

    @property
    def section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the 'Lighting' section."""
        if not self._section_first_entry_row:
            self._section_first_entry_row = self.find_section_first_entry_row()
        return self._section_first_entry_row

    @property
    def section_last_entry_row(self) -> int:
        """Return the row number of the last user-input entry row in the 'Lighting' section."""
        if not self._section_last_entry_row:
            self._section_last_entry_row = self.find_section_last_entry_row()
        return self._section_last_entry_row

    def find_section_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        """Return the row number of the 'Lighting input' section header."""

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.lighting_rows.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=1):
            if val == self.shape.lighting_rows.locator_string_header:
                return i

        raise Exception(
            f'\n\tError: Not able to find the "Lighting input" input section of '
            f'the "{self.shape.name}" worksheet? Please be sure the section begins '
            f'with the "{self.shape.lighting_rows.locator_string_header}" flag in '
            f"column {self.shape.lighting_rows.locator_col_header}."
        )

    def find_section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the 'Lighting input' section."""

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.lighting_rows.locator_col_entry,
            _row_start=self.section_header_row,
            _row_end=self.section_header_row + 25,
        )

        for i, val in enumerate(xl_data, start=self.section_header_row):
            if val == self.shape.lighting_rows.locator_string_entry:
                return i + 1

        raise Exception(
            f'\n\tError: Not able to find the first surface entry row in the "Lighting input" section?'
        )

    def find_section_last_entry_row(self, _start_row: Optional[int] = None) -> int:
        """Return the row number of the last user-input entry row in the 'Lighting input' section."""

        if not _start_row:
            _start_row = self.section_first_entry_row
        elif _start_row > 10_000:
            raise Exception(
                f'\n\tError: Not able to find the last surface entry row in the "Lighting input" section?'
            )

        _row_end = _start_row + 500
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.lighting_rows.locator_col_entry,
            _row_start=_start_row,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=self.section_first_entry_row):
            if val == self.shape.lighting_rows.locator_string_exit:
                return i - 2
        else:
            return self.find_section_last_entry_row(_row_end)

    def get_lighting_row_data(self, _row_num: int) -> ExistingLightingRow:
        """Return the lighting row object for the given row number."""
        return ExistingLightingRow(
            self.shape,
            self.xl.get_single_row_data(self.shape.name, _row_num),
        )

    @property
    def all_lighting_row_data(
        self,
    ) -> Generator[Tuple[int, ExistingLightingRow], None, None]:
        """Return a generator of all the row_nums and lighting rows in the Lighting worksheet.

        Yields:
        -------
            * Tuple[int, ExistingLightingRow]: The row-number and the surface row object.
        """

        for i in range(self.section_first_entry_row, self.section_last_entry_row):
            exg_srfc_row = self.get_lighting_row_data(i)
            yield i, exg_srfc_row

    @property
    def used_lighting_row_numbers(self) -> Generator[int, None, None]:
        """Return a generator of all the row_nums that have data in the Lighting section."""
        data = self.xl.get_single_column_data(
            self.shape.name,
            str(self.shape.lighting_rows.inputs.room_zone_name),
            self.section_first_entry_row,
            self.section_last_entry_row,
        )
        return (
            i
            for i, val in enumerate(data, start=self.section_first_entry_row)
            if val is not None
        )

    def set_lighting_power_density(self, _row_num: int, _power_density: float):
        """Set the lighting power density for the given row number."""
        _range = f"{self.shape.lighting_rows.inputs.installed_power}{_row_num}"
        self.xl.write_xl_item(xl_data.XlItem(self.shape.name, _range, _power_density))


class ElecNonRes:
    """IO Controller for the PHPP "Electricity non-res" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.ElecNonRes):
        self.xl = _xl
        self.shape = _shape
        self.lighting = Lighting(self.xl, self.shape)
