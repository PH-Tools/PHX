# -*- Python Version: 3.10 -*-

"""Data-entry constructor for the U-Values Worksheet."""

from dataclasses import dataclass
from functools import partial

from PHX.model.constructions import PhxConstructionOpaque, PhxLayer
from PHX.model.enums.building import ComponentExposureExterior, ComponentFaceType
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


@dataclass
class ConstructorBlock:
    """A single U-Value/Constructor entry block.

    PHPP resolves each block's surface resistances from two selector cells: an
    orientation (Rsi) and an adjacency (Rse). Both are properties of how the assembly
    is *used*, not of the assembly itself, so the exposure of the Components which
    reference the assembly is carried alongside the construction.
    """

    shape: shape_model.UValues
    phx_construction: PhxConstructionOpaque = PhxConstructionOpaque()
    face_type: ComponentFaceType = ComponentFaceType.WALL
    exposure_exterior: ComponentExposureExterior = ComponentExposureExterior.EXTERIOR

    @property
    def r_si_selector(self) -> str:
        """Return the PHPP orientation-selector string (Rsi) for the block's face-type."""
        selectors = self.shape.constructor.inputs.r_si_selectors
        if self.face_type == ComponentFaceType.ROOF_CEILING:
            return selectors.roof
        elif self.face_type == ComponentFaceType.FLOOR:
            return selectors.floor
        else:
            return selectors.wall

    @property
    def r_se_selector(self) -> str:
        """Return the PHPP adjacency-selector string (Rse) for the block's exterior exposure."""
        selectors = self.shape.constructor.inputs.r_se_selectors
        if self.exposure_exterior == ComponentExposureExterior.GROUND:
            return selectors.ground
        elif self.exposure_exterior == ComponentExposureExterior.SURFACE or self.exposure_exterior.value > 0:
            # -- Adjacent to another zone: EN ISO 6946 treats the outer face as interior.
            return selectors.ventilated
        else:
            return selectors.exterior

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

    def create_xl_items(self, _sheet_name: str, _start_row: int) -> list[xl_data.XlItem]:
        """Convert the PHX-Construction into a list of XLItems for writing to the PHPP."""

        create_range = partial(self._create_range, _start_row=_start_row)
        XLItemUValues = partial(xl_data.XlItem, _sheet_name)

        # -- Build the basic assembly attributes
        xl_items_list: list[xl_data.XlItem] = [
            XLItemUValues(
                create_range("display_name", self.shape.constructor.inputs.name_row_offset),
                f"'{self.phx_construction.display_name}",
            ),
            # -- Note: the selectors are written as strings, not numbers. PHPP reads only the
            # -- leading digit and resolves the resistance itself, which keeps the
            # -- climate-dependence of Rsi and the 'Rse = Rsi' behavior of 'Ventilated' intact.
            XLItemUValues(
                create_range("r_si", self.shape.constructor.inputs.rsi_row_offset),
                self.r_si_selector,
            ),
            XLItemUValues(
                create_range("r_se", self.shape.constructor.inputs.rse_row_offset),
                self.r_se_selector,
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
                layer_items: list[xl_data.XlItem] = [
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
