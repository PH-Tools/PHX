# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Data-entry constructor for the U-Values Worksheet."""

from dataclasses import dataclass
from functools import partial
from typing import List

from PHX.model.constructions import PhxConstructionOpaque, PhxLayer
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


@dataclass
class ConstructorBlock:
    """A single U-Value/Constructor entry block."""

    shape: shape_model.UValues
    phx_construction: PhxConstructionOpaque = PhxConstructionOpaque()

    def _create_range(self, _field_name: str, _row_offset: int, _start_row: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.constructor.inputs, _field_name).column
        return f"{col}{_start_row + _row_offset}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.constructor.inputs, _field_name).unit

    def is_mass_material(self, _layer: PhxLayer) -> bool:
        """Return True if the Layer is an SD 'Mass' Layer."""

        for material in _layer.materials:
            if material.display_name == "MAT_Mass" and material.conductivity == 100:
                return True

        return False

    def create_xl_items(self, _sheet_name: str, _start_row: int) -> List[xl_data.XlItem]:
        """Convert the PHX-Construction into a list of XLItems for writing to the PHPP."""

        create_range = partial(self._create_range, _start_row=_start_row)
        XLItemUValues = partial(xl_data.XlItem, _sheet_name)

        # -- Build the basic assembly attributes
        xl_items_list: List[xl_data.XlItem] = [
            XLItemUValues(
                create_range("display_name", self.shape.constructor.inputs.name_row_offset),
                f"'{self.phx_construction.display_name}",
            ),
            XLItemUValues(
                create_range("r_si", self.shape.constructor.inputs.rse_row_offset),
                0.0,
                "M2K/W",
                self._get_target_unit("r_si"),
            ),
            XLItemUValues(
                create_range("r_se", self.shape.constructor.inputs.rsi_row_offset),
                0.0,
                "M2K/W",
                self._get_target_unit("r_se"),
            ),
        ]

        # -- Build all the layers of the assembly
        for i, layer in enumerate(
            self.phx_construction.layers,
            start=self.shape.constructor.inputs.first_layer_row_offset,
        ):
            if self.is_mass_material(layer):
                continue

            xl_items_list.append(
                XLItemUValues(
                    create_range("thickness", i),
                    layer.thickness_mm,
                    "MM",
                    self._get_target_unit("thickness"),
                )
            )

            # -- add in each of the PhxMaterials found in the PhxLayer.materials collection
            for j, material in enumerate(layer.materials, start=1):
                layer_items: List[xl_data.XlItem] = [
                    XLItemUValues(
                        create_range(f"sec_{j}_description", i),
                        f"'{material.display_name}",
                    ),
                    XLItemUValues(
                        create_range(f"sec_{j}_conductivity", i),
                        material.conductivity,
                        "W/MK",
                        self._get_target_unit(f"sec_{j}_conductivity"),
                    ),
                ]
                # -- Only add the percentage info for sections 2 and 3...
                if j > 1:
                    layer_items.append(
                        XLItemUValues(
                            create_range(
                                f"sec_{j}_percentage",
                                getattr(self.shape.constructor.inputs, f"sec_{j}_percentage").row,
                            ),
                            material.percentage_of_assembly,
                        )
                    )
                xl_items_list.extend(layer_items)

        return xl_items_list
