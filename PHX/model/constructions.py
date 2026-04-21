# -*- Python Version: 3.10 -*-

"""PHX Construction, Materials Classes"""

from __future__ import annotations

import uuid
import warnings
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from PHX.model.assembly_pathways import identify_heat_flow_pathways

if TYPE_CHECKING:
    from PHX.model.assembly_pathways import PhxHeatFlowPathway

# -----------------------------------------------------------------------------
# Materials


@dataclass
class PhxColor:
    """An ARGB color value used for material display in WUFI-Passive.

    Attributes:
        alpha (int): Alpha (opacity) channel. Default: 255.
        red (int): Red channel. Default: 255.
        green (int): Green channel. Default: 255.
        blue (int): Blue channel. Default: 255.
    """

    # Default color is white
    alpha: int = 255
    red: int = 255
    green: int = 255
    blue: int = 255


@dataclass
class PhxMaterial:
    """A single building material with thermal, hygric, and display properties.

    Used as the base unit within PhxLayer to define assembly constructions.
    Thermal conductivity (W/mK) and thickness drive R-value calculations.

    Attributes:
        id_num (int): Auto-incremented identifier.
        display_name (str): Human-readable material name. Default: "".
        conductivity (float): Thermal conductivity in W/mK. Default: 0.0.
        density (float): Material density in kg/m3. Default: 0.0.
        porosity (float): Volumetric porosity fraction. Default: 0.95.
        heat_capacity (float): Specific heat capacity in J/kgK. Default: 0.0.
        water_vapor_resistance (float): Water vapor diffusion resistance factor (mu). Default: 1.0.
        reference_water (float): Reference water content in kg/m3. Default: 0.0.
        percentage_of_assembly (float): Fraction of the layer area occupied by this material. Default: 1.0.
        argb_color (PhxColor): Display color for the material. Default: white.
    """

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)

    display_name: str = ""
    conductivity: float = 0.0
    density: float = 0.0
    porosity: float = 0.95
    heat_capacity: float = 0.0
    water_vapor_resistance: float = 1.0
    reference_water: float = 0.0
    percentage_of_assembly: float = 1.0
    argb_color: PhxColor = field(default_factory=PhxColor)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    def __eq__(self, other: PhxMaterial) -> bool:
        return self.id_num == other.id_num

    def equivalent(self, other: PhxMaterial) -> bool:
        """Check if two materials are equivalent except for their ID-Number."""
        return all(
            [
                self.display_name == other.display_name,
                self.conductivity == other.conductivity,
                self.density == other.density,
                self.porosity == other.porosity,
                self.heat_capacity == other.heat_capacity,
                self.water_vapor_resistance == other.water_vapor_resistance,
                self.reference_water == other.reference_water,
                self.argb_color == other.argb_color,
            ]
        )

    def __hash__(self) -> int:
        return hash(self.id_num)


# -----------------------------------------------------------------------------
# Layers (and Mixed Materials)


@dataclass
class PhxLayerDivisionCell:
    """A single cell at a column/row position in a PhxLayerDivisionGrid, holding one material.

    Attributes:
        row (int): Row index in the division grid.
        column (int): Column index in the division grid.
        material (PhxMaterial): The material assigned to this cell.
        expanding_contracting (int): Expansion/contraction behavior flag. Default: 2 (Exp./Contr.).
    """

    row: int
    column: int
    material: PhxMaterial
    expanding_contracting: int = 2  # 2="Exp./Contr."

    def __eq__(self, other: PhxLayerDivisionCell) -> bool:
        return all(
            [
                self.row == other.row,
                self.column == other.column,
                self.material.equivalent(other.material),
                self.expanding_contracting == other.expanding_contracting,
            ]
        )


