from PHX.model.constructions import PhxLayer, PhxMaterial, PhxLayerDivisionGrid
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_layer_with_two_columns(reset_class_counters) -> None:
    # Setup the Base Layer
    layer = PhxLayer()
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.add_material(mat_1)

    # -- Add a second column and set the new material
    mat_2 = PhxMaterial(display_name="mat_2")
    layer.divisions.set_column_widths([1, 1])
    layer.divisions.set_cell_material(1, 0, mat_2)

    # --- Check the XML Output
    result = generate_WUFI_XML_from_object(layer, _header="")
    assert xml_string_to_list(result) == [
        "<Thickness>0.0</Thickness>",
        "<Material>",
            "<Name>mat_1</Name>",
            "<ThermalConductivity>0.0</ThermalConductivity>",
            "<BulkDensity>0.0</BulkDensity>",
            "<Porosity>0.0</Porosity>",
            "<HeatCapacity>0.0</HeatCapacity>",
            "<WaterVaporResistance>0.0</WaterVaporResistance>",
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
                '<Distance>1.0</Distance>',
                '<ExpandingContracting>2</ExpandingContracting>',
            '</DivisionH>',
            '<DivisionH index="1">',
                '<Distance>1.0</Distance>',
                '<ExpandingContracting>2</ExpandingContracting>',
            '</DivisionH>',
        '</ExchangeDivisionHorizontal>',
        '<ExchangeDivisionVertical count="0"/>',
        '<ExchangeMaterialIdentNrs count="2">',
            '<MaterialIDNr index="0">',
                '<Type>1</Type>',
                '<IdentNr_Object>-1</IdentNr_Object>',
            '</MaterialIDNr>',
            '<MaterialIDNr index="1">',
                '<Type>1</Type>',
                '<IdentNr_Object>2</IdentNr_Object>',
            '</MaterialIDNr>',
        '</ExchangeMaterialIdentNrs>',
    ]



def test_layer_with_three_columns() -> None:
    # Setup the Base Layer
    layer = PhxLayer()
    mat_1 = PhxMaterial(display_name="mat_1")
    layer.add_material(mat_1)

    # -- Add columns and set the new materials
    layer.divisions.set_column_widths([1, 2, 3])
    mat_2 = PhxMaterial(display_name="mat_2")
    layer.divisions.set_cell_material(1, 0, mat_2)

    mat_3 = PhxMaterial(display_name="mat_3")
    layer.divisions.set_cell_material(2, 0, mat_3)

    # --- Check the XML Output
    result = generate_WUFI_XML_from_object(layer, _header="")
    assert xml_string_to_list(result) == [
        "<Thickness>0.0</Thickness>",
        "<Material>",
            "<Name>mat_1</Name>",
            "<ThermalConductivity>0.0</ThermalConductivity>",
            "<BulkDensity>0.0</BulkDensity>",
            "<Porosity>0.0</Porosity>",
            "<HeatCapacity>0.0</HeatCapacity>",
            "<WaterVaporResistance>0.0</WaterVaporResistance>",
            "<ReferenceWaterContent>0.0</ReferenceWaterContent>",
            "<Color>",
                "<Alpha>255</Alpha>",
                "<Red>255</Red>",
                "<Green>255</Green>",
                "<Blue>255</Blue>",
            "</Color>",
        "</Material>",
        '<ExchangeDivisionHorizontal count="3">',
            '<DivisionH index="0">',
                '<Distance>1.0</Distance>',
                '<ExpandingContracting>2</ExpandingContracting>',
            '</DivisionH>',
            '<DivisionH index="1">',
                '<Distance>2.0</Distance>',
                '<ExpandingContracting>2</ExpandingContracting>',
            '</DivisionH>',
            '<DivisionH index="2">',
                '<Distance>3.0</Distance>',
                '<ExpandingContracting>2</ExpandingContracting>',
            '</DivisionH>',
        '</ExchangeDivisionHorizontal>',
        '<ExchangeDivisionVertical count="0"/>',
        '<ExchangeMaterialIdentNrs count="3">',
            '<MaterialIDNr index="0">',
                '<Type>1</Type>',
                '<IdentNr_Object>-1</IdentNr_Object>',
            '</MaterialIDNr>',
            '<MaterialIDNr index="1">',
                '<Type>1</Type>',
                '<IdentNr_Object>2</IdentNr_Object>',
            '</MaterialIDNr>',
            '<MaterialIDNr index="2">',
                '<Type>1</Type>',
                '<IdentNr_Object>3</IdentNr_Object>',
            '</MaterialIDNr>',
        '</ExchangeMaterialIdentNrs>',
    ]
