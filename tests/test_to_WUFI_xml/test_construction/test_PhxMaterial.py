from PHX.model import constructions
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_default_PhxMaterial(reset_class_counters):
    m1 = constructions.PhxMaterial()
    result = generate_WUFI_XML_from_object(m1, _header="")
    assert xml_string_to_list(result) == [
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
    ]
