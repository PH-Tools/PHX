from PHX.model import certification
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_default_PhxPHCertification(reset_class_counters):
    c1 = certification.PhxPhiusCertification()
    result = generate_WUFI_XML_from_object(c1, _header="")
    assert xml_string_to_list(result) == [
        "<PH_CertificateCriteria>7</PH_CertificateCriteria>",
        "<PH_SelectionTargetData>2</PH_SelectionTargetData>",
        "<AnnualHeatingDemand>15.0</AnnualHeatingDemand>",
        "<AnnualCoolingDemand>15.0</AnnualCoolingDemand>",
        "<PeakHeatingLoad>10.0</PeakHeatingLoad>",
        "<PeakCoolingLoad>10.0</PeakCoolingLoad>",
        '<PH_Buildings count="1">',
        '<PH_Building index="0">',
        "<IdentNr>1</IdentNr>",
        "<BuildingCategory>1</BuildingCategory>",
        "<OccupancyTypeResidential>1</OccupancyTypeResidential>",
        "<BuildingStatus>1</BuildingStatus>",
        "<BuildingType>1</BuildingType>",
        "<OccupancySettingMethod>2</OccupancySettingMethod>",
        "<NumberUnits>1</NumberUnits>",
        "<CountStories>1</CountStories>",
        "<EnvelopeAirtightnessCoefficient>1.0</EnvelopeAirtightnessCoefficient>",
        "<SummerHRVHumidityRecovery>4</SummerHRVHumidityRecovery>",
        '<FoundationInterfaces count="0"/>',
        "<InternalGainsAdditionalData>",
        '<EvaporationHeatPerPerson unit="W">15</EvaporationHeatPerPerson>',
        "<HeatLossFluschingWC>true</HeatLossFluschingWC>",
        "<QuantityWCs>1</QuantityWCs>",
        "<RoomCategory>1</RoomCategory>",
        "<UseDefaultValuesSchool>false</UseDefaultValuesSchool>",
        "<MarginalPerformanceRatioDHW/>",
        "</InternalGainsAdditionalData>",
        "<MechanicalRoomTemperature>20.0</MechanicalRoomTemperature>",
        "<IndoorTemperature>20.0</IndoorTemperature>",
        "<OverheatingTemperatureThreshold>25.0</OverheatingTemperatureThreshold>",
        "<NonCombustibleMaterials>false</NonCombustibleMaterials>",
        "</PH_Building>",
        "</PH_Buildings>",
        "<UseWUFIMeanMonthShading>true</UseWUFIMeanMonthShading>",
    ]


def test_customized_PhxPhiusCertification(reset_class_counters):
    c1 = certification.PhxPhiusCertification()
    c1.phius_certification_criteria.phius_annual_heating_demand = 123.45
    c1.phius_certification_criteria.phius_annual_cooling_demand = 234.56
    c1.phius_certification_criteria.phius_peak_heating_load = 345.67
    c1.phius_certification_criteria.phius_peak_cooling_load = 456.78
    result = generate_WUFI_XML_from_object(c1, _header="")
    assert xml_string_to_list(result) == [
        "<PH_CertificateCriteria>7</PH_CertificateCriteria>",
        "<PH_SelectionTargetData>2</PH_SelectionTargetData>",
        "<AnnualHeatingDemand>123.45</AnnualHeatingDemand>",
        "<AnnualCoolingDemand>234.56</AnnualCoolingDemand>",
        "<PeakHeatingLoad>345.67</PeakHeatingLoad>",
        "<PeakCoolingLoad>456.78</PeakCoolingLoad>",
        '<PH_Buildings count="1">',
        '<PH_Building index="0">',
        "<IdentNr>1</IdentNr>",
        "<BuildingCategory>1</BuildingCategory>",
        "<OccupancyTypeResidential>1</OccupancyTypeResidential>",
        "<BuildingStatus>1</BuildingStatus>",
        "<BuildingType>1</BuildingType>",
        "<OccupancySettingMethod>2</OccupancySettingMethod>",
        "<NumberUnits>1</NumberUnits>",
        "<CountStories>1</CountStories>",
        "<EnvelopeAirtightnessCoefficient>1.0</EnvelopeAirtightnessCoefficient>",
        "<SummerHRVHumidityRecovery>4</SummerHRVHumidityRecovery>",
        '<FoundationInterfaces count="0"/>',
        "<InternalGainsAdditionalData>",
        '<EvaporationHeatPerPerson unit="W">15</EvaporationHeatPerPerson>',
        "<HeatLossFluschingWC>true</HeatLossFluschingWC>",
        "<QuantityWCs>1</QuantityWCs>",
        "<RoomCategory>1</RoomCategory>",
        "<UseDefaultValuesSchool>false</UseDefaultValuesSchool>",
        "<MarginalPerformanceRatioDHW/>",
        "</InternalGainsAdditionalData>",
        "<MechanicalRoomTemperature>20.0</MechanicalRoomTemperature>",
        "<IndoorTemperature>20.0</IndoorTemperature>",
        "<OverheatingTemperatureThreshold>25.0</OverheatingTemperatureThreshold>",
        "<NonCombustibleMaterials>false</NonCombustibleMaterials>",
        "</PH_Building>",
        "</PH_Buildings>",
        "<UseWUFIMeanMonthShading>true</UseWUFIMeanMonthShading>",
    ]