@dataclass
class PhxLayerDivisionGrid:
    """A grid of PhxLayerDivisionCells to support 'mixed' materials in a single layer.

    Used to model inhomogeneous layers (e.g., wood studs with insulation fill) by
    subdividing the layer cross-section into a grid of cells, each with its own material.

    The Cell grid is ordered from top-left to bottom-right:

    |    | C0  | C1  | C2  | ...
    |:---|:---:|:---:|:---:|:---:
    | R0 | 0,0 | 1,0 | 2,0 | ...
    | R1 | 0,1 | 1,1 | 2,1 | ...
    | R2 | 0,2 | 1,2 | 2,2 | ...

    Attributes:
        is_a_steel_stud_cavity (bool): If True, the layer represents a steel-stud cavity
            (equivalence checking skips division comparison). Default: False.
    """

    _row_heights: list[float] = field(default_factory=list)
    _column_widths: list[float] = field(default_factory=list)
    _cells: list[PhxLayerDivisionCell] = field(default_factory=list)
    is_a_steel_stud_cavity: bool = False

    @property
    def column_widths(self) -> list[float]:
        """Return the list of column widths."""
        return self._column_widths

    @property
    def column_count(self) -> int:
        """Return the number of columns in the grid."""
        return len(self._column_widths)

    @property
    def row_heights(self) -> list[float]:
        """Return the list of row heights."""
        return self._row_heights

    @property
    def row_count(self) -> int:
        """Return the number of rows in the grid."""
        return len(self._row_heights)

    @property
    def cell_count(self) -> int:
        """Return the total number of cells in the grid."""
        return self.row_count * self.column_count

    @property
    def cells(self) -> list[PhxLayerDivisionCell]:
        """Return a list of all the PhxLayerDivisionCells in the grid, ordered by row then column"""
        return sorted(self._cells, key=lambda x: (x.row, x.column))

    def set_column_widths(self, _column_widths: Iterable[float]) -> None:
        """Set the column widths of the grid."""
        self._column_widths = []
        for width in _column_widths:
            self.add_new_column(width)

    def add_new_column(self, _column_width: float) -> None:
        """Add a new COLUMN to the grid with the given width."""
        self._column_widths.append(float(_column_width))

    def set_row_heights(self, _row_heights: Iterable[float]) -> None:
        """Set the row heights of the grid."""
        self._row_heights = []
        for height in _row_heights:
            self.add_new_row(height)

    def add_new_row(self, _row_height: float) -> None:
        """Add a new ROW to the grid with the given height. Will add a default column if none are set."""
        self._row_heights.append(float(_row_height))

    def get_cell(self, _column: int, _row: int) -> PhxLayerDivisionCell | None:
        """Get the PhxLayerDivisionCell at the given column and row position."""
        for cell in self._cells:
            if cell.column == _column and cell.row == _row:
                return cell
        return None

    def set_cell_material(self, _column_num: int, _row_num: int, _phx_material: PhxMaterial) -> None:
        """Set the PhxMaterial for a specific cell in the grid by its column/row position.

        Cells are indexed by their column and row position stating from top-left:

        |   | C0   | C1  | C2  | ...
        |---|------|-----|-----|----
        |R0 | 0,0  | 1,0 | 2,0 | ...
        |R1 | 0,1  | 1,1 | 2,1 | ...
        |R2 | 0,2  | 1,2 | 2,2 | ...
        """
        if _column_num >= self.column_count:
            raise IndexError(
                f"Column number '{_column_num}' is out of range."
                "Please set the columns before assigning division materials."
            )

        if _row_num >= self.row_count:
            raise IndexError(
                f"Row number '{_row_num}' is out of range." "Please set the rows before assigning division materials."
            )

        # -- See if the cell already exists, if so reset its material
        # -- if not, create a new cell.
        cell = self.get_cell(_column_num, _row_num)
        if cell:
            cell.material = _phx_material
        else:
            cell = PhxLayerDivisionCell(row=_row_num, column=_column_num, material=_phx_material)

        self._cells.append(cell)

    def get_cell_material(self, _column_num: int, _row_num: int) -> PhxMaterial | None:
        """Get the PhxMaterial for a specific cell in the grid by its column/row position."""
        for cell in self._cells:
            if cell.row == _row_num and cell.column == _column_num:
                return cell.material
        return None

    def get_cell_area(self, _column_num: int, _row_num) -> float:
        """Get the area of the cell (row-height * column-width)."""
        col_width = self.column_widths[_column_num]
        row_height = self.row_heights[_row_num]
        return col_width * row_height

    def get_base_material(self) -> PhxMaterial | None:
        """Get the 'base' material of the grid (the most common material in the layer, by cell-area)."""
        if not self._cells:
            return None

        material_areas = {}
        for cell in self._cells:
            cell_area = self.get_cell_area(cell.column, cell.row)
            if id(cell.material) not in material_areas:
                record = {"material": cell.material, "area": cell_area}
                material_areas[id(cell.material)] = record
            else:
                material_areas[id(cell.material)]["area"] += cell_area

        return max(material_areas.values(), key=lambda x: x["area"])["material"]

    def populate_defaults(self) -> None:
        """Populate the grid with default values. Ensure that there is at least one row or column."""
        if self.column_count > 0 and self.row_count == 0:
            self.add_new_row(1.0)
        elif self.row_count > 0 and self.column_count == 0:
            self.add_new_column(1.0)

    def __eq__(self, other: PhxLayerDivisionGrid) -> bool:
        return all(
            [
                self.row_heights == other.row_heights,
                self.column_widths == other.column_widths,
                self.cells == other.cells,
            ]
        )


