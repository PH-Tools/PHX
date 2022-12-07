# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP "U-Values" worksheet."""

from __future__ import annotations
from typing import List, Optional

from PHX.xl import xl_data
from PHX.xl.xl_data import col_offset
from PHX.PHPP.phpp_model import uvalues_constructor
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.sheet_io.io_variants import VariantAssemblyLayerName
from PHX.xl import xl_app


class UValues:
    """IO Controller for the PHPP "U-Values" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.UValues):
        self.xl = _xl
        self.shape = _shape
        self.constructor_start_rows: List[int] = []
        self.cache = {}

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
        self, _name, _row_start: int = 1, _row_end: int = 1730, _use_cache: bool = False
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
        if_num_column = col_offset(
            str(self.shape.constructor.inputs.display_name.column), id_num_offset
        )
        prefix = self.xl.get_data(self.shape.name, f"{if_num_column}{row}")
        name_with_id = f"{prefix}-{_name}"
        self.cache[_name] = name_with_id

        return name_with_id

    def write_construction_blocks(
        self, _const_blocks: List[uvalues_constructor.ConstructorBlock]
    ) -> None:
        if not self.constructor_start_rows:
            self.constructor_start_rows = self.get_start_rows()

        assert len(_const_blocks) <= len(
            self.constructor_start_rows
        ), f"Error: Too many U-Value Constructions: {len(self.constructor_start_rows)}"

        for construction, start_row in zip(_const_blocks, self.constructor_start_rows):
            for item in construction.create_xl_items(self.shape.name, start_row):
                self.xl.write_xl_item(item)

    def get_used_constructor_names(self) -> List[str]:
        """Return a list of the used construction names."""

        if not self.constructor_start_rows:
            self.constructor_start_rows = self.get_start_rows()

        name_col = self.shape.constructor.inputs.display_name.column

        construction_names = []
        for row_num in self.constructor_start_rows:
            assembly_name = self.xl.get_data(
                _sheet_name=self.shape.name,
                _range=f"{name_col}{row_num + 2}",
            )
            if assembly_name:
                construction_names.append(assembly_name)

        return sorted(construction_names)

    def clear_constructor_data(self, clear_name: bool = True):
        """Remove all of the existing input data from the constructor."""

        if not self.constructor_start_rows:
            self.constructor_start_rows = self.get_start_rows()

        for row_num in self.constructor_start_rows:
            # -- main body data
            data_block_start = (
                f"{self.shape.constructor.inputs.sec_1_description.column}{row_num + 8}"
            )
            data_block_end = (
                f"{self.shape.constructor.inputs.thickness.column}{row_num + 15}"
            )
            data_block_range = f"{data_block_start}:{data_block_end}"
            self.xl.write_xl_item(xl_data.XlItem(self.shape.name, data_block_range, None))

            # -- surface films
            self.xl.write_xl_item(
                xl_data.XlItem(
                    self.shape.name,
                    f"{self.shape.constructor.inputs.r_si.column}{row_num + 4}:{self.shape.constructor.inputs.r_se.column}{row_num + 5}",
                    None,
                )
            )

            # -- Assembly Name (Sometimes, like with Variants, will want to keep this)
            if clear_name:
                self.xl.write_xl_item(
                    xl_data.XlItem(
                        self.shape.name,
                        f"{self.shape.constructor.inputs.display_name.column}{row_num + 2}",
                        None,
                    )
                )

    def activate_variants(self, _assembly_phpp_ids: List[VariantAssemblyLayerName]):
        """Connect all the links to make the 'Variants' page drive the input values."""

        if not self.constructor_start_rows:
            self.constructor_start_rows = self.get_start_rows()

        self.clear_constructor_data(clear_name=False)

        name_col = self.shape.constructor.inputs.display_name.column

        for row_num in self.constructor_start_rows:
            assembly_name = self.xl.get_data(
                _sheet_name=self.shape.name,
                _range=f"{name_col}{row_num + 2}",
            )

            # -- Find the matching PHPP-ID name from the Variants
            # -- worksheet and make the link
            for variant_layer_id in _assembly_phpp_ids:
                if variant_layer_id.display_name == assembly_name:
                    # -- Link to the variants layer name
                    self.xl.write_xl_item(
                        xl_data.XlItem(
                            self.shape.name,
                            f"{self.shape.constructor.inputs.variants_layer_name}{row_num + 8}",
                            variant_layer_id.phpp_id,
                        )
                    )

                    # -- Link the variants layer conductivity
                    self.xl.write_xl_item(
                        xl_data.XlItem(
                            self.shape.name,
                            f"{self.shape.constructor.inputs.sec_1_conductivity.column}{row_num + 8}",
                            f"={self.shape.constructor.inputs.variants_conductivity}{row_num + 8}",
                        )
                    )

                    # -- Link the variants layer thickness
                    self.xl.write_xl_item(
                        xl_data.XlItem(
                            self.shape.name,
                            f"{self.shape.constructor.inputs.thickness.column}{row_num + 8}",
                            f"={self.shape.constructor.inputs.variants_thickness}{row_num + 8}",
                        )
                    )

                    # -- Set the surface films to zero
                    self.xl.write_xl_item(
                        xl_data.XlItem(
                            self.shape.name,
                            f"{self.shape.constructor.inputs.r_si.column}{row_num + 4}:{self.shape.constructor.inputs.r_se.column}{row_num + 5}",
                            0,
                        )
                    )
