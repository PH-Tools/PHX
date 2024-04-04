import pytest
from PHX.model.constructions import PhxLayer, PhxMaterial, PhxLayerDivisionGrid


# ---- DivisionGrid Columns and Rows ----------------------------


def test_empty_PhxLayerDivisionGrid(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    assert grid.cell_count == 0
    assert grid.column_count == 0
    assert grid.row_count == 0


def  test_add_single_column_to_grid(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    grid.add_new_column(1)
    assert grid.cell_count == 1
    assert grid.column_count == 1
    assert grid.row_count == 1


def test_add_multiple_columns_to_grid(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    grid.add_new_column(1)
    grid.add_new_column(1)
    assert grid.cell_count == 2
    assert grid.column_count == 2
    assert grid.row_count == 1


def test_set_multiple_columns_to_grid(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    grid.set_column_widths([0.1, 0.2])
    assert grid.cell_count == 2
    assert grid.column_count == 2
    assert grid.row_count == 1


def test_add_single_row_to_grid(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    grid.add_new_row(1)
    assert grid.cell_count == 1
    assert grid.column_count == 1
    assert grid.row_count == 1


def test_add_multiple_rows_to_grid(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    grid.add_new_row(1)
    grid.add_new_row(1)
    assert grid.cell_count == 2
    assert grid.column_count == 1
    assert grid.row_count == 2


def test_set_multiple_rows_to_grid(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    grid.set_row_heights([0.1, 0.2])
    assert grid.cell_count == 2
    assert grid.column_count == 1
    assert grid.row_count == 2


def test_set_multiple_rows_and_columns_to_grid(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    grid.set_column_widths([0.1, 0.2])
    grid.set_row_heights([0.1, 0.2])
    assert grid.cell_count == 4
    assert grid.column_count == 2
    assert grid.row_count == 2


# --- DivisionGrid Material Setting ------------------------------

def test_set_material_on_single_cell_grid_works(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    grid.add_new_column(1)
    assert grid.cell_count == 1
    assert grid.column_count == 1
    assert grid.row_count == 1

    grid.set_cell_material(0, 0, PhxMaterial())


def test_set_material_on_grid_raises_ValueError(reset_class_counters) -> None:
    grid = PhxLayerDivisionGrid()
    grid.add_new_column(1)
    assert grid.cell_count == 1
    assert grid.column_count == 1
    assert grid.row_count == 1

    with pytest.raises(IndexError):
        grid.set_cell_material(2, 0, PhxMaterial()) # out of bounds
    

def test_add_single_column(reset_class_counters) -> None:
    layer = PhxLayer()
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.add_material(mat_1)
    assert len(layer.division_materials) == 0

    layer.divisions.add_new_column(1)
    assert len(layer.division_materials) == 1 # sets the first column

    # -- Have not set anything, so should all be Layer's Material
    for mat in layer.division_materials:
        assert mat == layer.material


def test_add_single_row(reset_class_counters) -> None:
    layer = PhxLayer()
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.add_material(mat_1)
    assert len(layer.division_materials) == 0

    layer.divisions.add_new_row(1)
    assert len(layer.division_materials) == 1 # sets the first row

    # -- Have not set anything, so should all be Layer's Material
    for mat in layer.division_materials:
        assert mat == layer.material


def test_add_multiple_columns(reset_class_counters) -> None:
    layer = PhxLayer()    
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.add_material(mat_1)
    assert len(layer.division_materials) == 0 

    # -- Add some new columns
    layer.divisions.add_new_column(1)
    layer.divisions.add_new_column(2)
    assert len(layer.division_materials) == 2

    # -- Have not set anything, so should all be Layer's Material
    for mat in layer.division_materials:
        assert mat == layer.material


def test_multiple_rows(reset_class_counters) -> None:
    layer = PhxLayer()
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.add_material(mat_1)
    assert len(layer.division_materials) == 0 

    # -- Add some new columns
    layer.divisions.add_new_row(1)
    layer.divisions.add_new_row(2)
    assert len(layer.division_materials) == 2

    # -- Have not set anything, so should all be Layer's Material
    for mat in layer.division_materials:
        assert mat == layer.material


def test_simple_set_material_multiple_columns(reset_class_counters) -> None:
    mat_1 = PhxMaterial(display_name="mat_1")
    mat_2 = PhxMaterial(display_name="mat_2")
    mat_3 = PhxMaterial(display_name="mat_3")
    
    layer = PhxLayer()
    layer.add_material(mat_1)
    layer.divisions.set_column_widths([0.1, 0.2])
    layer.divisions.set_row_heights([1, 1])
    assert layer.divisions.row_count == 2
    assert layer.divisions.column_count == 2

    layer.divisions.set_cell_material(0, 0, mat_2)
    layer.divisions.set_cell_material(1, 0, mat_3)
    
    assert layer.divisions.get_cell_material(0, 0) == mat_2
    assert layer.divisions.get_cell_material(0, 1) == None
    assert layer.divisions.get_cell_material(1, 0) == mat_3
    assert layer.divisions.get_cell_material(1, 1) == None


def test_reset_material_multiple_columns(reset_class_counters) -> None:
    mat_1 = PhxMaterial(display_name="mat_1")
    mat_2 = PhxMaterial(display_name="mat_2")
    mat_3 = PhxMaterial(display_name="mat_3")
    
    layer = PhxLayer()
    layer.add_material(mat_1)
    layer.divisions.set_column_widths([0.1, 0.2])
    layer.divisions.set_row_heights([1, 1])
    assert layer.divisions.row_count == 2
    assert layer.divisions.column_count == 2

    layer.divisions.set_cell_material(0, 0, mat_2)
    assert layer.divisions.get_cell_material(0, 0) == mat_2

    # Reset an existing cell
    mat_4 = PhxMaterial(display_name="mat_4")
    layer.divisions.set_cell_material(0, 0, mat_4)
    assert layer.divisions.get_cell_material(0, 0) == mat_4
    assert layer.divisions.row_count == 2
    assert layer.divisions.column_count == 2


# -- Exchange Materials ------------------------------------------


def test_no_exchange_materials(reset_class_counters) -> None:
    layer = PhxLayer()
    assert len(layer.division_materials) == 0
    assert len(layer.exchange_materials) == 0
    assert layer.division_material_id_numbers == []


def test_one_column_exchange_material(reset_class_counters) -> None:
    layer = PhxLayer()
    mat_0 = PhxMaterial(display_name="mat_1")
    layer.add_material(mat_0)
    layer.divisions.set_column_widths([1, 1])
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.divisions.set_cell_material(0, 0, mat_1)
    
    """
    layer.division_materials = [
        0: mat_1,
        1: Layer's Material,
    ]
    """
    
    assert len(layer.division_materials) == 2
    assert len(layer.exchange_materials) == 1
    assert layer.division_material_id_numbers == [2, -1]

    assert layer.divisions.column_count == 2
    assert layer.divisions.row_count == 1
    assert layer.division_materials[0] == mat_1
    assert layer.division_materials[1] == layer.material

    # -- Test ID-Numbers


def test_multiple_columns_exchange_material(reset_class_counters) -> None:
    layer = PhxLayer()
    mat_0 = PhxMaterial(display_name="mat_0")
    layer.add_material(mat_0)
    
    layer.divisions.set_column_widths([1, 1, 1])
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.divisions.set_cell_material(0, 0, mat_1)

    assert layer.divisions.column_count == 3
    assert layer.divisions.row_count == 1

    """
    layer.division_materials = [
        0: mat_1,
        1: mat_0 (Layer's Material),
        2: mat_0 (Layer's Material),
    ]
    """
    assert len(layer.division_materials) == 3
    assert len(layer.exchange_materials) == 1
    assert layer.division_material_id_numbers == [2, -1, -1]

    assert layer.division_materials[0] == mat_1
    assert layer.division_materials[1] == layer.material
    assert layer.division_materials[2] == layer.material

    # -- Reset material 3
    mat_2 = PhxMaterial(display_name="mat_2")
    layer.divisions.set_cell_material(2, 0, mat_2)

    assert len(layer.division_materials) == 3
    assert len(layer.exchange_materials) == 2
    assert layer.division_material_id_numbers == [2, -1, 3]

    assert layer.division_materials[0] == mat_1
    assert layer.division_materials[1] == layer.material
    assert layer.division_materials[2] == mat_2


def test_one_row_exchange_material(reset_class_counters) -> None:
    layer = PhxLayer()
    mat_0 = PhxMaterial(display_name="mat_0")
    layer.add_material(mat_0)
    layer.divisions.set_row_heights([1, 1])
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.divisions.set_cell_material(0, 0, mat_1)

    assert len(layer.division_materials) == 2
    assert len(layer.exchange_materials) == 1
    assert layer.division_material_id_numbers == [2, -1]

    assert layer.divisions.column_count == 1
    assert layer.divisions.row_count == 2
    assert layer.division_materials[0] == mat_1
    assert layer.division_materials[1] == layer.material


def test_multiple_rows_exchange_materials(reset_class_counters) -> None:
    layer = PhxLayer()
    mat_0 = PhxMaterial(display_name="mat_1")
    layer.add_material(mat_0)
    layer.divisions.set_row_heights([1, 1, 1])
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.divisions.set_cell_material(0, 0, mat_1)

    assert len(layer.division_materials) == 3
    assert len(layer.exchange_materials) == 1
    assert layer.division_material_id_numbers == [2, -1, -1]
    
    assert layer.divisions.column_count == 1
    assert layer.divisions.row_count == 3
    assert layer.division_materials[0] == mat_1
    assert layer.division_materials[1] == layer.material
    assert layer.division_materials[2] == layer.material

    # -- Reset material 3
    mat_2 = PhxMaterial(display_name="mat_2")
    layer.divisions.set_cell_material(0, 2, mat_2)

    assert len(layer.division_materials) == 3
    assert len(layer.exchange_materials) == 2
    assert layer.division_material_id_numbers == [2, -1, 3]

    assert layer.division_materials[0] == mat_1
    assert layer.division_materials[1] == layer.material
    assert layer.division_materials[2] == mat_2
