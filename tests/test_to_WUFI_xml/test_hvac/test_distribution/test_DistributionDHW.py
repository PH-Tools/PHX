from ladybug_geometry.geometry3d.polyline import LineSegment3D
from ladybug_geometry.geometry3d.pointvector import Point3D

from PHX.to_WUFI_XML import xml_schemas
from PHX.model.hvac.piping import PhxPipeElement, PhxPipeSegment
from PHX.model.hvac.collection import PhxMechanicalSystemCollection

from tests.test_to_WUFI_xml._utils import xml_string_to_list
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object

def test_DistributionDHW_Class(reset_class_counters):
    p1, p2 = Point3D(0,0,0), Point3D(0,0,1)
    geom = LineSegment3D(p1, p2)
    phx_pipe_segment = PhxPipeSegment(
        "test-id", "test-name", geom, 0.0254, 0.0254, 0.04, True, None, 24,
    )

    phx_pipe_element = PhxPipeElement(
        "test_id",
        "test_name"
    )
    phx_pipe_element.add_segment(phx_pipe_segment)

    phx_mech_collection = PhxMechanicalSystemCollection()
    phx_mech_collection.add_branch_piping(phx_pipe_element)

    dist_dhw = xml_schemas.DistributionDHW(phx_mech_collection)

    result = generate_WUFI_XML_from_object(dist_dhw, _header="")
    assert xml_string_to_list(result) == [
        '<CalculationMethodIndividualPipes>1</CalculationMethodIndividualPipes>',
        '<DemandRecirculation>true</DemandRecirculation>',
        '<SelectionhotWaterFixtureEff>1</SelectionhotWaterFixtureEff>',
        '<NumberOfBathrooms>1</NumberOfBathrooms>',
        '<AllPipesAreInsulated>true</AllPipesAreInsulated>',
        '<SelectionUnitsOrFloors>1</SelectionUnitsOrFloors>',
        '<PipeMaterialSimplifiedMethod>1</PipeMaterialSimplifiedMethod>',
        '<PipeDiameterSimplifiedMethod>1</PipeDiameterSimplifiedMethod>',
        '<TemperatureRoom_WR>20</TemperatureRoom_WR>',
        '<DesignFlowTemperature_WR>60</DesignFlowTemperature_WR>',
        '<DailyRunningHoursCirculation_WR>24</DailyRunningHoursCirculation_WR>',
        '<LengthCirculationPipes_WR>0</LengthCirculationPipes_WR>',
        '<HeatLossCoefficient_WR>None</HeatLossCoefficient_WR>',
        '<LengthIndividualPipes_WR>1.0</LengthIndividualPipes_WR>',
        '<ExteriorPipeDiameter_WR>25.4</ExteriorPipeDiameter_WR>',
    ]
