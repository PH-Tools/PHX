from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.polyline import LineSegment3D

from PHX.model.hvac.ducting import PhxDuctElement, PhxDuctSegment
from PHX.to_WUFI_XML import xml_schemas
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_Duct_Schema(reset_class_counters):
    p1 = Point3D(0, 0, 0)
    p2 = Point3D(0, 0, 1)
    geom = LineSegment3D.from_end_points(p1, p2)

    phx_duct_segment = PhxDuctSegment(
        identifier="test_identifier",
        display_name="test_display_name",
        geometry=geom,
        diameter=25.4,
        width=None,
        height=None,
        insulation_thickness=25.4,
        insulation_conductivity=0.04,
        insulation_reflective=True,
    )

    phx_duct_element = PhxDuctElement(
        "test_identifier",
        "test_display_name",
        1,
    )
    phx_duct_element.add_segment(phx_duct_segment)
    result = generate_WUFI_XML_from_object(phx_duct_element, _header="")
    assert xml_string_to_list(result) == [
        "<Name>test_display_name</Name>",
        "<IdentNr>1</IdentNr>",
        '<DuctDiameter unit="mm">25.4</DuctDiameter>',
        '<DuctShapeHeight unit="mm">0.0</DuctShapeHeight>',
        '<DuctShapeWidth unit="mm">0.0</DuctShapeWidth>',
        '<DuctLength unit="m">1.0</DuctLength>',
        '<InsulationThickness unit="mm">25.4</InsulationThickness>',
        '<ThermalConductivity unit="W/mK">0.04</ThermalConductivity>',
        '<Quantity unit="-">1</Quantity>',
        "<DuctType>1</DuctType>",
        "<DuctShape>1</DuctShape>",
        "<IsReflective>true</IsReflective>",
        '<AssignedVentUnits count="1">',
        '<IdentNrVentUnit index="0">1</IdentNrVentUnit>',
        "</AssignedVentUnits>",
    ]
