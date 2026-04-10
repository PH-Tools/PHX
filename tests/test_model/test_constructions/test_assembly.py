import pytest

from PHX.model import constructions
from tests.test_model.test_constructions.conftest import make_test_layer as _make_layer


def _add_stud_division(
    layer: constructions.PhxLayer, base_pct: float, stud_pct: float, stud_conductivity: float
) -> None:
    """Add a 2-column division grid to an existing layer."""
    stud_mat = constructions.PhxMaterial(display_name="Wood Coniferous (Softwood)")
    stud_mat.conductivity = stud_conductivity
    layer.divisions.set_column_widths([base_pct, stud_pct])
    layer.divisions.add_new_row(1.0)
    # Column 0 = base material (already set), Column 1 = stud
    layer.divisions.set_cell_material(1, 0, stud_mat)


def _build_w_ec_assembly() -> constructions.PhxConstructionOpaque:
    """Build the W-EC (Ext. Conditioned) assembly from the PHPP reference.

    PHPP reference: sec 1 = 90.6%, sec 2 = 9.4%. PHPP U-value: 0.1249 W/(m2K).
    Note: small discrepancy vs PHPP expected due to internal rounding in the
    PHPP spreadsheet. The parallel-path algorithm correctness is validated by
    the hand-calculated expected value in the test assertion.
    """
    sec_1_pct = 0.906
    sec_2_pct = 0.094
    stud_k = 0.140

    l1 = _make_layer(0.016, 0.130, "OSB")
    l2 = _make_layer(0.140, 0.040, "Cellulose (Denspack)")
    _add_stud_division(l2, sec_1_pct, sec_2_pct, stud_k)
    l3 = _make_layer(0.038, 0.040, "Cellulose (Denspack)")
    l4 = _make_layer(0.089, 0.040, "Cellulose (Denspack)")
    _add_stud_division(l4, sec_1_pct, sec_2_pct, stud_k)
    l5 = _make_layer(0.089, 0.034, "Roxul Comfortbatt 3.5in")
    _add_stud_division(l5, sec_1_pct, sec_2_pct, stud_k)
    l6 = _make_layer(0.013, 0.170, "GWB (Typ)")

    asm = constructions.PhxConstructionOpaque()
    asm.display_name = "W-EC (Ext. Conditioned)"
    asm.layers = [l1, l2, l3, l4, l5, l6]
    return asm


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------


def test_default_assembly(reset_class_counters) -> None:
    a1 = constructions.PhxConstructionOpaque()
    assert a1.id_num == 1
    a2 = constructions.PhxConstructionOpaque()
    assert a2.id_num == 2

    assert a1 != a2
    assert a1.identifier != a2.identifier
    assert not a1.layers
    assert not a2.layers
    assert not a1.exchange_materials
    assert a1.exchange_materials == a2.exchange_materials


def test_set_assembly_identifier(reset_class_counters) -> None:
    a1 = constructions.PhxConstructionOpaque()
    a2 = constructions.PhxConstructionOpaque()

    a1.identifier = "a_test"
    assert a1.identifier == "a_test"
    assert a1.identifier != a2.identifier
    assert not a1.exchange_materials

    a1.identifier = None
    assert a1.identifier == "a_test"
    assert a1.identifier != a2.identifier
    assert not a2.exchange_materials


def test_add_simple_layer_no_divisions(reset_class_counters) -> None:
    mat_1 = constructions.PhxMaterial(display_name="mat_1")
    layer_1 = constructions.PhxLayer()
    layer_1.set_material(mat_1)

    a1 = constructions.PhxConstructionOpaque()
    a1.layers.append(layer_1)
    assert len(a1.layers) == 1
    assert not a1.exchange_materials


