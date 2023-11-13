from PHX.model.hvac import heating, _base, collection
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_default_PhxHeaterBoilerFossil(reset_class_counters):
    h1 = heating.PhxHeaterBoilerFossil()
    h1.usage_profile.space_heating_percent = 1.0
    assert h1.usage_profile.cooling == False

    coll = collection.PhxMechanicalSystemCollection()
    coll.add_new_mech_device(h1.identifier, h1)

    assert len(coll.heat_pump_devices) == 0
    assert len(coll.space_heating_devices) == 1

    result = generate_WUFI_XML_from_object(coll, _header="")
    assert xml_string_to_list(result) == [
        "<Name>Ideal Air System</Name>",
        '<Type choice="User defined (ideal system)">1</Type>',
        "<IdentNr>1</IdentNr>",
        '<ZonesCoverage count="1">',
        '<ZoneCoverage index="0">',
        "<IdentNrZone>1</IdentNrZone>",
        "<CoverageHeating>1.0</CoverageHeating>",
        "<CoverageCooling>1.0</CoverageCooling>",
        "<CoverageVentilation>1.0</CoverageVentilation>",
        "<CoverageHumidification>1.0</CoverageHumidification>",
        "<CoverageDehumidification>1.0</CoverageDehumidification>",
        "</ZoneCoverage>",
        "</ZonesCoverage>",
        '<Devices count="1">',
        '<Device index="0">',
        "<Name>_unnamed_equipment_</Name>",
        "<IdentNr>1</IdentNr>",
        "<SystemType>3</SystemType>",
        "<TypeDevice>3</TypeDevice>",
        "<UsedFor_Heating>true</UsedFor_Heating>",
        "<UsedFor_DHW>false</UsedFor_DHW>",
        "<UsedFor_Cooling>false</UsedFor_Cooling>",
        "<UsedFor_Ventilation>false</UsedFor_Ventilation>",
        "<UsedFor_Humidification>false</UsedFor_Humidification>",
        "<UsedFor_Dehumidification>false</UsedFor_Dehumidification>",
        "<PH_Parameters>",
        "<EnergySourceBoilerType>1</EnergySourceBoilerType>",
        "<CondensingBoiler>true</CondensingBoiler>",
        "<InConditionedSpace>true</InConditionedSpace>",
        "<MaximalBoilerPower>10.0</MaximalBoilerPower>",
        "<BoilerEfficiency30>0.98</BoilerEfficiency30>",
        "<BoilerEfficiencyNominalOutput>0.94</BoilerEfficiencyNominalOutput>",
        "<AverageReturnTemperatureMeasured30Load>30</AverageReturnTemperatureMeasured30Load>",
        "<AverageBoilerTemperatureDesign70_55>41</AverageBoilerTemperatureDesign70_55>",
        "<AverageBoilerTemperatureDesign55_45>35</AverageBoilerTemperatureDesign55_45>",
        "<AverageBoilerTemperatureDesign35_28>24</AverageBoilerTemperatureDesign35_28>",
        "<StandbyHeatLossBoiler70/>",
        "<SolarFractionBoilerSpaceHeating/>",
        "<AuxiliaryEnergy/>",
        "<AuxiliaryEnergyDHW/>",
        "</PH_Parameters>",
        "<DHW_Parameters>",
        "<CoverageWithinSystem>0.0</CoverageWithinSystem>",
        "<Unit>0.0</Unit>",
        "<Selection>1</Selection>",
        "</DHW_Parameters>",
        "<Heating_Parameters>",
        "<CoverageWithinSystem>1.0</CoverageWithinSystem>",
        "<Unit>0.0</Unit>",
        "<Selection>1</Selection>",
        "</Heating_Parameters>",
        "</Device>",
        "</Devices>",
        "<PHDistribution>",
        "<DistributionDHW>",
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
        '<Truncs count="0"/>',
        "</DistributionDHW>",
        "<DistributionCooling/>",
        '<DistributionVentilation count="0"/>',
        "<UseDefaultValues>false</UseDefaultValues>",
        "<DeviceInConditionedSpace>true</DeviceInConditionedSpace>",
        '<SupportiveDevices count="0"/>',
        "</PHDistribution>",
    ]