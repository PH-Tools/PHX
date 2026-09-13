# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP "Additional Vent" worksheet."""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import vent_ducts, vent_space, vent_units
from PHX.xl import xl_app, xl_data
from PHX.xl.xl_data import col_offset, xl_writable

# -- A user can extend any entry block with inserted rows, so section scans read in growing
# -- blocks until they find their end marker, and give up only at this row.
ROW_SEARCH_LIMIT = 10_000


def _is_empty(_value: object) -> bool:
    return _value is None


def _find_row_in_column(
    _xl: xl_app.XLConnection,
    _sheet_name: str,
    _col: str,
    _row_start: int,
    _first_block_rows: int,
    _matches: Callable[[object], bool],
) -> int | None:
    """Return the first row at or below '_row_start' whose value matches, or None before ROW_SEARCH_LIMIT.

    The first read spans '_first_block_rows'; later reads continue in 500-row blocks.
    """
    block_start, block_rows = _row_start, _first_block_rows
    while block_start <= ROW_SEARCH_LIMIT:
        block_end = min(block_start + block_rows, ROW_SEARCH_LIMIT)
        values = _xl.get_single_column_data(
            _sheet_name=_sheet_name,
            _col=_col,
            _row_start=block_start,
            _row_end=block_end,
        )
        for row, value in enumerate(values, start=block_start):
            if _matches(value):
                return row
        block_start, block_rows = block_end + 1, 500
    return None


class Spaces:
    """Reads and writes ventilation space data in the PHPP 'Additional Vent' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.AddnlVent) -> None:
        self.xl = _xl
        self.shape = _shape
        self.section_header_row: int | None = None
        self.section_first_entry_row: int | None = None
        self.section_last_entry_row: int | None = None

    def find_section_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        """Return the row number of the 'Rooms' section header."""

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.rooms.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        # -- The data begins at '_row_start', so enumerate from there: the
        # -- caller wants a worksheet row number, not an index into the block.
        for i, val in enumerate(xl_data, start=_row_start):
            if self.shape.rooms.locator_string_header in str(val):
                return i

        raise Exception(
            f'\nError: Not able to find the "Rooms" input section of '
            f'the "{self.shape.name}" worksheet? Please be sure the section '
            f'begins with the "{self.shape.rooms.locator_string_header}" '
            f'flag in column "{self.shape.rooms.locator_col_header}"?'
        )

    def find_section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the 'Rooms' section."""

        if not self.section_header_row:
            self.section_header_row = self.find_section_header_row()

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.rooms.locator_col_entry,
            _row_start=self.section_header_row,
            _row_end=self.section_header_row + 25,
        )

        for i, val in enumerate(xl_data, start=self.section_header_row):
            try:
                val = str(int(val))  # Value comes in as  "1.0" from Excel? # type: ignore
            except:
                continue

            if val == self.shape.rooms.locator_string_entry:
                return i

        raise Exception(
            f"\n\tError: Not able to find the first room entry row in the"
            f'"Rooms" section of the "{self.shape.name}" worksheet?'
        )

    def find_section_shape(self) -> None:
        self.section_header_row = self.find_section_header_row()
        self.section_first_entry_row = self.find_section_first_entry_row()
        self.section_last_entry_row = self.find_section_last_entry_row()

    def find_section_last_entry_row(self, _read_length: int = 50) -> int:
        """Return the row number of the last user-input entry row in the 'Rooms' section."""
        if not self.section_first_entry_row:
            self.section_first_entry_row = self.find_section_first_entry_row()

        # -- The Rooms block ends at the first empty cell in the locator column
        first_empty_row = _find_row_in_column(
            self.xl,
            self.shape.name,
            self.shape.rooms.locator_col_header,
            self.section_first_entry_row,
            _read_length,
            _is_empty,
        )
        if first_empty_row is None:
            raise Exception(
                f'Error: Unable to locate the end of the "Rooms" section of the "{self.shape.name}" worksheet in '
                f"{self.shape.rooms.locator_col_header}{self.section_first_entry_row}:"
                f"{self.shape.rooms.locator_col_header}{ROW_SEARCH_LIMIT}?"
            )
        return first_empty_row - 1


