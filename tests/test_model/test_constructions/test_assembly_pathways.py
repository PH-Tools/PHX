# -*- Python Version: 3.10 -*-

"""Tests for PHX.model.assembly_pathways — heat-flow pathway identification."""

import pytest

from PHX.model.constructions import PhxLayer, PhxMaterial
from tests.test_model.test_constructions.conftest import make_test_layer as _make_layer


def _add_grid(layer: PhxLayer, col_widths: list[float], col_materials: list[PhxMaterial | None]) -> None:
    """Add a single-row division grid to a layer.

    col_materials entries of None use the layer's base material for that column.
    """
    layer.divisions.set_column_widths(col_widths)
    layer.divisions.add_new_row(1.0)
    for col_idx, mat in enumerate(col_materials):
        if mat is not None:
            layer.divisions.set_cell_material(col_idx, 0, mat)


# ===========================================================================
# _cumulative_boundaries
# ===========================================================================


class TestCumulativeBoundaries:
    def test_empty_widths(self) -> None:
        from PHX.model.assembly_pathways import _cumulative_boundaries

        assert _cumulative_boundaries([]) == [0.0]

    def test_single_column(self) -> None:
        from PHX.model.assembly_pathways import _cumulative_boundaries

        result = _cumulative_boundaries([1.0])
        assert result == pytest.approx([0.0, 1.0])

    def test_multiple_columns(self) -> None:
        from PHX.model.assembly_pathways import _cumulative_boundaries

        result = _cumulative_boundaries([0.25, 0.50, 0.25])
        assert result == pytest.approx([0.0, 0.25, 0.75, 1.0])

    def test_non_normalized_widths(self) -> None:
        """Widths that don't sum to 1.0 are normalized so last boundary == 1.0."""
        from PHX.model.assembly_pathways import _cumulative_boundaries

        result = _cumulative_boundaries([2.0, 3.0, 5.0])  # sum = 10
        assert result == pytest.approx([0.0, 0.2, 0.5, 1.0])

    def test_seven_column_rafter_grid(self) -> None:
        """Real-world: 7-column rafter grid from linde_home R-VT."""
        from PHX.model.assembly_pathways import _cumulative_boundaries

        widths = [0.165, 0.038, 0.038, 0.330, 0.038, 0.038, 0.165]
        total = sum(widths)  # 0.812
        result = _cumulative_boundaries(widths)
        assert len(result) == 8
        assert result[0] == pytest.approx(0.0)
        assert result[-1] == pytest.approx(1.0)
        # Check a couple of interior boundaries
        assert result[1] == pytest.approx(0.165 / total)


# ===========================================================================
# _merged_boundaries
# ===========================================================================


