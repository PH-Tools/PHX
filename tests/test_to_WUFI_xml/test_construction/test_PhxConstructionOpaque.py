from PHX.model.constructions import PhxConstructionOpaque, PhxLayer, PhxMaterial
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list

# -- Simple Layers, No Divisions, no exchange materials


def test_default_PhxConstructionOpaque(reset_class_counters) -> None:
    a1 = PhxConstructionOpaque()
    result = generate_WUFI_XML_from_object(a1, _header="")
    assert xml_string_to_list(result) == [
        "<IdentNr>1</IdentNr>",
        "<Name></Name>",
        "<Order_Layers>2</Order_Layers>",
        "<Grid_Kind>2</Grid_Kind>",
        '<Layers count="0"/>',
        '<ExchangeMaterials count="0"/>',
    ]


def test_construction_with_single_layer_no_divisions(reset_class_counters) -> None:
    a1 = PhxConstructionOpaque()
    layer = PhxLayer()
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.set_material(mat_1)
    a1.layers.append(layer)

    # ---
    result = generate_WUFI_XML_from_object(a1, _header="")
    assert xml_string_to_list(result) == [
        "<IdentNr>1</IdentNr>",
        "<Name></Name>",
        "<Order_Layers>2</Order_Layers>",
        "<Grid_Kind>2</Grid_Kind>",
        '<Layers count="1">',
        '<Layer index="0">',
        "<Thickness>0.0</Thickness>",
        "<Material>",
        "<Name>mat_1</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<Porosity>0.95</Porosity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<WaterVaporResistance>1.0</WaterVaporResistance>",
        "<ReferenceWaterContent>0.0</ReferenceWaterContent>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</Material>",
        '<ExchangeDivisionHorizontal count="0"/>',
        '<ExchangeDivisionVertical count="0"/>',
        '<ExchangeMaterialIdentNrs count="0"/>',
        "</Layer>",
        "</Layers>",
        '<ExchangeMaterials count="0"/>',
    ]


def test_construction_with_multiple_layers_no_divisions(reset_class_counters) -> None:
    a1 = PhxConstructionOpaque()
    layer_1 = PhxLayer()
    mat_1 = PhxMaterial(display_name="mat_1")
    layer_1.set_material(mat_1)
    a1.layers.append(layer_1)

    layer_2 = PhxLayer()
    mat_2 = PhxMaterial(display_name="mat_2")
    layer_2.set_material(mat_2)
    a1.layers.append(layer_2)

    layer_3 = PhxLayer()
    mat_3 = PhxMaterial(display_name="mat_3")
    layer_3.set_material(mat_3)
    a1.layers.append(layer_3)

    # ---
    result = generate_WUFI_XML_from_object(a1, _header="")
    assert xml_string_to_list(result) == [
        "<IdentNr>1</IdentNr>",
        "<Name></Name>",
        "<Order_Layers>2</Order_Layers>",
        "<Grid_Kind>2</Grid_Kind>",
        '<Layers count="3">',
        '<Layer index="0">',
        "<Thickness>0.0</Thickness>",
        "<Material>",
        "<Name>mat_1</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<Porosity>0.95</Porosity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<WaterVaporResistance>1.0</WaterVaporResistance>",
        "<ReferenceWaterContent>0.0</ReferenceWaterContent>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</Material>",
        '<ExchangeDivisionHorizontal count="0"/>',
        '<ExchangeDivisionVertical count="0"/>',
        '<ExchangeMaterialIdentNrs count="0"/>',
        "</Layer>",
        '<Layer index="1">',
        "<Thickness>0.0</Thickness>",
        "<Material>",
        "<Name>mat_2</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<Porosity>0.95</Porosity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<WaterVaporResistance>1.0</WaterVaporResistance>",
        "<ReferenceWaterContent>0.0</ReferenceWaterContent>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</Material>",
        '<ExchangeDivisionHorizontal count="0"/>',
        '<ExchangeDivisionVertical count="0"/>',
        '<ExchangeMaterialIdentNrs count="0"/>',
        "</Layer>",
        '<Layer index="2">',
        "<Thickness>0.0</Thickness>",
        "<Material>",
        "<Name>mat_3</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<Porosity>0.95</Porosity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<WaterVaporResistance>1.0</WaterVaporResistance>",
        "<ReferenceWaterContent>0.0</ReferenceWaterContent>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</Material>",
        '<ExchangeDivisionHorizontal count="0"/>',
        '<ExchangeDivisionVertical count="0"/>',
        '<ExchangeMaterialIdentNrs count="0"/>',
        "</Layer>",
        "</Layers>",
        '<ExchangeMaterials count="0"/>',
    ]