@dataclass
class VentilatorDeviceUsage:
    """Convenience class for organizing and cleaning the data."""

    display_name: str = "-"
    vent_unit_type_name: str = "-"
    quantity: int = 0
    hr_efficiency: Unit = field(default_factory=Unit)
    mr_efficiency: Unit = field(default_factory=Unit)

    @classmethod
    def from_phpp_data_row(cls, row: Sequence) -> VentilatorDeviceUsage:
        """Create a new instance from a row of data from PHPP."""
        obj = cls()

        if not row:
            return obj

        if row[1] not in ["-", "", "None", None]:
            # split off the "01ud-" prefix...
            obj.display_name = str(row[1]).strip()

        if row[2] not in ["-", "", "None", None]:
            # split off the "01ud-" prefix...
            obj.vent_unit_type_name = str(row[2]).split("-", 1)[-1].strip()

        if row[0] not in ["-", "", "None", None]:
            # split off the "01ud-" prefix...
            obj.quantity = int(float(row[0]))

        if row[14] not in ["-", "", "None", None, "N/A"]:
            obj.hr_efficiency = Unit(row[14], "-")

        if row[16] not in ["-", "", "None", None, "N/A"]:
            obj.mr_efficiency = Unit(row[16], "-")

        return obj


class VentUnits:
    """Reads and writes ventilation unit data in the PHPP 'Additional Vent' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.AddnlVent):
        self.xl = _xl
        self.shape = _shape
        self._section_header_row: int | None = None
        self._section_first_entry_row: int | None = None
        self._section_last_entry_row: int | None = None

    @property
    def section_header_row(self) -> int:
        """Return the row number of the 'Area input' section header."""
        if not self._section_header_row:
            self._section_header_row = self.find_section_header_row()
        return self._section_header_row

    @property
    def section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the 'Area input' section."""
        if not self._section_first_entry_row:
            self._section_first_entry_row = self.find_section_first_entry_row()
        return self._section_first_entry_row

    @property
    def section_last_entry_row(self) -> int:
        """Return the row number of the last user-input entry row in the 'Area input' section."""
        if not self._section_last_entry_row:
            self._section_last_entry_row = self.find_section_last_entry_row()
        return self._section_last_entry_row

    def find_section_header_row(self, _row_start: int = 50, _row_end: int = 200) -> int:
        """Return the row number of the 'Vent-Units' section header."""
        RECURSION_LIMIT = 10_000

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.units.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=_row_start):
            if self.shape.units.locator_string_header in str(val):
                return i

        # -- If the section is not found, try again with a larger read-block
        if _row_end < RECURSION_LIMIT:
            return self.find_section_header_row(_row_start=_row_end, _row_end=_row_end + 200)
        # -- If the section is still not found, raise an exception
        raise Exception(
            f'\nError: Not able to find the "Ventilation-Units" input section '
            f'of the "{self.shape.name}" worksheet? Please be sure the section '
            f'begins with the "{self.shape.units.locator_string_header}" '
            f'flag in column "{self.shape.units.locator_col_header}?" '
        )

    def find_section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the 'Vent Unit' section."""

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.units.locator_col_entry,
            _row_start=self.section_header_row,
            _row_end=self.section_header_row + 25,
        )

        for i, val in enumerate(xl_data, start=self.section_header_row):
            try:
                val = str(int(val))  # Value comes in as  "1.0" from Excel? # type: ignore
            except:
                continue

            if val == self.shape.units.locator_string_entry:
                return i

        raise Exception(
            f"\nError: Not able to find the first vent-unit entry row on the " f'"{self.shape.name}" worksheet?'
        )

    def find_section_last_entry_row(self, _rows: int = 50) -> int:
        """Return the row number of the very last user-input entry row in the 'Vent Unit' section."""

        # -- The units block ends at the first empty cell in the locator column
        first_empty_row = _find_row_in_column(
            self.xl,
            self.shape.name,
            self.shape.units.locator_col_entry,
            self.section_first_entry_row,
            _rows,
            _is_empty,
        )
        if first_empty_row is None:
            raise Exception(
                f"\nError: Not able to find the last vent-unit entry row on the "
                f'"{self.shape.name}" worksheet before row {ROW_SEARCH_LIMIT}?'
            )
        return first_empty_row - 1

    def find_section_shape(self) -> None:
        try:
            self._section_header_row = self.find_section_header_row()
        except Exception:
            # Try one more time using a larger read-block
            self._section_header_row = self.find_section_header_row(_row_start=1, _row_end=1000)
        self._section_first_entry_row = self.find_section_first_entry_row()
        self._section_last_entry_row = self.find_section_last_entry_row()

    def get_vent_unit_num_by_phpp_id(self, _phpp_id: str) -> xl_writable:
        """Return the phpp-number of the Ventilation unit from the Additional Ventilation worksheet.

        Arguments:
        ---------
            * _phpp_id: (str): The phpp style id name (ie: "01ud-MyVentUnit") of
                the ventilation unit to find.

        Returns:
        --------
            * (xl_writable): The value from the PHPP indicating the number of
                the Ventilation unit.
        """

        search_column = str(self.shape.units.inputs.unit_selected.column)

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=search_column,
            _row_start=self.section_first_entry_row,
            _row_end=self.section_first_entry_row + 25,
        )

        for i, val in enumerate(xl_data, start=self.section_first_entry_row):
            if val == _phpp_id:
                num_col = col_offset(str(search_column), -3)
                return self.xl.get_data(self.shape.name, f"{num_col}{i}")

        raise Exception(
            f"Error: Cannot locate the Ventilation Unit: '{_phpp_id}' in"
            f" the '{self.shape.name}' worksheet Units section, column {search_column}?"
            f" Ensure that you enter the Ventilator-unit data into the '{self.shape.name}'"
            " worksheet before writing the spaces and ducts."
        )

    def get_ventilation_units(self) -> tuple[VentilatorDeviceUsage, ...]:
        """Return a tuple of VentilatorDeviceUsage objects from the PHPP worksheet."""
        input_shape = self.shape.units.inputs
        range_start = f"{input_shape.quantity.column}{self.section_first_entry_row}"
        range_end = f"{input_shape.temperature_below_defrost_used.column}{self.section_last_entry_row}"

        data = self.xl.get_data(
            self.shape.name,
            f"{range_start}:{range_end}",
        )
        if not isinstance(data, Collection):
            raise ValueError(
                f"There was a problem reading the ventilator-unit data from the "
                f"PHPP worksheet '{self.shape.name}', range: '{range_start}:{range_end}'?"
            )

        return tuple(VentilatorDeviceUsage.from_phpp_data_row(row) for row in data)


class VentDucts:
    """Reads and writes ventilation duct data in the PHPP 'Additional Vent' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.AddnlVent) -> None:
        self.xl = _xl
        self.shape = _shape
        self.section_header_row: int | None = None
        self.section_first_entry_row: int | None = None
        self.section_last_entry_row: int | None = None

    def find_section_header_row(self, _row_start: int = 1, _row_end: int = 300) -> int:
        """Return the row number of the ventilation-duct section header."""
        SEARCH_ROW_LIMIT = 10_000

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.ducts.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=_row_start):
            if self.shape.ducts.locator_string_header in str(val):
                return i

        # The Rooms section can be extended with inserted rows, which pushes the
        # downstream Units and Ducts sections beyond the initial search block.
        if _row_end < SEARCH_ROW_LIMIT:
            return self.find_section_header_row(
                _row_start=_row_end + 1,
                _row_end=min(_row_end + 300, SEARCH_ROW_LIMIT),
            )

        raise Exception(
            f'\n\tError: Not able to find the "Vent-Ducts" input section '
            f'of the "{self.shape.name}" worksheet? Please be sure the section '
            f'begins with the "{self.shape.ducts.locator_string_header}" '
            f"flag in column {self.shape.ducts.locator_col_header}?"
        )

    def find_section_first_entry_row(self) -> int:
        """Return the row number of the very first user-input entry row in the 'Ducts' section."""

        if not self.section_header_row:
            self.section_header_row = self.find_section_header_row()

        # -- Duct entry rows carry no number or marker to locate by, so the first one sits a fixed,
        # -- per-shape offset below the header (verified against each version's blank workbook).
        return self.section_header_row + self.shape.ducts.first_entry_row_offset

    def find_section_last_entry_row(self, _rows: int = 100) -> int:
        """Return the row number of the very last user-input entry row in the 'Ducts' section."""

        if not self.section_first_entry_row:
            self.section_first_entry_row = self.find_section_first_entry_row()

        # -- The duct rows carry no numbers, but instruction text follows the last entry row;
        # -- use it as the end-of-section flag.
        end_marker_row = _find_row_in_column(
            self.xl,
            self.shape.name,
            self.shape.ducts.locator_col_entry,
            self.section_first_entry_row,
            _rows,
            lambda _value: self.shape.ducts.locator_string_end in str(_value),
        )
        if end_marker_row is None:
            raise Exception(
                f"\nError: Not able to find the last duct entry row on the "
                f'"{self.shape.name}" worksheet before row {ROW_SEARCH_LIMIT}?'
            )
        return end_marker_row - 1

    def find_section_shape(self) -> None:
        self.section_header_row = self.find_section_header_row()
        self.section_first_entry_row = self.find_section_first_entry_row()
        self.section_last_entry_row = self.find_section_last_entry_row()