@dataclass
class PhxLayer:
    """A single layer in a PhxConstructionOpaque assembly.

    A layer has a thickness and either a single homogeneous material or a division grid
    of multiple materials (for mixed/inhomogeneous layers such as stud cavities with
    insulation between framing members).

    Attributes:
        thickness_m (float): Layer thickness in meters. Default: 0.0.
        divisions (PhxLayerDivisionGrid): Grid of material subdivisions for mixed layers. Default: empty grid.
    """

    thickness_m: float = 0.0
    divisions: PhxLayerDivisionGrid = field(default_factory=PhxLayerDivisionGrid)
    _material: PhxMaterial = field(default_factory=PhxMaterial)

    def _update_material_percentages(self) -> None:
        """Update the percentage of the assembly for each material in the layer."""
        if self.divisions.cell_count == 0:
            return None

        material_areas = {}
        for row in range(self.divisions.row_count or 1):
            for column in range(self.divisions.column_count or 1):
                # -- Find the cell's area and material
                cell_area = self.divisions.get_cell_area(column, row)
                cell_material = self.divisions.get_cell_material(column, row) or self.material

                # -- Update the material area record
                if id(cell_material) not in material_areas:
                    record = {"material": cell_material, "area": cell_area}
                    material_areas[id(cell_material)] = record
                else:
                    material_areas[id(cell_material)]["area"] += cell_area

        # -- Re-set the percentage of the assembly for each material
        total_area = sum([record["area"] for record in material_areas.values()])
        for record in material_areas.values():
            record["material"].percentage_of_assembly = record["area"] / total_area

        return None

    @property
    def materials(self) -> list[PhxMaterial]:
        """Return a list of all the PhxMaterials in the Layer."""
        self._update_material_percentages()
        return [self.material] + self.exchange_materials

    @materials.setter
    def materials(self, _: PhxMaterial) -> None:
        msg = (
            "The 'materials' property is deprecated. Please use the 'set_material()' method or "
            "the 'divisions' attribute to setup mixed materials."
        )
        raise DeprecationWarning(msg)

    @property
    def material(self) -> PhxMaterial:
        """Return the base PhxMaterial of the Layer."""
        return self._material

    def add_material(self, _material: PhxMaterial) -> None:
        """Add a PhxMaterial to the self.materials collection."""
        self._material = _material
        msg = (
            "The 'add_material' method is deprecated. Please use the 'set_material()' method or "
            "the 'divisions' attribute for mixed materials."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=2)

    def set_material(self, _material: PhxMaterial) -> None:
        """Set the PhxMaterial for the layer."""
        self._material = _material

    @property
    def thickness_mm(self) -> float:
        """Returns the thickness of the layer in MM"""
        return self.thickness_m * 1000

    @classmethod
    def from_total_u_value(cls, _total_u_value: float) -> PhxLayer:
        """Returns a new PhxLayer with a single material with the given U-Value.
        note that this will assign a default thickness of 1m to the layer.
        """
        obj = cls()
        obj.thickness_m = 1

        new_mat = PhxMaterial()
        new_mat.conductivity = obj.thickness_m * _total_u_value
        new_mat.display_name = "Material"
        obj.set_material(new_mat)

        return obj

    @property
    def layer_resistance(self) -> float:
        """Returns the thermal-resistance of the layer in m2K/W"""
        try:
            return (1 / self.material.conductivity) * self.thickness_m
        except ZeroDivisionError:
            return 0.0

    @property
    def layer_conductance(self) -> float:
        """Returns the thermal-conductance of the layer in W/m2K"""
        try:
            return 1 / self.layer_resistance
        except ZeroDivisionError:
            return 0.0

    @property
    def division_materials(self) -> list[PhxMaterial]:
        """Returns a list of all the PhxLayerDivisionCell PhxMaterials ordered by column and then row:

        |    | C0  | C1  | C2  | ...
        |:---|:---:|:---:|:---:|:---:
        | R0 | 0   | 4   | 8   | ...
        | R1 | 1   | 5   | 9   | ...
        | R2 | 2   | 6   | 10  | ...
        | R3 | 3   | 7   | 11  | ...
        """
        if self.divisions.row_count == 0 and self.divisions.column_count == 0:
            return []

        return [
            self.divisions.get_cell_material(column, row) or self.material
            for column in range(self.divisions.column_count or 1)
            for row in range(self.divisions.row_count or 1)
        ]

    @property
    def exchange_materials(self) -> list[PhxMaterial]:
        """Returns a list of all the 'Exchange' materials (for mixed layers) in all the Division Cells."""
        seen: set[int] = set()
        result: list[PhxMaterial] = []
        for m in self.division_materials:
            if m != self.material and id(m) not in seen:
                seen.add(id(m))
                result.append(m)
        return result

    @property
    def division_material_id_numbers(self) -> list[int]:
        """Returns a list of all the 'Exchange' material id-numbers in all the Division Cells.

        Will return -1 if the cell has the Layer's Material.
        """
        id_numbers_ = []
        for m in self.division_materials:
            if m != self.material:
                id_numbers_.append(m.id_num)
            else:
                id_numbers_.append(-1)
        return id_numbers_

    def equivalent(self, other: PhxLayer) -> bool:
        """Check if two layers are equivalent."""

        # -- If it is a 'steel-stud' material, we can't check against the other.
        # -- When reading back in from WUFI, this information will be lost.
        if self.divisions and self.divisions.is_a_steel_stud_cavity:
            return all(
                [
                    self.thickness_m == other.thickness_m,
                    self.material.equivalent(other.material),
                    # No .division check
                ]
            )
        # -- Otherwise, check the thickness, material and divisions
        return all(
            [
                self.thickness_m == other.thickness_m,
                self.material.equivalent(other.material),
                self.divisions == other.divisions,
            ]
        )


