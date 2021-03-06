from PHX.model.hvac import ventilation, _base, collection
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_default_PhxRoomVentilation(reset_class_counters):
    v1 = ventilation.PhxDeviceVentilator()
    sys = _base.PhxMechanicalSubSystem()
    sys.device = v1
    coll = collection.PhxMechanicalEquipmentCollection()
    coll.add_new_mech_subsystem(sys.identifier, sys)
    result = generate_WUFI_XML_from_object(coll, _header="")
    assert xml_string_to_list(result) == [
        '<Systems count="1">',
        '<System index="0">',
        '<Name>Ideal Air System</Name>',
        '<Type choice="User defined (ideal system)">1</Type>',
        '<IdentNr>1</IdentNr>',
        '<ZonesCoverage count="1">',
        '<ZoneCoverage index="0">',
        '<IdentNrZone>1.0</IdentNrZone>',
        '<CoverageHeating>1.0</CoverageHeating>',
        '<CoverageCooling>1.0</CoverageCooling>',
        '<CoverageVentilation>1.0</CoverageVentilation>',
        '<CoverageHumidification>1.0</CoverageHumidification>',
        '<CoverageDehumidification>1.0</CoverageDehumidification>',
        '</ZoneCoverage>',
        '</ZonesCoverage>',
        '<Devices count="1">',
        '<Device index="0">',
        '<Name>_unnamed_equipment_</Name>',
        '<IdentNr>1</IdentNr>',
        '<SystemType>1</SystemType>',
        '<TypeDevice>1</TypeDevice>',
        '<UsedFor_Heating>false</UsedFor_Heating>',
        '<UsedFor_DHW>false</UsedFor_DHW>',
        '<UsedFor_Cooling>false</UsedFor_Cooling>',
        '<UsedFor_Ventilation>true</UsedFor_Ventilation>',
        '<UsedFor_Humidification>false</UsedFor_Humidification>',
        '<UsedFor_Dehumidification>false</UsedFor_Dehumidification>',
        '<UseOptionalClimate>false</UseOptionalClimate>',
        '<IdentNr_OptionalClimate>-1</IdentNr_OptionalClimate>',
        '<HeatRecovery>0.0</HeatRecovery>',
        '<MoistureRecovery >0.0</MoistureRecovery >',
        '<PH_Parameters>',
        '<Quantity>1</Quantity>',
        '<HumidityRecoveryEfficiency>0.0</HumidityRecoveryEfficiency>',
        '<ElectricEfficiency>0.55</ElectricEfficiency>',
        '<DefrostRequired>true</DefrostRequired>',
        '<FrostProtection>true</FrostProtection>',
        '<TemperatureBelowDefrostUsed>-5.0</TemperatureBelowDefrostUsed>',
        '<InConditionedSpace>true</InConditionedSpace>',
        '</PH_Parameters>',
        '</Device>',
        '</Devices>',
        '<PHDistribution>',
        '<DistributionCooling/>',
        '<UseDefaultValues>true</UseDefaultValues>',
        '<DeviceInConditionedSpace>true</DeviceInConditionedSpace>',
        '</PHDistribution>',
        '</System>',
        '</Systems>'
    ]