def test_add_layer_with_multiple_columns(reset_class_counters) -> None:
    mat_1 = constructions.PhxMaterial(display_name="mat_1")
    mat_2 = constructions.PhxMaterial(display_name="mat_2")
    layer_1 = constructions.PhxLayer()
    layer_1.set_material(mat_1)
    layer_1.divisions.set_column_widths([1, 1])
    layer_1.divisions.add_new_row(1)
    layer_1.divisions.set_cell_material(1, 0, mat_2)

    # -- Construction
    a1 = constructions.PhxConstructionOpaque()
    a1.layers.append(layer_1)
    assert len(a1.layers) == 1
    assert a1.exchange_materials == [mat_2]

    # -- Add another column
    mat_3 = constructions.PhxMaterial(display_name="mat_3")
    layer_1.divisions.add_new_column(1)
    assert a1.exchange_materials == [mat_2]

    # -- Reset the material in the new column
    layer_1.divisions.set_cell_material(2, 0, mat_3)
    assert a1.exchange_materials == [mat_2, mat_3]


def test_multiple_layers_multiple_columns(reset_class_counters) -> None:
    # -- Multiple Columns
    mat_1 = constructions.PhxMaterial(display_name="mat_1")
    mat_2 = constructions.PhxMaterial(display_name="mat_2")
    layer_1 = constructions.PhxLayer()
    layer_1.set_material(mat_1)
    layer_1.divisions.set_column_widths([1, 1])
    layer_1.divisions.add_new_row(1)
    layer_1.divisions.set_cell_material(1, 0, mat_2)

    # -- Multiple Rows
    mat_3 = constructions.PhxMaterial(display_name="mat_3")
    mat_4 = constructions.PhxMaterial(display_name="mat_4")
    layer_2 = constructions.PhxLayer()
    layer_2.set_material(mat_3)
    layer_2.divisions.set_row_heights([1, 1])
    layer_2.divisions.add_new_column(1)
    layer_2.divisions.set_cell_material(0, 1, mat_4)

    # -- Construction
    a1 = constructions.PhxConstructionOpaque()
    a1.layers.append(layer_1)
    a1.layers.append(layer_2)

    assert len(a1.layers) == 2
    assert a1.exchange_materials == [mat_2, mat_4]


# ---------------------------------------------------------------------------
# R-value / U-value tests
# ---------------------------------------------------------------------------


def test_r_value_single_material_layers(reset_class_counters) -> None:
    """Regression: simple assembly r_value == sum of individual layer resistances."""
    l1 = _make_layer(0.100, 0.040, "Insulation")  # R = 0.100/0.040 = 2.5
    l2 = _make_layer(0.013, 0.170, "GWB")  # R = 0.013/0.170 ≈ 0.0765

    asm = constructions.PhxConstructionOpaque()
    asm.layers = [l1, l2]

    expected_r = l1.layer_resistance + l2.layer_resistance
    assert asm.r_value == pytest.approx(expected_r, abs=1e-10)


def test_u_value_single_material_layers(reset_class_counters) -> None:
    """Regression: u_value == 1 / r_value for simple assembly."""
    l1 = _make_layer(0.100, 0.040, "Insulation")
    l2 = _make_layer(0.013, 0.170, "GWB")

    asm = constructions.PhxConstructionOpaque()
    asm.layers = [l1, l2]

    assert asm.u_value == pytest.approx(1.0 / asm.r_value, abs=1e-10)


def test_u_value_w_ec_two_sections(reset_class_counters) -> None:
    """W-EC assembly with 90.6% insulation / 9.4% studs.

    PHPP reference U-value: 0.1249 W/(m2K).
    Hand-calculated parallel-path U-value from these exact inputs: ~0.1229.
    The small gap (~2%) is from PHPP internal rounding of layer values.
    """
    asm = _build_w_ec_assembly()

    # -- Must be significantly higher than single-section value (~0.1054)
    assert asm.u_value > 0.115

    # -- Hand-calculated: U = 0.906/R_sec1 + 0.094/R_sec2
    # R_sec1 = 9.4922, R_sec2 = 3.4210
    # U = 0.09547 + 0.02748 = 0.12295
    assert asm.u_value == pytest.approx(0.1229, abs=0.001)


