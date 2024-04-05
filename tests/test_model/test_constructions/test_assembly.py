from PHX.model import constructions


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