class TestMergedBoundaries:
    def test_no_layers(self) -> None:
        from PHX.model.assembly_pathways import _merged_boundaries

        assert _merged_boundaries([]) == pytest.approx([0.0, 1.0])

    def test_all_uniform_layers(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import _merged_boundaries

        layers = [_make_layer(0.1, 0.04), _make_layer(0.013, 0.17)]
        assert _merged_boundaries(layers) == pytest.approx([0.0, 1.0])

    def test_single_grid_layer(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import _merged_boundaries

        layer = _make_layer(0.1, 0.04)
        stud = PhxMaterial(display_name="wood")
        stud.conductivity = 0.14
        _add_grid(layer, [0.75, 0.25], [None, stud])

        result = _merged_boundaries([layer])
        assert result == pytest.approx([0.0, 0.75, 1.0])

    def test_identical_grids_no_duplication(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import _merged_boundaries

        stud1 = PhxMaterial(display_name="wood")
        stud1.conductivity = 0.14
        stud2 = PhxMaterial(display_name="wood")
        stud2.conductivity = 0.14

        l1 = _make_layer(0.1, 0.04)
        _add_grid(l1, [0.75, 0.25], [None, stud1])
        l2 = _make_layer(0.089, 0.04)
        _add_grid(l2, [0.75, 0.25], [None, stud2])

        result = _merged_boundaries([l1, l2])
        assert result == pytest.approx([0.0, 0.75, 1.0])

    def test_different_grids_merged(self, reset_class_counters) -> None:
        """Two layers with different grids produce union of boundaries."""
        from PHX.model.assembly_pathways import _merged_boundaries

        stud1 = PhxMaterial(display_name="wood")
        stud1.conductivity = 0.14
        stud2 = PhxMaterial(display_name="wood")
        stud2.conductivity = 0.14

        # Layer 1: 50/50 split
        l1 = _make_layer(0.1, 0.04)
        _add_grid(l1, [0.50, 0.50], [None, stud1])

        # Layer 2: 75/25 split
        l2 = _make_layer(0.089, 0.034)
        _add_grid(l2, [0.75, 0.25], [None, stud2])

        result = _merged_boundaries([l1, l2])
        # Union: {0.0, 0.5, 1.0} ∪ {0.0, 0.75, 1.0} = {0.0, 0.5, 0.75, 1.0}
        assert result == pytest.approx([0.0, 0.5, 0.75, 1.0])


# ===========================================================================
# _material_at_position
# ===========================================================================


class TestMaterialAtPosition:
    def test_uniform_layer(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import _material_at_position

        layer = _make_layer(0.1, 0.04, "Insulation")
        assert _material_at_position(layer, 0.0) is layer.material
        assert _material_at_position(layer, 0.5) is layer.material
        assert _material_at_position(layer, 0.99) is layer.material

    def test_two_column_grid(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import _material_at_position

        layer = _make_layer(0.1, 0.04, "Insulation")
        stud = PhxMaterial(display_name="wood")
        stud.conductivity = 0.14
        _add_grid(layer, [0.75, 0.25], [None, stud])

        # Midpoint of first sub-column (0.0–0.75): position=0.375 → base material
        assert _material_at_position(layer, 0.375) is layer.material
        # Midpoint of second sub-column (0.75–1.0): position=0.875 → stud
        assert _material_at_position(layer, 0.875) is stud

    def test_three_column_grid(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import _material_at_position

        layer = _make_layer(0.1, 0.04, "Insulation")
        wood = PhxMaterial(display_name="wood")
        wood.conductivity = 0.14
        steel = PhxMaterial(display_name="steel")
        steel.conductivity = 50.0
        _add_grid(layer, [0.40, 0.20, 0.40], [None, wood, steel])

        assert _material_at_position(layer, 0.2) is layer.material  # col 0
        assert _material_at_position(layer, 0.5) is wood  # col 1
        assert _material_at_position(layer, 0.8) is steel  # col 2

    def test_position_on_boundary_goes_right(self, reset_class_counters) -> None:
        """Position exactly on a boundary should resolve to the column to the right."""
        from PHX.model.assembly_pathways import _material_at_position

        layer = _make_layer(0.1, 0.04, "Insulation")
        stud = PhxMaterial(display_name="wood")
        stud.conductivity = 0.14
        _add_grid(layer, [0.50, 0.50], [None, stud])

        # Position 0.5 is exactly on the boundary between col 0 and col 1
        assert _material_at_position(layer, 0.5) is stud


# ===========================================================================
# identify_heat_flow_pathways
# ===========================================================================


class TestIdentifyHeatFlowPathways:
    def test_empty_layers(self) -> None:
        from PHX.model.assembly_pathways import identify_heat_flow_pathways

        assert identify_heat_flow_pathways([]) == []

    def test_single_uniform_layer(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import identify_heat_flow_pathways

        layer = _make_layer(0.1, 0.04, "Insulation")
        pathways = identify_heat_flow_pathways([layer])
        assert len(pathways) == 1
        assert pathways[0].percentage == pytest.approx(1.0)
        assert pathways[0].materials == [layer.material]

    def test_all_layers_same_grid_two_pathways(self, reset_class_counters) -> None:
        """All mixed layers share the same 75/25 grid → 2 pathways."""
        from PHX.model.assembly_pathways import identify_heat_flow_pathways

        stud1 = PhxMaterial(display_name="wood")
        stud1.conductivity = 0.14
        stud2 = PhxMaterial(display_name="wood")
        stud2.conductivity = 0.14

        l1 = _make_layer(0.1, 0.04, "Insulation")
        _add_grid(l1, [0.75, 0.25], [None, stud1])

        l2 = _make_layer(0.013, 0.17, "GWB")  # uniform

        l3 = _make_layer(0.089, 0.034, "Roxul")
        _add_grid(l3, [0.75, 0.25], [None, stud2])

        pathways = identify_heat_flow_pathways([l1, l2, l3])
        assert len(pathways) == 2

        pcts = sorted([p.percentage for p in pathways], reverse=True)
        assert pcts[0] == pytest.approx(0.75)
        assert pcts[1] == pytest.approx(0.25)

    def test_different_grids_three_pathways(self, reset_class_counters) -> None:
        """Two layers with different grids → 3 unique pathways."""
        from PHX.model.assembly_pathways import identify_heat_flow_pathways

        wood1 = PhxMaterial(display_name="wood")
        wood1.conductivity = 0.14
        wood2 = PhxMaterial(display_name="wood")
        wood2.conductivity = 0.14

        # Layer 1: 60/40 split (insulation / wood)
        l1 = _make_layer(0.1, 0.04, "Insulation")
        _add_grid(l1, [0.60, 0.40], [None, wood1])

        # Layer 2: 80/20 split (insulation / wood)
        l2 = _make_layer(0.089, 0.034, "Roxul")
        _add_grid(l2, [0.80, 0.20], [None, wood2])

        pathways = identify_heat_flow_pathways([l1, l2])
        assert len(pathways) == 3

        pcts = sorted([p.percentage for p in pathways], reverse=True)
        # Pathway A: insulation + insulation = 60% (L1 col0 ∩ L2 col0)
        # Pathway B: wood + insulation = 20% (L1 col1, L2 col0 still, since 0.60 < 0.80)
        # Pathway C: wood + wood = 20% (L1 col1, L2 col1)
        assert pcts[0] == pytest.approx(0.60)
        assert pcts[1] == pytest.approx(0.20)
        assert pcts[2] == pytest.approx(0.20)

    def test_mixed_uniform_and_grid(self, reset_class_counters) -> None:
        """Uniform layers use base material for all pathways."""
        from PHX.model.assembly_pathways import identify_heat_flow_pathways

        stud = PhxMaterial(display_name="wood")
        stud.conductivity = 0.14

        l1 = _make_layer(0.013, 0.17, "GWB")  # uniform
        l2 = _make_layer(0.1, 0.04, "Insulation")
        _add_grid(l2, [0.75, 0.25], [None, stud])

        pathways = identify_heat_flow_pathways([l1, l2])
        assert len(pathways) == 2

        # Both pathways use l1's base material for the first layer
        for p in pathways:
            assert p.materials[0] is l1.material

    def test_grid_all_same_material_collapses(self, reset_class_counters) -> None:
        """Grid where all cells are the same material → 1 pathway."""
        from PHX.model.assembly_pathways import identify_heat_flow_pathways

        layer = _make_layer(0.1, 0.04, "Insulation")
        # Grid with 2 columns, but both use the base material (None = base)
        _add_grid(layer, [0.60, 0.40], [None, None])

        pathways = identify_heat_flow_pathways([layer])
        assert len(pathways) == 1
        assert pathways[0].percentage == pytest.approx(1.0)

    def test_grid_all_same_non_base_material_collapses_to_division_material(self, reset_class_counters) -> None:
        """Collapsed pathways keep the division material, not the base material."""
        from PHX.model.assembly_pathways import identify_heat_flow_pathways

        layer = _make_layer(0.1, 0.04, "Base Insulation")
        wood = PhxMaterial(display_name="Wood")
        wood.conductivity = 0.14

        _add_grid(layer, [0.60, 0.40], [wood, wood])

        pathways = identify_heat_flow_pathways([layer])
        assert len(pathways) == 1
        assert pathways[0].percentage == pytest.approx(1.0)
        assert pathways[0].materials == [wood]

    def test_single_column_grid_uses_division_material(self, reset_class_counters) -> None:
        """A one-column grid still takes its material from the division cell."""
        from PHX.model.assembly_pathways import identify_heat_flow_pathways

        layer = _make_layer(0.1, 0.04, "Base Insulation")
        wood = PhxMaterial(display_name="Wood")
        wood.conductivity = 0.14

        _add_grid(layer, [1.0], [wood])

        pathways = identify_heat_flow_pathways([layer])
        assert len(pathways) == 1
        assert pathways[0].percentage == pytest.approx(1.0)
        assert pathways[0].materials == [wood]

    def test_percentages_sum_to_one(self, reset_class_counters) -> None:
        """Pathway percentages must sum to 1.0."""
        from PHX.model.assembly_pathways import identify_heat_flow_pathways

        wood1 = PhxMaterial(display_name="wood")
        wood1.conductivity = 0.14
        wood2 = PhxMaterial(display_name="wood")
        wood2.conductivity = 0.14

        l1 = _make_layer(0.1, 0.04, "Insulation")
        _add_grid(l1, [0.60, 0.40], [None, wood1])
        l2 = _make_layer(0.089, 0.034, "Roxul")
        _add_grid(l2, [0.80, 0.20], [None, wood2])

        pathways = identify_heat_flow_pathways([l1, l2])
        assert sum(p.percentage for p in pathways) == pytest.approx(1.0)


# ===========================================================================
# compute_r_value_from_pathways
# ===========================================================================


class TestComputeRValueFromPathways:
    def test_empty_pathways(self) -> None:
        from PHX.model.assembly_pathways import compute_r_value_from_pathways

        assert compute_r_value_from_pathways([], []) == 0.0

    def test_single_pathway(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import PhxHeatFlowPathway, compute_r_value_from_pathways

        l1 = _make_layer(0.1, 0.04, "Insulation")  # R = 2.5
        l2 = _make_layer(0.013, 0.17, "GWB")  # R ≈ 0.0765

        pathway = PhxHeatFlowPathway(
            materials=[l1.material, l2.material],
            percentage=1.0,
        )
        result = compute_r_value_from_pathways([pathway], [l1, l2])
        expected = 0.1 / 0.04 + 0.013 / 0.17
        assert result == pytest.approx(expected, abs=1e-10)

    def test_two_pathways(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import PhxHeatFlowPathway, compute_r_value_from_pathways

        insulation = PhxMaterial(display_name="Insulation")
        insulation.conductivity = 0.04
        wood = PhxMaterial(display_name="Wood")
        wood.conductivity = 0.14
        gwb = PhxMaterial(display_name="GWB")
        gwb.conductivity = 0.17

        l1 = _make_layer(0.1, 0.04)
        l1.set_material(insulation)
        l2 = _make_layer(0.013, 0.17)
        l2.set_material(gwb)

        p1 = PhxHeatFlowPathway(materials=[insulation, gwb], percentage=0.75)
        p2 = PhxHeatFlowPathway(materials=[wood, gwb], percentage=0.25)

        result = compute_r_value_from_pathways([p1, p2], [l1, l2])

        r1 = 0.1 / 0.04 + 0.013 / 0.17
        r2 = 0.1 / 0.14 + 0.013 / 0.17
        expected = 1.0 / (0.75 / r1 + 0.25 / r2)
        assert result == pytest.approx(expected, abs=1e-10)

    def test_zero_conductivity_handled(self, reset_class_counters) -> None:
        from PHX.model.assembly_pathways import PhxHeatFlowPathway, compute_r_value_from_pathways

        mat_zero = PhxMaterial(display_name="Zero")
        mat_zero.conductivity = 0.0
        mat_normal = PhxMaterial(display_name="Normal")
        mat_normal.conductivity = 0.04

        l1 = _make_layer(0.1, 0.0)
        l1.set_material(mat_zero)
        l2 = _make_layer(0.013, 0.04)
        l2.set_material(mat_normal)

        pathway = PhxHeatFlowPathway(
            materials=[mat_zero, mat_normal],
            percentage=1.0,
        )
        # Should not raise — zero conductivity layer is skipped
        result = compute_r_value_from_pathways([pathway], [l1, l2])
        # Only l2 contributes: R = 0.013 / 0.04 = 0.325
        assert result == pytest.approx(0.013 / 0.04, abs=1e-10)