def test_r_value_u_value_are_reciprocals(reset_class_counters) -> None:
    """For any assembly with non-zero r_value, r * u == 1."""
    asm = _build_w_ec_assembly()
    assert abs(asm.r_value * asm.u_value - 1.0) < 1e-10


def test_from_total_u_value_unchanged(reset_class_counters) -> None:
    """Regression: from_total_u_value factory should still produce correct values."""
    asm = constructions.PhxConstructionOpaque.from_total_u_value(0.5, "Test")
    assert asm.u_value == pytest.approx(0.5, abs=1e-10)
    assert asm.r_value == pytest.approx(2.0, abs=1e-10)


def test_empty_assembly(reset_class_counters) -> None:
    """No layers: r_value == 0.0, u_value == 0.0."""
    asm = constructions.PhxConstructionOpaque()
    assert asm.r_value == 0.0
    assert asm.u_value == 0.0


def test_heat_flow_pathways_property_uniform(reset_class_counters) -> None:
    """Uniform assembly exposes 1 pathway at 100%."""
    l1 = _make_layer(0.100, 0.040, "Insulation")
    l2 = _make_layer(0.013, 0.170, "GWB")

    asm = constructions.PhxConstructionOpaque()
    asm.layers = [l1, l2]

    pathways = asm.heat_flow_pathways
    assert len(pathways) == 1
    assert pathways[0].percentage == pytest.approx(1.0)


def test_r_value_single_pathway_non_base_divisions_take_precedence(reset_class_counters) -> None:
    """Collapsed one-pathway grids should compute R from division materials."""
    layer = _make_layer(0.100, 0.040, "Base Insulation")

    wood = constructions.PhxMaterial(display_name="Wood")
    wood.conductivity = 0.140

    layer.divisions.set_column_widths([0.60, 0.40])
    layer.divisions.add_new_row(1.0)
    layer.divisions.set_cell_material(0, 0, wood)
    layer.divisions.set_cell_material(1, 0, wood)

    asm = constructions.PhxConstructionOpaque()
    asm.layers = [layer]

    assert len(asm.heat_flow_pathways) == 1
    assert asm.heat_flow_pathways[0].materials == [wood]
    assert asm.r_value == pytest.approx(0.100 / 0.140, abs=1e-10)
    assert asm.u_value == pytest.approx(0.140 / 0.100, abs=1e-10)


def test_r_value_single_pathway_respects_divisions_across_multiple_layers(reset_class_counters) -> None:
    """Single-pathway assemblies use pathway materials in every layer."""
    wood = constructions.PhxMaterial(display_name="Wood")
    wood.conductivity = 0.140

    l1 = _make_layer(0.100, 0.040, "Base Insulation")
    l1.divisions.set_column_widths([1.0])
    l1.divisions.add_new_row(1.0)
    l1.divisions.set_cell_material(0, 0, wood)

    l2 = _make_layer(0.013, 0.170, "GWB")

    asm = constructions.PhxConstructionOpaque()
    asm.layers = [l1, l2]

    expected_r = 0.100 / 0.140 + 0.013 / 0.170
    assert len(asm.heat_flow_pathways) == 1
    assert asm.heat_flow_pathways[0].materials == [wood, l2.material]
    assert asm.r_value == pytest.approx(expected_r, abs=1e-10)
    assert asm.u_value == pytest.approx(1.0 / expected_r, abs=1e-10)


def test_heat_flow_pathways_property_w_ec(reset_class_counters) -> None:
    """W-EC assembly (all mixed layers same grid) → 2 pathways."""
    asm = _build_w_ec_assembly()
    pathways = asm.heat_flow_pathways
    assert len(pathways) == 2
    assert sum(p.percentage for p in pathways) == pytest.approx(1.0)


