from ladybug_geometry.geometry3d.polyline import LineSegment3D
from ladybug_geometry.geometry3d.pointvector import Point3D

from PHX.to_WUFI_XML import xml_schemas
from PHX.model.hvac.piping import (
    PhxPipeElement,
    PhxPipeSegment,
    PhxPipeTrunk,
    PhxPipeBranch,
    PhxHotWaterPipingMaterial,
    PhxHotWaterPipingDiameter,
)
from PHX.model.hvac.collection import PhxMechanicalSystemCollection

from tests.test_to_WUFI_xml._utils import xml_string_to_list
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object


def test_add_Trunk_to_HW_System(reset_class_counters):
    p1, p2 = Point3D(0, 0, 0), Point3D(0, 0, 1)
    phx_pipe_segment = PhxPipeSegment(
        identifier="test-id",
        display_name="test-display-name",
        geometry=LineSegment3D(p1, p2),
        pipe_material=PhxHotWaterPipingMaterial.COPPER_K,
        pipe_diameter=PhxHotWaterPipingDiameter._1_0_0_IN,
        insulation_thickness_m=25.4,
        insulation_conductivity=0.04,
        insulation_reflective=True,
        insulation_quality=None,
        daily_period=24,
    )
    phx_pipe_fixture = PhxPipeElement()
    phx_pipe_fixture.add_segment(phx_pipe_segment)

    phx_pipe_branch = PhxPipeBranch(display_name="test-branch")
    phx_pipe_branch.add_fixture(phx_pipe_fixture)

    phx_pipe_trunk = PhxPipeTrunk(display_name="test-trunk")

    phx_mech_collection = PhxMechanicalSystemCollection()
    phx_mech_collection.add_distribution_piping(phx_pipe_trunk)

    result = generate_WUFI_XML_from_object(
        phx_mech_collection, _header="", _schema_name="_DistributionDHW"
    )
    assert xml_string_to_list(result) == [
        "<CalculationMethodIndividualPipes>4</CalculationMethodIndividualPipes>",
        "<DemandRecirculation>true</DemandRecirculation>",
        "<SelectionhotWaterFixtureEff>1</SelectionhotWaterFixtureEff>",
        "<NumberOfBathrooms>1</NumberOfBathrooms>",
        "<AllPipesAreInsulated>true</AllPipesAreInsulated>",
        "<SelectionUnitsOrFloors>2</SelectionUnitsOrFloors>",
        "<PipeMaterialSimplifiedMethod>2</PipeMaterialSimplifiedMethod>",
        "<PipeDiameterSimplifiedMethod>25.4</PipeDiameterSimplifiedMethod>",
        "<TemperatureRoom_WR>20.0</TemperatureRoom_WR>",
        "<DesignFlowTemperature_WR>60.0</DesignFlowTemperature_WR>",
        "<DailyRunningHoursCirculation_WR>0.0</DailyRunningHoursCirculation_WR>",
        "<LengthCirculationPipes_WR>0</LengthCirculationPipes_WR>",
        "<HeatLossCoefficient_WR/>",
        "<LengthIndividualPipes_WR>0</LengthIndividualPipes_WR>",
        "<ExteriorPipeDiameter_WR/>",
        '<Truncs count="1">',
        '<Trunc index="0">',
        "<Name>test-trunk</Name>",
        "<IdentNr>1</IdentNr>",
        "<PipingLength>0</PipingLength>",
        "<PipeMaterial>3</PipeMaterial>",
        "<PipingDiameter>1</PipingDiameter>",
        "<CountUnitsOrFloors>1</CountUnitsOrFloors>",
        "<DemandRecirculation>false</DemandRecirculation>",
        '<Branches count="0"/>',
        "</Trunc>",
        "</Truncs>",
    ]
