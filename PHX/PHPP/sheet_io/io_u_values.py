# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP "U-Values" worksheet."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, List, Optional

from ph_units.unit_type import Unit

from PHX.model.constructions import PhxConstructionOpaque
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import uvalues_constructor
from PHX.PHPP.sheet_io.io_variants import VariantAssemblyLayerName
from PHX.xl import xl_app, xl_data
from PHX.xl.xl_data import col_offset


class NoEmptyConstructorError(Exception):
    def __init__(self):
        """Raises if there are no empty COnstructors in the worksheet."""
        self.msg = "No empty constructors found. Please remove some constructors and try again."
        super().__init__(self.msg)


@dataclass
class ExistingAssemblyData:
    name: str
    u_value: Unit
    r_value: Unit
    ext_exposure: str
    int_exposure: str


class UValues:
    """IO Controller for the PHPP "U-Values" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.UValues) -> None:
        self.xl = _xl
        self.shape = _shape
        self._constructor_start_rows: List[int] = []
        self.cache = {}

    # -------------------------------------------------------------------------
    # -- Getters

    @property
    def all_constructor_start_rows(self) -> List[int]:
        """Return a list of all of the PHPP Constructor starting rows"""
        if not self._constructor_start_rows:
            self._constructor_start_rows = self.get_start_rows()
        return self._constructor_start_rows

    @property
    def used_constructor_start_rows(self) -> Generator[int, None, None]:
        """Return the PHPP Constructors that have any data in them, one at a time."""
        for row_num in self.all_constructor_start_rows:
            name_col = self.shape.constructor.inputs.display_name.column
            name_range = f"{name_col}{row_num + self.shape.constructor.inputs.name_row_offset}"
            if self.xl.get_data(self.shape.name, name_range):
                yield row_num

    def get_start_rows(self, _row_start: int = 1, _row_end: int = 1730) -> List[int]:
        """Reads through the U-Values worksheet and finds each of the constructor 'start' (title) rows.

        Arguments:
        ----------
            * _row_start: (int) default=1
            * _row_end: (int) default=1730

        Returns:
        -------
            * (List[int]): A list of all of the starting title row numbers found.
        """

        # -- Get the data from Excel in one operation
        col_data = self.xl.get_multiple_column_data(
            _sheet_name=self.shape.name,
            _col_start=self.shape.constructor.locator_col_header,
            _col_end=col_offset(self.shape.constructor.locator_col_header, 1),
            _row_start=_row_start,
            _row_end=_row_end,
        )

        # -- Find the starting row numbers
        constructors: List[int] = []
        for i, column_val in enumerate(col_data):
            if column_val[0] == self.shape.constructor.locator_string_header:
                constructors.append(i)
            elif column_val[0] == "Bauteil Nr.":  # Fuck you PHPP
                constructors.append(i)

        return constructors

    def get_constructor_phpp_id_by_name(
        self,
        _name: str,
        _row_start: int = 1,
        _row_end: int = 1730,
        _use_cache: bool = False,
    ) -> Optional[str]:
        """Returns the full PHPP-style value for the constructor with a specified name.

        ie: "Exterior Wall" in constructor 1 will return "01ud-Exterior Wall"

        Argument:
        ---------
            * _name: (str) The name to search for.
            * _row_start: (int) default=1
            * _row_end: (int) default=1730

        Returns:
        --------
            * (Optional[str]): The full PHPP-style id for the construction. ie: "01ud-MyConstruction"
        """

        if _use_cache:
            try:
                return self.cache[_name]
            except KeyError:
                pass

        row = self.xl.get_row_num_of_value_in_column(
            sheet_name=self.shape.name,
            row_start=_row_start,
            row_end=_row_end,
            col=str(self.shape.constructor.inputs.display_name.column),
            find=_name,
        )

        if not row:
            return

        id_num_offset = self.shape.constructor.inputs.phpp_id_num_col_offset
        if_num_column = col_offset(str(self.shape.constructor.inputs.display_name.column), id_num_offset)
        prefix = self.xl.get_data(self.shape.name, f"{if_num_column}{row}")
        name_with_id = f"{prefix}-{_name}"
        self.cache[_name] = name_with_id

        return name_with_id

    def get_used_constructor_names(self) -> List[str]:
        """Return a list of the used construction names."""

        name_col = self.shape.constructor.inputs.display_name.column

        construction_names = []
        for row_num in self.all_constructor_start_rows:
            assembly_name = self.xl.get_data(
                _sheet_name=self.shape.name,
                _range=f"{name_col}{row_num + self.shape.constructor.inputs.name_row_offset}",
            )
            if assembly_name:
                construction_names.append(assembly_name)

        return sorted(construction_names)

    def get_constructor_r_si_type(self, _row_num: int) -> str:
        """Return "Wall", "Roof" or "Floor" depending on the constructor type."""
        col = self.shape.constructor.inputs.r_si.column
        row_num = _row_num + self.shape.constructor.inputs.rsi_row_offset
        return str(self.xl.get_data(self.shape.name, f"{col}{row_num}"))

    def get_constructor_r_se_type(self, _row_num: int) -> str:
        """Return "Ground", "Outdoor air" or "Ventilated" depending on the constructor type."""
        col = self.shape.constructor.inputs.r_se.column
        row_num = _row_num + self.shape.constructor.inputs.rse_row_offset
        return str(self.xl.get_data(self.shape.name, f"{col}{row_num}"))

    def get_constructor_name(self, _row_num: int) -> str:
        """Return the name of the constructor at the specified row."""
        col = self.shape.constructor.inputs.display_name.column
        row_num = _row_num + self.shape.constructor.inputs.name_row_offset
        return str(self.xl.get_data(self.shape.name, f"{col}{row_num}"))

    def get_first_empty_constructor_start_row(self) -> int:
        """Return the first empty constructor's row number."""
        for row_num in self.all_constructor_start_rows:
            name = self.get_constructor_name(row_num)
            if not self.get_constructor_name(row_num) or name == "None":
                return row_num
        else:
            raise NoEmptyConstructorError

    def get_constructor_u_value(self, _row_num: int) -> Unit:
        """Return the U-Value of the constructor at the specified row."""
        col = self.shape.constructor.inputs.result_val_col
        row_num = _row_num + self.shape.constructor.inputs.result_val_row_offset
        value = float(self.xl.get_data(self.shape.name, f"{col}{row_num}"))
        unit_type = self.shape.constructor.inputs.result_val_unit

        #  -- Handle the fact it might be SI or IP units
        if unit_type == "W/M2K":
            # -- It is already a U-Value
            return Unit(value, unit_type)
        else:
            # -- It is an R-Value, so return the inverse
            return Unit(value, unit_type).inverse()

    def get_constructor_r_value(self, _row_num: int) -> Unit:
        """Return the U-Value of the constructor at the specified row."""
        col = self.shape.constructor.inputs.result_val_col
        row_num = _row_num + self.shape.constructor.inputs.result_val_row_offset
        value = float(self.xl.get_data(self.shape.name, f"{col}{row_num}"))
        unit_type = self.shape.constructor.inputs.result_val_unit

        #  -- Handle the fact it might be SI or IP units
        if unit_type == "W/M2K":
            # -- It is an U-Value, so return the inverse
            return Unit(value, unit_type).inverse()
        else:
            # -- It is already an R-Value
            return Unit(value, unit_type)

    # -------------------------------------------------------------------------
    # -- Writers

    def write_single_PHX_construction(self, _phx_construction, _start_row) -> None:
        """Write a single PHX Construction to the PHPP worksheet."""
        new_constructor = uvalues_constructor.ConstructorBlock(self.shape, _phx_construction)
        self.write_single_constructor_block(new_constructor, _start_row)

    def write_single_constructor_block(
        self, _construction: uvalues_constructor.ConstructorBlock, _start_row: int
    ) -> None:
        """Write a single Construction with all the layers to the PHPP worksheet."""
        for item in _construction.create_xl_items(self.shape.name, _start_row):
            self.xl.write_xl_item(item)

    def write_constructor_blocks(self, _const_blocks: List[uvalues_constructor.ConstructorBlock]) -> None:
        """Write a list of ConstructorBlocks to the U-Values worksheet."""

        self.clear_all_constructor_data(_clear_name=True)

        assert len(_const_blocks) <= len(
            self.all_constructor_start_rows
        ), f"Error: Too many U-Value Constructions: {len(self.all_constructor_start_rows)}"

        for construction, start_row in zip(_const_blocks, self.all_constructor_start_rows):
            self.write_single_constructor_block(construction, start_row)

    def add_new_phx_construction(self, _phx_construction: PhxConstructionOpaque) -> str:
        """Add a new PHX Construction to the PHPP worksheet in the first empty slot found.

        Returns:
        --------
            * (str): The PHPP-id of the new construction.
        """
        new_constructor = uvalues_constructor.ConstructorBlock(self.shape, _phx_construction)
        self.write_single_constructor_block(new_constructor, self.get_first_empty_constructor_start_row())

        return self.get_constructor_phpp_id_by_name(_phx_construction.display_name)

    # -------------------------------------------------------------------------
    # -- Removers

    def clear_single_constructor_data(self, _row_num, _clear_name: bool = False) -> None:
        """Clears the existing data from a single constructor block."""
        # -- main body data
        data_block_start = f"{self.shape.constructor.inputs.sec_1_description.column}{_row_num + self.shape.constructor.inputs.first_layer_row_offset}"
        data_block_end = f"{self.shape.constructor.inputs.thickness.column}{_row_num + self.shape.constructor.inputs.last_layer_row_offset}"
        data_block_range = f"{data_block_start}:{data_block_end}"
        self.xl.write_xl_item(xl_data.XlItem(self.shape.name, data_block_range, None))

        # -- surface films
        self.xl.write_xl_item(
            xl_data.XlItem(
                self.shape.name,
                f"{self.shape.constructor.inputs.r_si.column}{_row_num + 4}:{self.shape.constructor.inputs.r_se.column}{_row_num + 5}",
                None,
            )
        )

        # -- Assembly Name (Sometimes, like with Variants, will want to keep this)
        if _clear_name:
            self.xl.write_xl_item(
                xl_data.XlItem(
                    self.shape.name,
                    f"{self.shape.constructor.inputs.display_name.column}{_row_num + self.shape.constructor.inputs.name_row_offset}",
                    None,
                )
            )

    def clear_all_constructor_data(self, _clear_name: bool = True) -> None:
        """Remove all of the existing input data from all of the constructors in the PHPP."""
        for row_num in self.all_constructor_start_rows:
            self.clear_single_constructor_data(row_num, _clear_name)

    # -------------------------------------------------------------------------

    def activate_variants(self, _assembly_phpp_ids: List[VariantAssemblyLayerName]) -> None:
        """Connect all the links to make the 'Variants' page drive the input values."""

        self.clear_all_constructor_data(_clear_name=False)

        name_col = self.shape.constructor.inputs.display_name.column

        for row_num in self.all_constructor_start_rows:
            assembly_name = self.xl.get_data(
                _sheet_name=self.shape.name,
                _range=f"{name_col}{row_num + self.shape.constructor.inputs.name_row_offset}",
            )

            # -- Find the matching PHPP-ID name from the Variants
            # -- worksheet and make the link
            for variant_layer_id in _assembly_phpp_ids:
                if variant_layer_id.display_name == assembly_name:
                    # -- Link to the variants layer name
                    self.xl.write_xl_item(
                        xl_data.XlItem(
                            self.shape.name,
                            f"{self.shape.constructor.inputs.variants_layer_name}{row_num + self.shape.constructor.inputs.first_layer_row_offset}",
                            variant_layer_id.phpp_id,
                        )
                    )

                    # -- Link the variants layer conductivity
                    self.xl.write_xl_item(
                        xl_data.XlItem(
                            self.shape.name,
                            f"{self.shape.constructor.inputs.sec_1_conductivity.column}{row_num + self.shape.constructor.inputs.first_layer_row_offset}",
                            f"={self.shape.constructor.inputs.variants_conductivity}{row_num + self.shape.constructor.inputs.first_layer_row_offset}",
                        )
                    )

                    # -- Link the variants layer thickness
                    self.xl.write_xl_item(
                        xl_data.XlItem(
                            self.shape.name,
                            f"{self.shape.constructor.inputs.thickness.column}{row_num + self.shape.constructor.inputs.first_layer_row_offset}",
                            f"={self.shape.constructor.inputs.variants_thickness}{row_num + self.shape.constructor.inputs.first_layer_row_offset}",
                        )
                    )

                    # -- Set the surface films to zero
                    self.xl.write_xl_item(
                        xl_data.XlItem(
                            self.shape.name,
                            f"{self.shape.constructor.inputs.r_si.column}{row_num + self.shape.constructor.inputs.rse_row_offset}:{self.shape.constructor.inputs.r_se.column}{row_num + self.shape.constructor.inputs.rsi_row_offset}",
                            0,
                        )
                    )

    def get_all_envelope_assemblies(self) -> List[ExistingAssemblyData]:
        assemblies: List[ExistingAssemblyData] = []

        for row_num in self.used_constructor_start_rows:
            existing_assembly = ExistingAssemblyData(
                self.get_constructor_name(row_num),
                self.get_constructor_u_value(row_num),
                self.get_constructor_r_value(row_num),
                self.get_constructor_r_se_type(row_num),
                self.get_constructor_r_si_type(row_num),
            )
            assemblies.append(existing_assembly)

        return assemblies