def test_u_value_tji_three_pathways(reset_class_counters) -> None:
    """TJI-style assembly with different grids in flange vs web layers → 3 pathways.

    Layer structure (outside to inside):
        L1: Plywood       12mm  k=0.13   (uniform)
        L2: Flange cavity  38mm  k=0.04   grid: 81.25% ins / 18.75% wood
        L3: Web cavity    200mm  k=0.04   grid: 90.625% ins / 9.375% wood
        L4: Flange cavity  38mm  k=0.04   grid: 81.25% ins / 18.75% wood
        L5: GWB            13mm  k=0.17   (uniform)

    Expected 3 pathways:
        A (81.250%): ins + ins + ins + ins + ins  → through cavity
        B ( 9.375%): ins + wood + ins + wood + ins → flange only
        C ( 9.375%): ins + wood + wood + wood + ins → through web
    """
    k_ins = 0.040
    k_wood = 0.140

    l1 = _make_layer(0.012, 0.130, "Plywood")
    l2 = _make_layer(0.038, k_ins, "Cellulose")
    _add_stud_division(l2, 0.8125, 0.1875, k_wood)
    l3 = _make_layer(0.200, k_ins, "Cellulose")
    _add_stud_division(l3, 0.90625, 0.09375, k_wood)
    l4 = _make_layer(0.038, k_ins, "Cellulose")
    _add_stud_division(l4, 0.8125, 0.1875, k_wood)
    l5 = _make_layer(0.013, 0.170, "GWB")

    asm = constructions.PhxConstructionOpaque()
    asm.display_name = "TJI Roof"
    asm.layers = [l1, l2, l3, l4, l5]

    # -- Verify 3 pathways
    pathways = asm.heat_flow_pathways
    assert len(pathways) == 3
    pcts = sorted([p.percentage for p in pathways], reverse=True)
    assert pcts[0] == pytest.approx(0.8125)
    assert pcts[1] == pytest.approx(0.09375)
    assert pcts[2] == pytest.approx(0.09375)

    # -- Hand-calculated R-values per pathway
    r_plywood = 0.012 / 0.130
    r_gwb = 0.013 / 0.170

    r_a = r_plywood + 0.038 / k_ins + 0.200 / k_ins + 0.038 / k_ins + r_gwb
    r_b = r_plywood + 0.038 / k_wood + 0.200 / k_ins + 0.038 / k_wood + r_gwb
    r_c = r_plywood + 0.038 / k_wood + 0.200 / k_wood + 0.038 / k_wood + r_gwb

    expected_r = 1.0 / (0.8125 / r_a + 0.09375 / r_b + 0.09375 / r_c)

    assert asm.r_value == pytest.approx(expected_r, abs=1e-8)
    assert asm.u_value == pytest.approx(1.0 / expected_r, abs=1e-8)


def test_section_fallback_to_base_material(reset_class_counters) -> None:
    """Layer 1 has divisions (2 sections), layer 2 doesn't.

    Section 2 should use layer 2's base material for its R-value path.
    """
    # Layer 1: 100mm insulation (k=0.040) with 50% studs (k=0.140)
    l1 = _make_layer(0.100, 0.040, "Insulation")
    _add_stud_division(l1, 0.50, 0.50, 0.140)

    # Layer 2: 13mm GWB (k=0.170), no divisions
    l2 = _make_layer(0.013, 0.170, "GWB")

    asm = constructions.PhxConstructionOpaque()
    asm.layers = [l1, l2]

    # Section 1 (insulation path): R = 0.100/0.040 + 0.013/0.170
    r_sec1 = 0.100 / 0.040 + 0.013 / 0.170
    # Section 2 (stud path): R = 0.100/0.140 + 0.013/0.170 (uses GWB base mat)
    r_sec2 = 0.100 / 0.140 + 0.013 / 0.170

    expected_u = 0.50 / r_sec1 + 0.50 / r_sec2
    assert asm.u_value == pytest.approx(expected_u, abs=1e-6)