# --- Assemblies/Layers with Divisions (Mixed material layers)


def test_construction_with_single_layer_two_columns(reset_class_counters) -> None:
    # Setup the Base Layer, Material
    layer_1 = PhxLayer()
    mat_1 = PhxMaterial(display_name="mat_1")
    layer_1.set_material(mat_1)

    # -- Add a second column and set the new material
    mat_2 = PhxMaterial(display_name="mat_2")
    layer_1.divisions.set_column_widths([1, 1])
    layer_1.divisions.add_new_row(1)
    layer_1.divisions.set_cell_material(1, 0, mat_2)

    #  -- Construct the Assembly
    a1 = PhxConstructionOpaque()
    a1.layers.append(layer_1)

    # ---
    result = generate_WUFI_XML_from_object(a1, _header="")
    assert xml_string_to_list(result) == [
        "<IdentNr>1</IdentNr>",
        "<Name></Name>",
        "<Order_Layers>2</Order_Layers>",
        "<Grid_Kind>2</Grid_Kind>",
        '<Layers count="1">',
        '<Layer index="0">',
        "<Thickness>0.0</Thickness>",
        "<Material>",
        "<Name>mat_1</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<Porosity>0.95</Porosity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<WaterVaporResistance>1.0</WaterVaporResistance>",
        "<ReferenceWaterContent>0.0</ReferenceWaterContent>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</Material>",
        '<ExchangeDivisionHorizontal count="2">',
        '<DivisionH index="0">',
        "<Distance>1.0</Distance>",
        "<ExpandingContracting>2</ExpandingContracting>",
        "</DivisionH>",
        '<DivisionH index="1">',
        "<Distance>1.0</Distance>",
        "<ExpandingContracting>2</ExpandingContracting>",
        "</DivisionH>",
        "</ExchangeDivisionHorizontal>",
        '<ExchangeDivisionVertical count="0"/>',
        '<ExchangeMaterialIdentNrs count="2">',
        '<MaterialIDNr index="0">',
        "<Type>1</Type>",
        "<IdentNr_Object>-1</IdentNr_Object>",
        "</MaterialIDNr>",
        '<MaterialIDNr index="1">',
        "<Type>1</Type>",
        "<IdentNr_Object>3</IdentNr_Object>",
        "</MaterialIDNr>",
        "</ExchangeMaterialIdentNrs>",
        "</Layer>",
        "</Layers>",
        '<ExchangeMaterials count="1">',
        '<ExchangeMaterial index="0">',
        "<IdentNr>3</IdentNr>",
        "<Name>mat_2</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</ExchangeMaterial>",
        "</ExchangeMaterials>",
    ]


