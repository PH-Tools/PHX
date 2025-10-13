from PHX.model import building
from PHX.model.enums.building import SpecificHeatCapacityType
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_default_PhxProject(reset_class_counters):
    z1 = building.PhxZone()
    result = generate_WUFI_XML_from_object(z1, _header="")
    assert xml_string_to_list(result) == [
        "<Name></Name>",
        "<KindZone>1</KindZone>",
        "<KindAttachedZone>0</KindAttachedZone>",
        "<TemperatureReductionFactorUserDefined>1.0</TemperatureReductionFactorUserDefined>",
        "<IdentNr>1</IdentNr>",
        '<RoomsVentilation count="0"/>',
        '<LoadsPersonsPH count="0"/>',
        '<LoadsLightingsPH count="0"/>',
        "<GrossVolume_Selection>7</GrossVolume_Selection>",
        "<GrossVolume>0.0</GrossVolume>",
        "<NetVolume_Selection>6</NetVolume_Selection>",
        "<NetVolume>0.0</NetVolume>",
        "<FloorArea_Selection>6</FloorArea_Selection>",
        "<FloorArea>0.0</FloorArea>",
        "<ClearanceHeight_Selection>1</ClearanceHeight_Selection>",
        "<ClearanceHeight>2.5</ClearanceHeight>",
        "<SpecificHeatCapacity_Selection>1</SpecificHeatCapacity_Selection>",
        "<SpecificHeatCapacity>60</SpecificHeatCapacity>",
        "<IdentNrPH_Building>1</IdentNrPH_Building>",
        '<OccupantQuantityUserDef unit="-">0</OccupantQuantityUserDef>',
        '<NumberBedrooms unit="-">0</NumberBedrooms>',
        '<HomeDevice count="0"/>',
        '<ExhaustVents count="0"/>',
        '<ThermalBridges count="0"/>',
        '<SummerNaturalVentilationDay unit="1/hr">0</SummerNaturalVentilationDay>',
        '<SummerNaturalVentilationNight unit="1/hr">0</SummerNaturalVentilationNight>',
    ]


def test_zone_xml_specific_heat_capacity_mixed(reset_class_counters):
    """Test XML output for PhxZone with MIXED specific heat capacity."""
    zone = building.PhxZone(specific_heat_capacity=SpecificHeatCapacityType.MIXED, specific_heat_capacity_wh_m2k=132)
    result = generate_WUFI_XML_from_object(zone, _header="")
    xml_lines = xml_string_to_list(result)

    # Check that the specific heat capacity selection and value are correct
    assert "<SpecificHeatCapacity_Selection>2</SpecificHeatCapacity_Selection>" in xml_lines
    assert "<SpecificHeatCapacity>132</SpecificHeatCapacity>" in xml_lines


def test_zone_xml_specific_heat_capacity_massive(reset_class_counters):
    """Test XML output for PhxZone with MASSIVE specific heat capacity."""
    zone = building.PhxZone(specific_heat_capacity=SpecificHeatCapacityType.MASSIVE, specific_heat_capacity_wh_m2k=204)
    result = generate_WUFI_XML_from_object(zone, _header="")
    xml_lines = xml_string_to_list(result)

    # Check that the specific heat capacity selection and value are correct
    assert "<SpecificHeatCapacity_Selection>3</SpecificHeatCapacity_Selection>" in xml_lines
    assert "<SpecificHeatCapacity>204</SpecificHeatCapacity>" in xml_lines


def test_zone_xml_specific_heat_capacity_user_defined(reset_class_counters):
    """Test XML output for PhxZone with USER_DEFINED specific heat capacity."""
    zone = building.PhxZone(
        specific_heat_capacity=SpecificHeatCapacityType.USER_DEFINED, specific_heat_capacity_wh_m2k=150
    )
    result = generate_WUFI_XML_from_object(zone, _header="")
    xml_lines = xml_string_to_list(result)

    # Check that the specific heat capacity selection and value are correct
    assert "<SpecificHeatCapacity_Selection>6</SpecificHeatCapacity_Selection>" in xml_lines
    assert "<SpecificHeatCapacity>150</SpecificHeatCapacity>" in xml_lines


def test_zone_xml_default_specific_heat_capacity_verification(reset_class_counters):
    """Verify the default case specifically focuses on the specific heat capacity XML output."""
    zone = building.PhxZone()  # Uses default LIGHTWEIGHT (1) and 60 Wh/m²K
    result = generate_WUFI_XML_from_object(zone, _header="")
    xml_lines = xml_string_to_list(result)

    # Verify the specific heat capacity lines in the default case
    assert "<SpecificHeatCapacity_Selection>1</SpecificHeatCapacity_Selection>" in xml_lines
    assert "<SpecificHeatCapacity>60</SpecificHeatCapacity>" in xml_lines
