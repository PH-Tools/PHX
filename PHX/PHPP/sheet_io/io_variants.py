# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP "Variants" worksheet."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict

from PHX.xl import xl_data
from PHX.xl.xl_data import col_offset
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_app


@dataclass
class VariantAssemblyLayerName:
    """Variants Assembly PHPP ID."""

    prefix: str
    display_name: str

    @property
    def phpp_id(self) -> str:
        return f"{self.prefix}-{self.display_name}"


@dataclass
class VariantWindowTypeName:
    """Variants Window Type PHPP ID."""

    prefix: str
    display_name: str

    @property
    def phpp_id(self) -> str:
        return f"{self.prefix}-{self.display_name}"


class Variants:
    """IO Controller for the PHPP "Variants" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Variants):
        self.xl = _xl
        self.shape = _shape
        self.user_input_section_start_row: Optional[int] = None
        self.start_assembly_layers: Optional[int] = None
        self.start_window_types: Optional[int] = None
        self.start_ventilation: Optional[int] = None

    def get_user_input_section_start(self, _row_start=1, _rows=500) -> int:
        """Return the row number of the user-input section header."""
        # -- Get the data from Excel in one operation
        col_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.input_header.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_start + _rows,
        )

        for i, column_val in enumerate(col_data, start=_row_start):
            if column_val == self.shape.input_header.locator_string_header:
                return i

        raise Exception(
            f'Error: Unable to locate the "{self.shape.input_header.locator_string_header}" '
            f'section of the "{self.shape.name}" worksheet in column '
            f'"{self.shape.input_header.locator_col_header}"?'
        )

    def get_assembly_layers_start(
        self, _row_start: Optional[int] = None, _rows: int = 100
    ) -> int:
        """Return the row number of the start of the Building Assembly Layers variant section."""
        if not self.user_input_section_start_row:
            self.user_input_section_start_row = self.get_user_input_section_start()

        # -- Get the data from Excel in one operation
        row_start = _row_start or self.user_input_section_start_row
        col_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.assemblies.locator_col_header,
            _row_start=row_start,
            _row_end=row_start + _rows,
        )

        for i, column_val in enumerate(col_data, start=row_start):
            if column_val == self.shape.assemblies.locator_string_header:
                return i

        raise Exception(
            f'Error: Unable to locate the "{self.shape.assemblies.locator_string_header}" '
            f'section of the "{self.shape.name}" worksheet in column '
            f'"{self.shape.assemblies.locator_col_header}"?'
        )

    def get_window_types_start(
        self, _row_start: Optional[int] = None, _rows: int = 300
    ) -> int:
        """Return the row number of the start of the Window Types input section."""
        if not self.start_assembly_layers:
            self.start_assembly_layers = self.get_assembly_layers_start()

        # -- Get the data from Excel in one operation
        row_start = _row_start or self.start_assembly_layers
        col_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.windows.locator_col_header,
            _row_start=row_start,
            _row_end=row_start + _rows,
        )

        for i, column_val in enumerate(col_data, start=row_start):
            if column_val == self.shape.windows.locator_string_header:
                return i

        raise Exception(
            f'Error: Unable to locate the "{self.shape.windows.locator_string_header}" '
            f'section of the "{self.shape.name}" worksheet in column '
            f'"{self.shape.windows.locator_col_header}"?'
        )

    def get_ventilation_start(
        self, _row_start: Optional[int] = None, _rows: int = 300
    ) -> int:
        """Return the row number of the start of the Ventilation input section."""
        if not self.start_window_types:
            self.start_window_types = self.get_window_types_start()

        # -- Get the data from Excel in one operation
        row_start = _row_start or self.start_window_types
        col_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.ventilation.locator_col_header,
            _row_start=row_start,
            _row_end=row_start + _rows,
        )

        for i, column_val in enumerate(col_data, start=row_start):
            if column_val == self.shape.ventilation.locator_string_header:
                return i

        raise Exception(
            f'Error: Unable to locate the "{self.shape.ventilation.locator_string_header}" '
            f'section of the "{self.shape.name}" worksheet in column '
            f'"{self.shape.ventilation.locator_col_header}"?'
        )

    def get_ventilation_input_item_rows(self) -> Dict[str, int]:
        """Return a dict of the input items and their row-numbers for the ventilation items."""
        if not self.start_ventilation:
            self.start_ventilation = self.get_ventilation_start()

        read_data = self.xl.get_single_column_data(
            self.shape.name,
            self.shape.ventilation.input_col,
            self.start_ventilation + 1,
            self.start_ventilation + 10,
        )

        return {
            str(_): i for i, _ in enumerate(read_data, start=self.start_ventilation + 1)
        }

    def write_assembly_layer(self, _assembly_name: str, _assembly_num: int) -> None:
        """Write a new assembly layer to the Variants worksheet."""

        if not self.start_assembly_layers:
            self.start_assembly_layers = self.get_assembly_layers_start()

        # -- Variants assemblies are input every other row
        row_offset = (_assembly_num * 2) + 1
        self.xl.write_xl_item(
            xl_data.XlItem(
                self.shape.name,
                f"{self.shape.assemblies.input_col}{self.start_assembly_layers + row_offset}",
                str(_assembly_name),
            )
        )

        return None

    def write_window_type(self, _window_type_name: str, _window_type_num: int) -> None:
        """Write a new Window Type name to the Variants worksheet."""
        if not self.start_window_types:
            self.start_window_types = self.get_window_types_start()

        # -- Window types are input every 8th row
        row_offset = (_window_type_num * 8) + 1
        self.xl.write_xl_item(
            xl_data.XlItem(
                self.shape.name,
                f"{self.shape.assemblies.input_col}{self.start_window_types + row_offset}",
                str(_window_type_name),
            )
        )

        return None

    def get_assembly_layer_phpp_ids(self) -> List[VariantAssemblyLayerName]:
        """Return a list of the Variants PHPP-ids for all assembly layers."""
        if not self.start_assembly_layers:
            self.start_assembly_layers = self.get_assembly_layers_start()

        # -- Get the data from Excel in one operation
        col_data = self.xl.get_multiple_column_data(
            _sheet_name=self.shape.name,
            _col_start=col_offset(self.shape.assemblies.input_col, -1),
            _col_end=self.shape.assemblies.input_col,
            _row_start=self.start_assembly_layers + 1,
            _row_end=self.start_assembly_layers + 52,
        )

        return [
            VariantAssemblyLayerName(str(data_list[0]), str(data_list[1]))
            for data_list in col_data
            if all(data_list)
        ]

    def get_window_type_phpp_ids(self) -> Dict[str, VariantWindowTypeName]:
        if not self.start_window_types:
            self.start_window_types = self.get_window_types_start()

        # -- Get the data from Excel in one operation
        col_data = self.xl.get_multiple_column_data(
            _sheet_name=self.shape.name,
            _col_start=col_offset(self.shape.assemblies.input_col, -1),
            _col_end=self.shape.assemblies.input_col,
            _row_start=self.start_window_types + 1,
            _row_end=self.start_window_types + 207,
        )

        # -- Return dict with the PHPP ID objects keyed' by their display-name (no prefix)
        # -- to allow for faster lookup when entering window surface line-items.
        # -- ie: {'Type1': VariantWindowTypeName('a-Type1'), 'Type2':VariantWindowTypeName('b-Type2'), ... }
        return {
            str(data_list[1]): VariantWindowTypeName(str(data_list[0]), str(data_list[1]))
            for data_list in col_data
            if all(data_list)
        }