class AddnlVent:
    """IO Controller for the PHPP Additional Vent worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.AddnlVent) -> None:
        self.xl = _xl
        self.shape = _shape
        self.spaces = Spaces(self.xl, self.shape)
        self.vent_units = VentUnits(self.xl, self.shape)
        self.vent_ducts = VentDucts(self.xl, self.shape)

    def _write_section_rows(
        self,
        _rows: Sequence[vent_space.VentSpaceRow | vent_units.VentUnitRow | vent_ducts.VentDuctRow],
        _section: Spaces | VentUnits | VentDucts,
        _section_name: str,
    ) -> None:
        """Locate a section's capacity, then write only rows that fit within it."""
        if not _rows:
            return

        _section.find_section_shape()
        first_entry_row = _section.section_first_entry_row
        last_entry_row = _section.section_last_entry_row
        if first_entry_row is None or last_entry_row is None:
            raise ValueError(f"Unable to locate the {_section_name} entry rows on worksheet '{self.shape.name}'.")

        row_capacity = last_entry_row - first_entry_row + 1
        if len(_rows) > row_capacity:
            self.xl.output(
                f"\nPHPPAddlVentCapacityWarning: worksheet '{self.shape.name}' section '{_section_name}' "
                f"has {len(_rows)} entries but capacity is {row_capacity}; truncating to {row_capacity} rows. "
                "Use PHPP's Tools workbook to add rows.\n"
            )

        row_items = [
            row.create_xl_items(self.shape.name, _row_num=i)
            for i, row in enumerate(_rows[:row_capacity], start=first_entry_row)
        ]
        for item in xl_data.merge_xl_item_rows(row_items):
            self.xl.write_xl_item(item)

    def write_spaces(self, _spaces: list[vent_space.VentSpaceRow]) -> None:
        self._write_section_rows(_spaces, self.spaces, "Rooms")

    def write_vent_units(self, _vent_units: list[vent_units.VentUnitRow]) -> None:
        self._write_section_rows(_vent_units, self.vent_units, "Ventilation units")

    def write_vent_ducts(self, _vent_ducts: list[vent_ducts.VentDuctRow]) -> None:
        self._write_section_rows(_vent_ducts, self.vent_ducts, "Ducts")

    def activate_variants(self, variants_worksheet_name: str, vent_unit_range: str) -> None:
        """Link the Vent unit to the Variants worksheet."""

        # -- Ventilator Unit
        start_row = self.vent_units.find_section_first_entry_row()
        end_row = self.vent_units.find_section_last_entry_row()
        for i in range(start_row, end_row + 1):
            self.xl.write_xl_item(
                xl_data.XlItem(
                    self.shape.name,
                    f"{self.shape.units.inputs.unit_selected.column}{i}",
                    f"={variants_worksheet_name}!{vent_unit_range}",
                )
            )

        return None

    def get_ventilation_units(self) -> tuple[VentilatorDeviceUsage, ...]:
        """Return a list of Ventilation Units found in the Worksheet."""
        return self.vent_units.get_ventilation_units()

    def read_space_data(self) -> list[list]:
        """Return all of the Space data from the worksheet.

        Data is returned 'by column' from the results section of the worksheet.
        """

        if not self.spaces.section_first_entry_row:
            self.spaces.section_first_entry_row = self.spaces.find_section_first_entry_row()

        if not self.spaces.section_last_entry_row:
            self.spaces.section_last_entry_row = self.spaces.find_section_last_entry_row()

        rng_start = f"{self.shape.rooms.locator_col_entry}{self.spaces.section_first_entry_row-3}"
        rng_end = f"{self.shape.rooms.last_col}{self.spaces.section_last_entry_row}"
        data = self.xl.get_data_by_columns(
            _sheet_name=self.shape.name,
            _range_address=f"{rng_start}:{rng_end}",
        )
        return data
