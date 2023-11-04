from PHX.model.hvac import heat_pumps, _base, collection
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_default_PhxHeaterHeatPumpAnnual_with_no_cooling(reset_class_counters):
    h1 = heat_pumps.PhxHeatPumpAnnual()
    h1.usage_profile.space_heating_percent = 1.0

    # -- Set all the cooling 'off'
    h1.params_cooling.ventilation.used = False
    h1.params_cooling.recirculation.used = False
    h1.params_cooling.dehumidification.used = False
    h1.params_cooling.panel.used = False

    coll = collection.PhxMechanicalSystemCollection()
    coll.add_new_mech_device(h1.identifier, h1)
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
        "<SystemType>5</SystemType>",
        "<TypeDevice>5</TypeDevice>",
        "<UsedFor_Heating>true</UsedFor_Heating>",
        "<UsedFor_DHW>false</UsedFor_DHW>",
        "<UsedFor_Cooling>false</UsedFor_Cooling>",
        "<UsedFor_Ventilation>false</UsedFor_Ventilation>",
        "<UsedFor_Humidification>false</UsedFor_Humidification>",
        "<UsedFor_Dehumidification>false</UsedFor_Dehumidification>",
        "<PH_Parameters>",
        "<AuxiliaryEnergy/>",
        "<AuxiliaryEnergyDHW/>",
        "<InConditionedSpace>true</InConditionedSpace>",
        "<AnnualCOP/>",
        "<TotalSystemPerformanceRatioHeatGenerator/>",
        "<HPType>3</HPType>",
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
        "<Cooling_Parameters>",
        "<CoverageWithinSystem>0.0</CoverageWithinSystem>",
        "<Unit>0.0</Unit>",
        "<Selection>1</Selection>",
        "</Cooling_Parameters>",
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


def test_default_PhxHeaterHeatPumpAnnual_with_single_recirc_cooling(reset_class_counters):
    h1 = heat_pumps.PhxHeatPumpAnnual()
    h1.usage_profile.space_heating_percent = 1.0
    h1.usage_profile.cooling_percent = 1.0

    # -- Turn on only the Recirculation cooling
    h1.params_cooling.ventilation.used = False
    h1.params_cooling.recirculation.used = True
    h1.params_cooling.dehumidification.used = False
    h1.params_cooling.panel.used = False

    coll = collection.PhxMechanicalSystemCollection()
    coll.add_new_mech_device(h1.identifier, h1)
    
    # -- Check the result
    result = generate_WUFI_XML_from_object(coll, _header="")
    assert xml_string_to_list(result) == [
        '<Name>Ideal Air System</Name>',
        '<Type choice="User defined (ideal system)">1</Type>',
        '<IdentNr>1</IdentNr>',
        '<ZonesCoverage count="1">',
        '<ZoneCoverage index="0">',
        '<IdentNrZone>1</IdentNrZone>',
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
        '<SystemType>5</SystemType>',
        '<TypeDevice>5</TypeDevice>',
        '<UsedFor_Heating>true</UsedFor_Heating>',
        '<UsedFor_DHW>false</UsedFor_DHW>',
        '<UsedFor_Cooling>true</UsedFor_Cooling>',
        '<UsedFor_Ventilation>false</UsedFor_Ventilation>',
        '<UsedFor_Humidification>false</UsedFor_Humidification>',
        '<UsedFor_Dehumidification>false</UsedFor_Dehumidification>',
        '<PH_Parameters>',
        '<AuxiliaryEnergy/>',
        '<AuxiliaryEnergyDHW/>',
        '<InConditionedSpace>true</InConditionedSpace>',
        '<AnnualCOP/>',
        '<TotalSystemPerformanceRatioHeatGenerator/>',
        '<HPType>3</HPType>',
        '</PH_Parameters>',
        '<DHW_Parameters>',
        '<CoverageWithinSystem>0.0</CoverageWithinSystem>',
        '<Unit>0.0</Unit>',
        '<Selection>1</Selection>',
        '</DHW_Parameters>',
        '<Heating_Parameters>',
        '<CoverageWithinSystem>1.0</CoverageWithinSystem>',
        '<Unit>0.0</Unit>',
        '<Selection>1</Selection>',
        '</Heating_Parameters>',
        "<Cooling_Parameters>",
        "<CoverageWithinSystem>1.0</CoverageWithinSystem>",
        "<Unit>0.0</Unit>",
        "<Selection>1</Selection>",
        "</Cooling_Parameters>",
        '</Device>',
        '</Devices>',
        '<PHDistribution>',
        '<DistributionDHW>',
        '<CalculationMethodIndividualPipes>4</CalculationMethodIndividualPipes>',
        '<DemandRecirculation>true</DemandRecirculation>',
        '<SelectionhotWaterFixtureEff>1</SelectionhotWaterFixtureEff>',
        '<NumberOfBathrooms>1</NumberOfBathrooms>',
        '<AllPipesAreInsulated>true</AllPipesAreInsulated>',
        '<SelectionUnitsOrFloors>2</SelectionUnitsOrFloors>',
        '<PipeMaterialSimplifiedMethod>2</PipeMaterialSimplifiedMethod>',
        '<PipeDiameterSimplifiedMethod>25.4</PipeDiameterSimplifiedMethod>',
        '<TemperatureRoom_WR>20.0</TemperatureRoom_WR>',
        '<DesignFlowTemperature_WR>60.0</DesignFlowTemperature_WR>',
        '<DailyRunningHoursCirculation_WR>0.0</DailyRunningHoursCirculation_WR>',
        '<LengthCirculationPipes_WR>0</LengthCirculationPipes_WR>',
        '<HeatLossCoefficient_WR/>',
        '<LengthIndividualPipes_WR>0</LengthIndividualPipes_WR>',
        '<ExteriorPipeDiameter_WR/>',
        '<Truncs count="0"/>',
        '</DistributionDHW>',
        '<DistributionCooling>',
        '<CoolingViaRecirculation>true</CoolingViaRecirculation>',
        '<RecirculatingAirOnOff>false</RecirculatingAirOnOff>',
        '<MaxRecirculationAirCoolingPower>10.0</MaxRecirculationAirCoolingPower>',
        '<MinTempCoolingCoilRecirculatingAir>12.0</MinTempCoolingCoilRecirculatingAir>',
        '<RecirculationCoolingCOP>4.0</RecirculationCoolingCOP>',
        '<RecirculationAirVolume>100.0</RecirculationAirVolume>',
        '<ControlledRecirculationVolumeFlow>true</ControlledRecirculationVolumeFlow>',
        '</DistributionCooling>',
        '<DistributionVentilation count="0"/>',
        '<UseDefaultValues>false</UseDefaultValues>',
        '<DeviceInConditionedSpace>true</DeviceInConditionedSpace>',
        '<SupportiveDevices count="0"/>',
        '</PHDistribution>',
    ]