# -*- Python Version: 3.10 -*-

"""Heat-flow pathway identification for opaque assemblies (ISO 6946 upper-bound method).

When an assembly has layers with different division grids (e.g., rafter layers at one
framing fraction and a service cavity at another), the intersection of those grids creates
multiple unique heat-flow pathways. Each pathway is a vertical slice through the assembly
where every layer contributes a specific material.

This module provides:
- `identify_heat_flow_pathways` — analyze layers to find unique pathways + percentages
- `compute_r_value_from_pathways` — ISO 6946 upper-bound R from pathway data
- `PhxHeatFlowPathway` — lightweight container for one pathway's materials + percentage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PHX.model.constructions import PhxLayer, PhxMaterial


@dataclass
class PhxHeatFlowPathway:
    """A single vertical heat-flow pathway through an opaque assembly.

    Represents one unique material-sequence slice through a multi-layer construction,
    as identified by the ISO 6946 upper-bound method. Each pathway has an ordered list
    of materials (one per layer) and a percentage of the total assembly width it occupies.

    Attributes:
        materials (list[PhxMaterial]): Ordered list of PhxMaterial references, one per layer
            (same order as PhxConstructionOpaque.layers). Default: [].
        percentage (float): Fraction of the total assembly width occupied by this pathway
            (0.0-1.0). Default: 0.0.
    """

    materials: list[PhxMaterial] = field(default_factory=list)
    percentage: float = 0.0


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _cumulative_boundaries(column_widths: list[float]) -> list[float]:
    """Convert proportional column widths to normalized cumulative boundary positions.

    Example: [0.165, 0.038, 0.330] → [0.0, 0.31, 0.381, 1.0] (normalized so last == 1.0).
    Returns [0.0] for an empty list.
    """
    if not column_widths:
        return [0.0]

    total = sum(column_widths)
    if total == 0:
        return [0.0]

    boundaries = [0.0]
    cumulative = 0.0
    for w in column_widths:
        cumulative += w / total
        boundaries.append(cumulative)

    # Force last boundary to exactly 1.0 to avoid floating-point drift.
    boundaries[-1] = 1.0
    return boundaries


def _merged_boundaries(layers: list[PhxLayer]) -> list[float]:
    """Build the combined column grid from all layers' division grids.

    Takes the union of cumulative boundary positions from every layer that
    has a division grid. Returns sorted, deduplicated boundary positions.
    Returns [0.0, 1.0] if no layers have grids.
    """
    all_boundaries: set[float] = {0.0, 1.0}

    for layer in layers:
        if layer.divisions.column_count == 0:
            continue
        for b in _cumulative_boundaries(layer.divisions.column_widths):
            # Deduplicate within tolerance.
            if not any(abs(b - existing) < 1e-10 for existing in all_boundaries):
                all_boundaries.add(b)

    return sorted(all_boundaries)


def _material_at_position(layer: PhxLayer, position: float, boundaries: list[float] | None = None) -> PhxMaterial:
    """Return the material in a layer at a given normalized position (0.0–1.0).

    For uniform layers (no division grid): returns the base material.
    For grid layers: finds which original column contains *position* and returns
    that cell's material (row 0).

    Pass pre-computed *boundaries* to avoid recomputing them on every call.
    """
    if layer.divisions.column_count == 0:
        return layer.material

    if boundaries is None:
        boundaries = _cumulative_boundaries(layer.divisions.column_widths)

    # Find which column contains this position.
    for col_idx in range(len(boundaries) - 1):
        left = boundaries[col_idx]
        right = boundaries[col_idx + 1]
        if left <= position < right:
            return layer.divisions.get_cell_material(col_idx, 0) or layer.material

    # Position == 1.0 (or very close): belongs to the last column.
    last_col = layer.divisions.column_count - 1
    return layer.divisions.get_cell_material(last_col, 0) or layer.material


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def identify_heat_flow_pathways(layers: list[PhxLayer]) -> list[PhxHeatFlowPathway]:
    """Identify unique heat-flow pathways through a stack of assembly layers.

    Builds a merged column grid from all layers' division grids, then walks each
    sub-column to determine its material sequence. Slices with identical material
    sequences are merged and their widths summed into a single pathway.

    Arguments:
    ----------
        * layers (list[PhxLayer]): The ordered layer stack of an opaque construction.

    Returns:
    --------
        * list[PhxHeatFlowPathway]: Unique pathways sorted by descending percentage.
            Empty list for empty input.
    """
    if not layers:
        return []

    boundaries = _merged_boundaries(layers)

    # -- Precompute per-layer cumulative boundaries to avoid redundant recalculation.
    layer_boundaries: dict[int, list[float] | None] = {}
    for layer in layers:
        if layer.divisions.column_count > 0:
            layer_boundaries[id(layer)] = _cumulative_boundaries(layer.divisions.column_widths)
        else:
            layer_boundaries[id(layer)] = None

    # -- For each sub-column, determine the material sequence and width.
    pathway_groups: dict[tuple[int, ...], float] = {}
    pathway_materials: dict[tuple[int, ...], list[PhxMaterial]] = {}

    for i in range(len(boundaries) - 1):
        left = boundaries[i]
        right = boundaries[i + 1]
        midpoint = (left + right) / 2.0
        width = right - left

        mat_sequence: list[PhxMaterial] = []
        mat_key: list[int] = []
        for layer in layers:
            mat = _material_at_position(layer, midpoint, layer_boundaries[id(layer)])
            mat_sequence.append(mat)
            mat_key.append(mat.id_num)

        key = tuple(mat_key)
        pathway_groups[key] = pathway_groups.get(key, 0.0) + width
        if key not in pathway_materials:
            pathway_materials[key] = mat_sequence

    # -- Build result, sorted by descending percentage.
    result = [
        PhxHeatFlowPathway(materials=pathway_materials[key], percentage=pct) for key, pct in pathway_groups.items()
    ]
    result.sort(key=lambda p: p.percentage, reverse=True)
    return result


def compute_r_value_from_pathways(pathways: list[PhxHeatFlowPathway], layers: list[PhxLayer]) -> float:
    """Compute ISO 6946 upper-bound R-value from identified heat-flow pathways.

    For each pathway: R_i = sum(thickness / conductivity) across all layers.
    Upper-bound R-value: R = 1 / sum(pct_i / R_i). Layers with zero conductivity
    are skipped.

    Arguments:
    ----------
        * pathways (list[PhxHeatFlowPathway]): The unique pathways identified by
            identify_heat_flow_pathways().
        * layers (list[PhxLayer]): The ordered layer stack (must match the layer
            order used when identifying pathways).

    Returns:
    --------
        * float: The ISO 6946 upper-bound R-value [m2K/W]. Returns 0.0 for empty input.
    """
    if not pathways or not layers:
        return 0.0

    u_parallel = 0.0
    for pathway in pathways:
        total_r = 0.0
        for layer, mat in zip(layers, pathway.materials, strict=True):
            try:
                total_r += layer.thickness_m / mat.conductivity
            except ZeroDivisionError:
                pass
        if total_r > 0:
            u_parallel += pathway.percentage / total_r

    try:
        return 1.0 / u_parallel
    except ZeroDivisionError:
        return 0.0