def test_construction_with_two_layers_two_columns_each(reset_class_counters) -> None:
    # ---- SECOND LAYER
    # Setup the Base Layer, Material
    layer_1 = PhxLayer()
    mat_1 = PhxMaterial(display_name="mat_1")
    layer_1.set_material(mat_1)

    # -- Add a second column and set the new material
    mat_2 = PhxMaterial(display_name="mat_2")
    layer_1.divisions.set_column_widths([1, 1])
    layer_1.divisions.add_new_row(1)
    layer_1.divisions.set_cell_material(1, 0, mat_2)

    # ---- SECOND LAYER
    # Setup the Base Layer, Material
    layer_2 = PhxLayer()
    mat_3 = PhxMaterial(display_name="mat_3")
    layer_2.set_material(mat_3)

    # -- Add a second column and set the new material
    mat_4 = PhxMaterial(display_name="mat_4")
    layer_2.divisions.set_column_widths([1, 1])
    layer_2.divisions.add_new_row(1)
    layer_2.divisions.set_cell_material(0, 0, mat_4)

    #  -- Construct the Assembly
    a1 = PhxConstructionOpaque()
    a1.layers.append(layer_1)
    a1.layers.append(layer_2)

    # ---
    result = generate_WUFI_XML_from_object(a1, _header="")
    assert xml_string_to_list(result) == [
        "<IdentNr>1</IdentNr>",
        "<Name></Name>",
        "<Order_Layers>2</Order_Layers>",
        "<Grid_Kind>2</Grid_Kind>",
        '<Layers count="2">',
        '<Layer index="0">',
        "<Thickness>0.0</Thickness>",
        "<Material>",
        "<Name>mat_1</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<Porosity>0.95</Porosity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<WaterVaporResistance>1.0</WaterVaporResistance>",
        "<ReferenceWaterContent>0.0</ReferenceWaterContent>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</Material>",
        '<ExchangeDivisionHorizontal count="2">',
        '<DivisionH index="0">',
        "<Distance>1.0</Distance>",
        "<ExpandingContracting>2</ExpandingContracting>",
        "</DivisionH>",
        '<DivisionH index="1">',
        "<Distance>1.0</Distance>",
        "<ExpandingContracting>2</ExpandingContracting>",
        "</DivisionH>",
        "</ExchangeDivisionHorizontal>",
        '<ExchangeDivisionVertical count="0"/>',
        '<ExchangeMaterialIdentNrs count="2">',
        '<MaterialIDNr index="0">',
        "<Type>1</Type>",
        "<IdentNr_Object>-1</IdentNr_Object>",
        "</MaterialIDNr>",
        '<MaterialIDNr index="1">',
        "<Type>1</Type>",
        "<IdentNr_Object>3</IdentNr_Object>",
        "</MaterialIDNr>",
        "</ExchangeMaterialIdentNrs>",
        "</Layer>",
        '<Layer index="1">',
        "<Thickness>0.0</Thickness>",
        "<Material>",
        "<Name>mat_3</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<Porosity>0.95</Porosity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<WaterVaporResistance>1.0</WaterVaporResistance>",
        "<ReferenceWaterContent>0.0</ReferenceWaterContent>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</Material>",
        '<ExchangeDivisionHorizontal count="2">',
        '<DivisionH index="0">',
        "<Distance>1.0</Distance>",
        "<ExpandingContracting>2</ExpandingContracting>",
        "</DivisionH>",
        '<DivisionH index="1">',
        "<Distance>1.0</Distance>",
        "<ExpandingContracting>2</ExpandingContracting>",
        "</DivisionH>",
        "</ExchangeDivisionHorizontal>",
        '<ExchangeDivisionVertical count="0"/>',
        '<ExchangeMaterialIdentNrs count="2">',
        '<MaterialIDNr index="0">',
        "<Type>1</Type>",
        "<IdentNr_Object>6</IdentNr_Object>",
        "</MaterialIDNr>",
        '<MaterialIDNr index="1">',
        "<Type>1</Type>",
        "<IdentNr_Object>-1</IdentNr_Object>",
        "</MaterialIDNr>",
        "</ExchangeMaterialIdentNrs>",
        "</Layer>",
        "</Layers>",
        '<ExchangeMaterials count="2">',
        '<ExchangeMaterial index="0">',
        "<IdentNr>3</IdentNr>",
        "<Name>mat_2</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</ExchangeMaterial>",
        '<ExchangeMaterial index="1">',
        "<IdentNr>6</IdentNr>",
        "<Name>mat_4</Name>",
        "<ThermalConductivity>0.0</ThermalConductivity>",
        "<BulkDensity>0.0</BulkDensity>",
        "<HeatCapacity>0.0</HeatCapacity>",
        "<Color>",
        "<Alpha>255</Alpha>",
        "<Red>255</Red>",
        "<Green>255</Green>",
        "<Blue>255</Blue>",
        "</Color>",
        "</ExchangeMaterial>",
        "</ExchangeMaterials>",
    ]