# -----------------------------------------------------------------------------
# Construction


@dataclass
class PhxConstructionOpaque:
    """An opaque assembly construction (wall, roof, or floor) composed of ordered material layers.

    Layers are stacked from outside to inside by default. The assembly's U-value and R-value
    are computed from the constituent layers and their heat-flow pathways (accounting for
    mixed/inhomogeneous layers).

    Attributes:
        id_num (int): Auto-incremented identifier.
        display_name (str): Human-readable construction name. Default: "".
        layer_order (int): Layer stacking direction. Default: 2 (outside to inside).
        grid_kind (int): Grid resolution for mixed-material layers. Default: 2 (medium).
        layers (list[PhxLayer]): Ordered list of material layers in the assembly. Default: [].
    """

    _count: ClassVar[int] = 0

    _identifier: uuid.UUID | str = field(init=False, default_factory=uuid.uuid4)
    id_num: int = field(init=False, default=0)
    display_name: str = ""
    layer_order: int = 2  # Outside to Inside
    grid_kind: int = 2  # Medium
    layers: list[PhxLayer] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def identifier(self) -> str:
        return str(self._identifier)

    @identifier.setter
    def identifier(self, _in: str | None) -> None:
        if not _in:
            return
        self._identifier = str(_in)

    @property
    def heat_flow_pathways(self) -> list[PhxHeatFlowPathway]:
        """Return the unique heat-flow pathways through this assembly.

        Each pathway represents a vertical slice with a unique material sequence
        across all layers. See :mod:`PHX.model.assembly_pathways` for details.
        """

        return identify_heat_flow_pathways(self.layers)

    @property
    def r_value(self) -> float:
        """Total thermal resistance of the assembly in m2K/W, computed from heat-flow pathways."""
        if not self.layers:
            return 0.0

        pathways = self.heat_flow_pathways
        if not pathways:
            return 0.0

        from PHX.model.assembly_pathways import compute_r_value_from_pathways

        return compute_r_value_from_pathways(pathways, self.layers)

    @property
    def u_value(self) -> float:
        """Total thermal transmittance (U-value) of the assembly in W/m2K."""
        try:
            return 1 / self.r_value
        except ZeroDivisionError:
            return 0.0

    def __hash__(self) -> int:
        return hash(self.identifier)

    @classmethod
    def from_total_u_value(cls, _total_u_value: float, _display_name: str = "") -> PhxConstructionOpaque:
        """Returns a new PhxConstructionOpaque with a single layer with the given U-Value."""
        obj = cls()
        obj.display_name = _display_name or f"U-Value: {_total_u_value}"
        obj.layers.append(PhxLayer.from_total_u_value(_total_u_value))
        return obj

    @property
    def exchange_materials(self) -> list[PhxMaterial]:
        """Returns a flat list of all the 'Exchange' materials (for mixed layers) from all the Layers."""
        return [material for layer in self.layers for material in layer.exchange_materials]


