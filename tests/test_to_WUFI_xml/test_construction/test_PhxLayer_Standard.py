from PHX.model import constructions
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_default_PhxLayer(reset_class_counters):
    l1 = constructions.PhxLayer()
    result = generate_WUFI_XML_from_object(l1, _header="")
    assert xml_string_to_list(result) == [
        "<Thickness>0.0</Thickness>",
        "<Material>",
        "<Name></Name>",
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
    ]