# -----------------------------------------------------------------------------
# Windows


@dataclass
class PhxWindowFrameElement:
    """A single frame edge element (top, bottom, left, or right) of a window construction.

    Stores the frame width, U-value, and psi-values for the glazing-edge and installation
    thermal bridges along this frame edge.

    Attributes:
        width (float): Frame face width in meters. Default: 0.1.
        u_value (float): Frame thermal transmittance in W/m2K. Default: 1.0.
        psi_glazing (float): Linear thermal transmittance at the glazing-to-frame edge in W/mK. Default: 0.0.
        psi_install (float): Linear thermal transmittance at the frame-to-wall installation edge in W/mK. Default: 0.0.
    """

    width: float = 0.1  # m
    u_value: float = 1.0  # W/m2k
    psi_glazing: float = 0.00  # W/mk
    psi_install: float = 0.00  # W/mk

    @classmethod
    def from_total_u_value(cls, _total_u_value: float) -> PhxWindowFrameElement:
        """Returns a new PhxWindowFrameElement with u-values set to a single value."""
        obj = cls()
        obj.width = 0.1  # m
        obj.u_value = _total_u_value
        obj.psi_glazing = 0.0
        obj.psi_install = 0.0
        return obj


@dataclass
class PhxConstructionWindow:
    """A window construction defining glazing, frame, and overall thermal properties.

    Supports both simplified (single U-value) and detailed (per-edge frame elements with
    psi-values) window modeling. Frame elements are defined for each edge: top, right,
    bottom, left. The glass g-value (SHGC) and emissivity characterize solar and
    radiative performance.

    Attributes:
        id_num (int): Auto-incremented identifier.
        display_name (str): Human-readable window type name. Default: "".
        use_detailed_uw (bool): If True, compute Uw from component values rather than using a single input. Default: True.
        use_detailed_frame (bool): If True, use per-edge frame elements. Default: True.
        u_value_window (float): Overall window U-value (Uw) in W/m2K. Default: 1.0.
        u_value_glass (float): Center-of-glass U-value (Ug) in W/m2K. Default: 1.0.
        u_value_frame (float): Frame U-value (Uf) in W/m2K. Default: 1.0.
        frame_top (PhxWindowFrameElement): Top frame edge element. Default: PhxWindowFrameElement().
        frame_right (PhxWindowFrameElement): Right frame edge element. Default: PhxWindowFrameElement().
        frame_bottom (PhxWindowFrameElement): Bottom frame edge element. Default: PhxWindowFrameElement().
        frame_left (PhxWindowFrameElement): Left frame edge element. Default: PhxWindowFrameElement().
        frame_factor (float): Glazing fraction (glass area / total window area). Default: 0.75.
        glass_mean_emissivity (float): Mean emissivity of the glazing unit. Default: 0.1.
        glass_g_value (float): Solar heat gain coefficient (SHGC / g-value) of the glazing. Default: 0.4.
    """

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    _identifier: uuid.UUID | str = field(init=False, default_factory=uuid.uuid4)
    display_name: str = ""
    _glazing_type_display_name: str = ""
    _frame_type_display_name: str = ""

    use_detailed_uw: bool = True
    use_detailed_frame: bool = True

    u_value_window: float = 1.0
    u_value_glass: float = 1.0
    u_value_frame: float = 1.0

    frame_top: PhxWindowFrameElement = field(default_factory=PhxWindowFrameElement)
    frame_right: PhxWindowFrameElement = field(default_factory=PhxWindowFrameElement)
    frame_bottom: PhxWindowFrameElement = field(default_factory=PhxWindowFrameElement)
    frame_left: PhxWindowFrameElement = field(default_factory=PhxWindowFrameElement)
    frame_factor: float = 0.75

    glass_mean_emissivity: float = 0.1
    glass_g_value: float = 0.4

    _id_num_shade: int = -1

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def glazing_type_display_name(self) -> str:
        return self._glazing_type_display_name or self.display_name

    @glazing_type_display_name.setter
    def glazing_type_display_name(self, _in: str) -> None:
        self._glazing_type_display_name = _in

    @property
    def frame_type_display_name(self) -> str:
        return self._frame_type_display_name or self.display_name

    @frame_type_display_name.setter
    def frame_type_display_name(self, _in: str) -> None:
        self._frame_type_display_name = _in

    @property
    def identifier(self) -> str:
        return str(self._identifier)

    @identifier.setter
    def identifier(self, _in: str) -> None:
        if not _in:
            return
        self._identifier = str(_in)

    @property
    def id_num_shade(self) -> int:
        return self._id_num_shade

    @id_num_shade.setter
    def id_num_shade(self, _in: int | None) -> None:
        if _in is not None:
            self._id_num_shade = _in

    @classmethod
    def from_total_u_value(
        cls, _total_u_value: float, _g_value: float = 0.4, _display_name: str = ""
    ) -> PhxConstructionWindow:
        """Returns a new PhxConstructionWindow with all u-values set to a single value."""
        obj = cls()
        obj.display_name = _display_name or f"U-Value: {_total_u_value}"
        obj.frame_type_display_name = _display_name or f"U-Value: {_total_u_value}"
        obj.glazing_type_display_name = _display_name or f"U-Value: {_total_u_value}"

        obj.u_value_window = _total_u_value
        obj.u_value_glass = _total_u_value
        obj.u_value_frame = _total_u_value

        obj.glass_g_value = _g_value

        obj.frame_top = PhxWindowFrameElement.from_total_u_value(_total_u_value)
        obj.frame_right = PhxWindowFrameElement.from_total_u_value(_total_u_value)
        obj.frame_bottom = PhxWindowFrameElement.from_total_u_value(_total_u_value)
        obj.frame_left = PhxWindowFrameElement.from_total_u_value(_total_u_value)

        return obj

    @property
    def frames(self) -> Generator[PhxWindowFrameElement, None, None]:
        """Returns a generator of all frame elements in order: Top, Right, Bottom, Left."""
        yield from (
            self.frame_top,
            self.frame_right,
            self.frame_bottom,
            self.frame_left,
        )

    def set_all_frames_u_value(self, _u_value: float) -> None:
        """Sets the u-value of all frame elements to the given value."""
        for frame in self.frames:
            frame.u_value = _u_value

    def set_all_frames_width(self, _width: float) -> None:
        """Sets the width of all frame elements to the given value."""
        for frame in self.frames:
            frame.width = _width

    def set_all_frames_psi_glazing(self, _psi_glazing: float) -> None:
        """Sets the psi_glazing of all frame elements to the given value."""
        for frame in self.frames:
            frame.psi_glazing = _psi_glazing

    def set_all_frames_psi_install(self, _psi_install: float) -> None:
        """Sets the psi_install of all frame elements to the given value."""
        for frame in self.frames:
            frame.psi_install = _psi_install
