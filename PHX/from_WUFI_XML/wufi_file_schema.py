# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Pydantic Model for WUFI-XML file format."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from honeybee_ph_standards.sourcefactors import factors, phius_CO2_factors, phius_source_energy_factors
from ph_units.converter import convert
from pydantic import BaseModel, validator

from PHX.from_WUFI_XML import wufi_file_types as unit
from PHX.from_WUFI_XML.read_WUFI_XML_file import Tag
from PHX.model.enums.phius_certification import PhiusCertificationProgram

# ------------------------------------------------------------------------------
# -- Unit Types


def unpack_xml_tag(_value: Union[List, Dict, Tag]) -> Union[Dict, List, str, None]:
    """This validator should run first before any unit-conversion. This will
    unpack the Tag object and return the .text, or a dict with the unit and the
    value if it is a unit-type.
    """
    if isinstance(_value, Tag):
        # -- If it is a unit-type, pass back a dict with the unit and the value
        # -- this will get unpacked and used by the unit-type converter.
        unit_type = getattr(_value, "attrib", {}).get("unit", None)
        if unit_type:
            return {"value": _value.text, "unit_type": unit_type}

        # -- Otherwise, just pass back the .text
        if _value.text == "None":
            return None
        else:
            return _value.text

    return _value


# ------------------------------------------------------------------------------
# -- Climate


class CO2FactorsUserDef(BaseModel):
    __root__: Any

    @validator("__root__", pre=True)
    def unpack_xml_tag_name(cls, v):
        # -- Have to do it this way cus' the WUFI file structure is a mess
        # Input is a dict like: '{'PEF0': Tag(text='1.1', tag='PEF0', attrib={'unit': 'Btu/Btu'})}'
        input_tag = list(v.values())[-1]
        input_dict: Dict = unpack_xml_tag(input_tag)  # type: ignore
        result = convert(input_dict["value"], str(input_dict["unit_type"]), "G/KWH")
        if not result:
            msg = f"Error converting {input_dict['value']} from {input_dict['unit_type']} to G/KWH"
            raise Exception(msg)
        return float(result)


class PEFactorsUserDef(BaseModel):
    __root__: Any

    @validator("__root__", pre=True)
    def unpack_xml_tag_name(cls, v):
        # -- Have to do it this way cus' the WUFI file structure is a mess
        # Input is a dict like: '{'PEF0': Tag(text='1.1', tag='PEF0', attrib={'unit': 'Btu/Btu'})}'
        input_tag = list(v.values())[-1]
        input_dict: Dict = unpack_xml_tag(input_tag)  # type: ignore
        result = convert(input_dict["value"], str(input_dict["unit_type"]), "KWH/KWH")
        if not result:
            msg = f"Error converting {input_dict['value']} from {input_dict['unit_type']} to KWH/KWH"
            raise Exception(msg)
        return float(result)


class MonthlyClimateTemp_Item(BaseModel):
    Item: Optional[unit.DegreeC]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class MonthlyClimateRadiation_Item(BaseModel):
    Item: Optional[unit.kWh_per_M2]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class PH_ClimateLocation(BaseModel):
    Selection: int
    Name: Optional[str]
    Comment: Optional[str]
    DailyTemperatureSwingSummer: unit.DegreeDeltaK
    AverageWindSpeed: unit.M_per_Second

    Latitude: unit.CardinalDegrees
    Longitude: unit.CardinalDegrees
    dUTC: int

    HeightNNWeatherStation: unit.M
    HeightNNBuilding: unit.M

    ClimateZone: int
    GroundThermalConductivity: unit.Watts_per_MK
    GroundHeatCapacitiy: unit.Joule_per_KGK
    GroundDensity: unit.KG_per_M3
    DepthGroundwater: unit.M
    FlowRateGroundwater: unit.M_per_Day

    TemperatureMonthly: List[Optional[MonthlyClimateTemp_Item]]
    DewPointTemperatureMonthly: List[Optional[MonthlyClimateTemp_Item]]
    SkyTemperatureMonthly: List[Optional[MonthlyClimateTemp_Item]]

    NorthSolarRadiationMonthly: List[Optional[MonthlyClimateRadiation_Item]]
    EastSolarRadiationMonthly: List[Optional[MonthlyClimateRadiation_Item]]
    SouthSolarRadiationMonthly: List[Optional[MonthlyClimateRadiation_Item]]
    WestSolarRadiationMonthly: List[Optional[MonthlyClimateRadiation_Item]]
    GlobalSolarRadiationMonthly: List[Optional[MonthlyClimateRadiation_Item]]

    TemperatureHeating1: Optional[unit.DegreeC]
    NorthSolarRadiationHeating1: Optional[unit.Watts_per_M2]
    EastSolarRadiationHeating1: Optional[unit.Watts_per_M2]
    SouthSolarRadiationHeating1: Optional[unit.Watts_per_M2]
    WestSolarRadiationHeating1: Optional[unit.Watts_per_M2]
    GlobalSolarRadiationHeating1: Optional[unit.Watts_per_M2]

    TemperatureHeating2: Optional[unit.DegreeC]
    NorthSolarRadiationHeating2: Optional[unit.Watts_per_M2]
    EastSolarRadiationHeating2: Optional[unit.Watts_per_M2]
    SouthSolarRadiationHeating2: Optional[unit.Watts_per_M2]
    WestSolarRadiationHeating2: Optional[unit.Watts_per_M2]
    GlobalSolarRadiationHeating2: Optional[unit.Watts_per_M2]

    TemperatureCooling: Optional[unit.DegreeC]
    NorthSolarRadiationCooling: Optional[unit.Watts_per_M2]
    EastSolarRadiationCooling: Optional[unit.Watts_per_M2]
    SouthSolarRadiationCooling: Optional[unit.Watts_per_M2]
    WestSolarRadiationCooling: Optional[unit.Watts_per_M2]
    GlobalSolarRadiationCooling: Optional[unit.Watts_per_M2]

    TemperatureCooling2: Optional[unit.DegreeC]
    NorthSolarRadiationCooling2: Optional[unit.Watts_per_M2]
    EastSolarRadiationCooling2: Optional[unit.Watts_per_M2]
    SouthSolarRadiationCooling2: Optional[unit.Watts_per_M2]
    WestSolarRadiationCooling2: Optional[unit.Watts_per_M2]
    GlobalSolarRadiationCooling2: Optional[unit.Watts_per_M2]

    SelectionPECO2Factor: int
    PEFactorsUserDef: Optional[List[PEFactorsUserDef]]
    CO2FactorsUserDef: Optional[List[CO2FactorsUserDef]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)

    def set_standard_pe_factors(self, PH_CertificateCriteriaNum: int) -> None:
        """Set the PE-Factors from the Standards-Library based on the PH_CertificateCriteria."""
        self.PEFactorsUserDef = []

        # -- Load in the Factor values from the Standards library
        factor_mapping = {
            PhiusCertificationProgram.DEFAULT: phius_source_energy_factors.factors_2021,
            PhiusCertificationProgram.PHIUS_2015: phius_source_energy_factors.factors_2018,
            PhiusCertificationProgram.PHIUS_2018: phius_source_energy_factors.factors_2018,
            PhiusCertificationProgram.ITALIAN: phius_source_energy_factors.factors_2021,
            PhiusCertificationProgram.PHIUS_2018_CORE: phius_source_energy_factors.factors_2018,
            PhiusCertificationProgram.PHIUS_2018_ZERO: phius_source_energy_factors.factors_2018,
            PhiusCertificationProgram.PHIUS_2021_CORE: phius_source_energy_factors.factors_2021,
            PhiusCertificationProgram.PHIUS_2021_ZERO: phius_source_energy_factors.factors_2021,
        }
        factor_dict = factor_mapping[PhiusCertificationProgram(PH_CertificateCriteriaNum)]
        factor_objects = factors.build_factors_from_library(factor_dict)

        # -- Mimic the XML structure normal data would come in as
        # -- and build up all the PEFactorsUserDef objects
        for i, obj in enumerate(factor_objects):
            obj.unit
            x = {f"PEF{i}": Tag(text=str(obj.value), tag=f"PEF{0}", attrib={"unit": obj.unit})}
            self.PEFactorsUserDef.append(PEFactorsUserDef.parse_obj(x))

    def set_standard_co2_factors(self, PH_CertificateCriteriaNum: int) -> None:
        """Set the CO2-Factors from the Standards-Library based on the PH_CertificateCriteria."""
        self.CO2FactorsUserDef = []

        # -- Load in the Factor values from the Standards library
        factor_mapping = {
            PhiusCertificationProgram.DEFAULT: phius_CO2_factors.factors_2021,
            PhiusCertificationProgram.PHIUS_2015: phius_CO2_factors.factors_2018,
            PhiusCertificationProgram.PHIUS_2018: phius_CO2_factors.factors_2018,
            PhiusCertificationProgram.ITALIAN: phius_CO2_factors.factors_2021,
            PhiusCertificationProgram.PHIUS_2018_CORE: phius_CO2_factors.factors_2018,
            PhiusCertificationProgram.PHIUS_2018_ZERO: phius_CO2_factors.factors_2018,
            PhiusCertificationProgram.PHIUS_2021_CORE: phius_CO2_factors.factors_2021,
            PhiusCertificationProgram.PHIUS_2021_ZERO: phius_CO2_factors.factors_2021,
        }
        factor_dict = factor_mapping[PhiusCertificationProgram(PH_CertificateCriteriaNum)]
        factor_objects = factors.build_factors_from_library(factor_dict)

        # -- Mimic the XML structure normal data would come in as
        # -- and build up all the PEFactorsUserDef objects
        for i, obj in enumerate(factor_objects):
            x = {f"CO2F{i}": Tag(text=str(obj.value), tag=f"CO2F{0}", attrib={"unit": obj.unit})}
            self.CO2FactorsUserDef.append(CO2FactorsUserDef.parse_obj(x))


class ClimateLocation(BaseModel):
    Selection: int

    Latitude_DB: Optional[unit.CardinalDegrees]
    Longitude_DB: Optional[unit.CardinalDegrees]
    HeightNN_DB: Optional[unit.M]
    dUTC_DB: Optional[float]

    Albedo: int
    GroundReflShort: unit._Percentage
    GroundReflLong: unit._Percentage
    GroundEmission: unit._Percentage
    CloudIndex: unit._Percentage
    CO2concenration: unit.MG_per_M3
    Unit_CO2concentration: unit.PartsPerMillionByVolume
    PH_ClimateLocation: Optional[PH_ClimateLocation]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Geometry


class Vertix(BaseModel):
    # Note: Bizarrely, even in IP units WUFI XML, the Vertices are in Meters.
    IdentNr: int
    X: float
    Y: float
    Z: float

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class IdentNr(BaseModel):
    IdentNr: int
    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Polygon(BaseModel):
    IdentNr: int
    NormalVectorX: float
    NormalVectorY: float
    NormalVectorZ: float
    IdentNrPoints: List[IdentNr]
    IdentNrPolygonsInside: Optional[List[IdentNr]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Graphics_3D(BaseModel):
    Vertices: List[Vertix]
    Polygons: List[Polygon]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Building and Components


class Room(BaseModel):
    Name: str
    Type: int
    IdentNrUtilizationPatternVent: int
    IdentNrVentilationUnit: int
    Quantity: int
    AreaRoom: Optional[unit.M2]
    ClearRoomHeight: Optional[unit.M]
    DesignVolumeFlowRateSupply: unit.M3_per_Hour
    DesignVolumeFlowRateExhaust: unit.M3_per_Hour

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class LoadPerson(BaseModel):
    Name: str
    IdentNrUtilizationPattern: int
    ChoiceActivityPersons: int
    NumberOccupants: unit._Float
    FloorAreaUtilizationZone: unit.M2

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class LoadsLighting(BaseModel):
    Name: str
    RoomCategory: int
    ChoiceLightTransmissionGlazing: int
    LightingControl: int
    WithinThermalEnvelope: bool
    MotionDetector: bool
    FacadeIncludingWindows: bool
    FractionTreatedFloorArea: unit._Percentage
    DeviationFromNorth: unit.AngleDegree
    RoomDepth: unit.M
    RoomWidth: unit.M
    RoomHeight: unit.M
    LintelHeight: unit.M
    WindowWidth: unit.M
    InstalledLightingPower: unit.Watts_per_M2
    LightingFullLoadHours: unit.Hours_per_Year

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class ExhaustVent(BaseModel):
    Name: Optional[str]
    Type: int
    ExhaustVolumeFlowRate: Optional[unit.M3_per_Hour]
    RunTimePerYear: Optional[unit.Hours_per_Year]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class HomeDevice(BaseModel):
    # -- Basic
    Comment: Optional[str]
    ReferenceQuantity: Optional[int]
    Quantity: Optional[int]
    InConditionedSpace: Optional[bool]
    ReferenceEnergyDemandNorm: Optional[int]
    EnergyDemandNorm: Optional[unit.kWh]
    EnergyDemandNormUse: Optional[unit.kWh]
    CEF_CombinedEnergyFactor: Optional[unit._Percentage]
    Type: int

    # -- Cook-tops
    CookingWith: Optional[int]

    # -- Lighting
    FractionHightEfficiency: Optional[unit._Percentage]

    # -- Dishwasher
    CookingWith: Optional[int]

    # -- Dryer
    Dryer_Choice: Optional[int]
    GasConsumption: Optional[unit.kWh]
    EfficiencyFactorGas: Optional[unit._Percentage]
    FieldUtilizationFactorPreselection: Optional[int]
    FieldUtilizationFactor: Optional[unit._Float]

    #  -- Washer
    Connection: Optional[int]
    UtilizationFactor: Optional[unit._Float]
    CapacityClothesWasher: Optional[unit.M3]
    MEF_ModifiedEnergyFactor: Optional[unit._Float]

    # -- Dishwasher
    DishwasherCapacityPreselection: Optional[int]
    DishwasherCapacityInPlace: Optional[unit._Float]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class IdentNrPolygons(BaseModel):
    IdentNr: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Component(BaseModel):
    IdentNr: int
    Name: Optional[str]
    Visual: bool
    Type: int
    IdentNrColorI: int
    IdentNrColorE: int
    InnerAttachment: int
    OuterAttachment: int
    IdentNr_ComponentInnerSurface: Optional[int]
    IdentNrAssembly: Optional[int]
    IdentNrWindowType: Optional[int]
    IdentNrPolygons: List[IdentNrPolygons]

    # Window-Specific Attributes
    DepthWindowReveal: Optional[unit.M]
    IdentNrSolarProtection: Optional[int]
    IdentNrOverhang: Optional[int]
    DefaultCorrectionShadingMonth: Optional[unit._Percentage]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class ThermalBridge(BaseModel):
    Name: Optional[str]
    Type: int
    Length: Optional[unit.M]
    PsiValue: Optional[unit.Watts_per_MK]
    IdentNrOptionalClimate: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Zone(BaseModel):
    Name: str
    KindZone: int
    KindAttachedZone: Optional[int]
    TemperatureReductionFactorUserDefined: Optional[unit._Percentage]
    IdentNr: int
    RoomsVentilation: Optional[List[Room]]
    LoadsPersonsPH: Optional[List[LoadPerson]]
    LoadsLightingsPH: Optional[List[LoadsLighting]]
    GrossVolume_Selection: int
    GrossVolume: Optional[unit.M3]
    NetVolume_Selection: int
    NetVolume: Optional[unit.M3]
    FloorArea_Selection: int
    FloorArea: Optional[unit.M2]
    ClearanceHeight_Selection: int
    ClearanceHeight: Optional[unit.M]
    SpecificHeatCapacity_Selection: int
    SpecificHeatCapacity: unit.Wh_per_M2K
    IdentNrPH_Building: int
    OccupantQuantityUserDef: unit._Int
    NumberBedrooms: Optional[unit._Int]
    SummerNaturalVentilationDay: Optional[unit.ACH]
    SummerNaturalVentilationNight: Optional[unit.ACH]

    HomeDevice: Optional[List[HomeDevice]]
    ExhaustVents: Optional[List[ExhaustVent]]
    ThermalBridges: Optional[List[ThermalBridge]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Building(BaseModel):
    Components: List[Component]
    Zones: List[Zone]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- HVAC


class Twig(BaseModel):
    Name: str
    IdentNr: int
    PipingLength: Optional[unit.M]
    PipeMaterial: int
    PipingDiameter: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Branch(BaseModel):
    Name: Optional[str]
    IdentNr: int
    PipingLength: Optional[unit.M]
    PipeMaterial: int
    PipingDiameter: int
    Twigs: Optional[List[Twig]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Trunc(BaseModel):
    Name: Optional[str]
    IdentNr: int
    PipingLength: Optional[unit.M]
    PipeMaterial: int
    PipingDiameter: int
    CountUnitsOrFloors: int
    DemandRecirculation: bool
    Branches: Optional[List[Branch]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class DistributionDHW(BaseModel):
    CalculationMethodIndividualPipes: int
    DemandRecirculation: bool
    SelectionhotWaterFixtureEff: int
    NumberOfBathrooms: Optional[int]
    AllPipesAreInsulated: bool
    SelectionUnitsOrFloors: int
    PipeMaterialSimplifiedMethod: int
    PipeDiameterSimplifiedMethod: Optional[float]
    TemperatureRoom_WR: Optional[unit.DegreeC]
    DesignFlowTemperature_WR: Optional[unit.DegreeC]
    DailyRunningHoursCirculation_WR: Optional[unit.Hour]
    LengthCirculationPipes_WR: Optional[unit.M]
    HeatLossCoefficient_WR: Optional[unit.Watts_per_MK]
    LengthIndividualPipes_WR: Optional[unit.M]
    ExteriorPipeDiameter_WR: Optional[unit.M]
    Truncs: Optional[List[Trunc]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class DistributionCooling(BaseModel):
    CoolingViaRecirculation: Optional[bool]
    RecirculatingAirOnOff: Optional[bool]
    MaxRecirculationAirCoolingPower: Optional[unit.KiloWatt]
    MinTempCoolingCoilRecirculatingAir: Optional[unit.DegreeC]
    RecirculationCoolingCOP: Optional[unit._Percentage]
    RecirculationAirVolume: Optional[unit.M3_per_Hour]
    ControlledRecirculationVolumeFlow: bool

    # -- Ventilation Air
    CoolingViaVentilationAir: Optional[bool]
    SupplyAirCoolingOnOff: Optional[bool]
    SupplyAirCoolinCOP: Optional[unit._Percentage]
    MaxSupplyAirCoolingPower: Optional[unit.KiloWatt]
    MinTemperatureCoolingCoilSupplyAir: Optional[unit.DegreeC]

    # -- Dehumidification
    Dehumidification: Optional[bool]
    DehumdificationCOP: Optional[unit._Percentage]
    UsefullDehumidificationHeatLoss: Optional[bool]

    # -- Panel
    PanelCooling: Optional[bool]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class SupportiveDevice(BaseModel):
    Name: Optional[str]
    Type: int
    Quantity: int
    InConditionedSpace: Optional[bool]
    NormEnergyDemand: Optional[unit.Watts]
    Controlled: Optional[bool]
    PeriodOperation: Optional[unit.KiloHours_per_Year]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class AssignedVentUnit(BaseModel):
    IdentNrVentUnit: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Duct(BaseModel):
    Name: Optional[str]
    IdentNr: int
    DuctDiameter: Optional[unit.MM]
    DuctShapeHeight: Optional[unit.MM]
    DuctShapeWidth: Optional[unit.MM]
    DuctLength: Optional[unit.M]
    InsulationThickness: Optional[unit.MM]
    ThermalConductivity: Optional[unit.Watts_per_MK]
    Quantity: Optional[unit._Int]
    DuctType: int
    DuctShape: int
    IsReflective: bool
    AssignedVentUnits: Optional[List[AssignedVentUnit]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class PHDistribution(BaseModel):
    # TODO DistributionHeating: DistributionHeating
    DistributionDHW: Optional[DistributionDHW]
    DistributionCooling: Optional[DistributionCooling]
    DistributionVentilation: Optional[List[Duct]]
    UseDefaultValues: bool
    DeviceInConditionedSpace: Optional[bool]
    SupportiveDevices: Optional[List[SupportiveDevice]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class ZoneCoverage(BaseModel):
    IdentNrZone: int
    CoverageHeating: float
    CoverageCooling: float
    CoverageVentilation: float
    CoverageHumidification: float
    CoverageDehumidification: float

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class PH_Parameters(BaseModel):
    # -- Heat Pump
    InConditionedSpace: Optional[bool]
    AuxiliaryEnergy: Optional[unit.Watts]
    AuxiliaryEnergyDHW: Optional[unit.Watts]
    AnnualCOP: Optional[unit.kWh_per_kWh]
    TotalSystemPerformanceRatioHeatGenerator: Optional[unit._Percentage]
    HPType: Optional[int]
    RatedCOP1: Optional[unit._Percentage]
    RatedCOP2: Optional[unit._Percentage]
    AmbientTemperature1: Optional[unit.DegreeC]
    AmbientTemperature2: Optional[unit.DegreeC]

    # -- Ventilation
    Quantity: Optional[int]
    HumidityRecoveryEfficiency: Optional[unit._Percentage]
    ElectricEfficiency: Optional[unit.Wh_per_M3]
    DefrostRequired: Optional[bool]
    FrostProtection: Optional[bool]
    TemperatureBelowDefrostUsed: Optional[unit.DegreeC]
    NoSummerBypass: Optional[bool]

    # -- HP Water Heater
    HPWH_EF: Optional[unit._Percentage]

    # -- Water Storage
    QauntityWS: Optional[int]
    SolarThermalStorageCapacity: Optional[unit.Liter]
    StorageLossesStandby: Optional[unit.Watts_per_DegreeK]
    TotalSolarThermalStorageLosses: Optional[unit.Watts_per_DegreeK]
    InputOption: Optional[int]
    AverageHeatReleaseStorage: Optional[unit.Watts]
    TankRoomTemp: Optional[unit.DegreeC]
    TypicalStorageWaterTemperature: Optional[unit.DegreeC]

    # -- PV System
    SelectionLocation: Optional[int]
    SelectionOnSiteUtilization: Optional[int]
    SelectionUtilization: Optional[int]
    ArraySizePV: Optional[float]
    PhotovoltaicRenewableEnergy: Optional[unit.kWh]
    OnsiteUtilization: Optional[unit._Percentage]

    # -- Boilers
    EnergySourceBoilerType: Optional[int]
    CondensingBoiler: Optional[bool]
    BoilerEfficiency30: Optional[unit._Percentage]
    BoilerEfficiencyNominalOutput: Optional[float]
    AverageReturnTemperatureMeasured30Load: Optional[float]
    AverageBoilerTemperatureDesign70_55: Optional[float]
    AverageBoilerTemperatureDesign55_45: Optional[float]
    AverageBoilerTemperatureDesign35_28: Optional[float]
    StandbyHeatLossBoiler70: Optional[float]
    MaximalBoilerPower: Optional[float]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class DHW_Parameters(BaseModel):
    CoverageWithinSystem: unit._Percentage
    Unit: float
    Selection: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Heating_Parameters(BaseModel):
    CoverageWithinSystem: unit._Percentage
    Unit: float
    Selection: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Cooling_Parameters(BaseModel):
    CoverageWithinSystem: Optional[unit._Percentage]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Ventilation_Parameters(BaseModel):
    CoverageWithinSystem: Optional[unit._Percentage]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Device(BaseModel):
    Name: Optional[str]
    IdentNr: int
    SystemType: int
    TypeDevice: int

    UsedFor_Heating: bool
    UsedFor_DHW: bool
    UsedFor_Cooling: bool
    UsedFor_Ventilation: bool
    UsedFor_Humidification: bool
    UsedFor_Dehumidification: bool

    PH_Parameters: Optional[PH_Parameters]
    DHW_Parameters: Optional[DHW_Parameters]
    Heating_Parameters: Optional[Heating_Parameters]
    Cooling_Parameters: Optional[Cooling_Parameters]
    Ventilation_Parameters: Optional[Ventilation_Parameters]

    HeatRecovery: Optional[unit._Percentage]
    MoistureRecovery: Optional[unit._Percentage]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class System(BaseModel):
    Name: str
    Type: int
    IdentNr: int
    ZonesCoverage: List[ZoneCoverage]
    PHDistribution: PHDistribution
    Devices: List[Device]

    @validator("ZonesCoverage", pre=True)
    def unpack_zone_coverage(cls, v):
        return v

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Systems(BaseModel):
    Systems: List[System]


# ------------------------------------------------------------------------------
# -- Foundations


class FoundationInterface(BaseModel):
    # -- Common Attributes
    Name: Optional[str]
    SettingFloorSlabType: int
    FloorSlabType: int

    # -- Heated Basement
    FloorSlabArea: Optional[unit.M2]
    U_ValueBasementSlab: Optional[unit.Watts_per_M2K]
    FloorSlabPerimeter: Optional[unit.M]
    U_ValueBasementWall: Optional[unit.Watts_per_M2K]
    DepthBasementBelowGroundSurface: Optional[unit.M]

    # -- Unheated Basement
    HeightBasementWallAboveGrade: Optional[unit.M]
    FloorCeilingArea: Optional[unit.M]
    U_ValueCeilingToUnheatedCellar: Optional[unit.Watts_per_M2K]
    U_ValueWallAboveGround: Optional[unit.Watts_per_M2K]
    BasementVolume: Optional[unit.M3]

    # -- Slab on Grade
    PositionPerimeterInsulation: Optional[int]
    PerimeterInsulationWidthDepth: Optional[unit.M]
    ConductivityPerimeterInsulation: Optional[unit.Watts_per_MK]
    ThicknessPerimeterInsulation: Optional[unit.M]

    # -- Vented Crawlspace
    U_ValueCrawlspaceFloor: Optional[unit.Watts_per_M2K]
    CrawlspaceVentOpenings: Optional[unit.M2]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Variants


class InternalGainsAdditionalData(BaseModel):
    EvaporationHeatPerPerson: unit.Watts
    HeatLossFluschingWC: bool
    QuantityWCs: unit._Int
    RoomCategory: int
    UseDefaultValuesSchool: bool
    MarginalPerformanceRatioDHW: Optional[unit._Percentage]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class PH_Building(BaseModel):
    IdentNr: int
    BuildingCategory: int
    OccupancyTypeResidential: Optional[int]
    OccupancyTypeNonResidential: Optional[int]
    BuildingStatus: int
    BuildingType: int
    OccupancySettingMethod: int
    NumberUnits: Optional[unit._Int]
    CountStories: Optional[int]
    EnvelopeAirtightnessCoefficient: unit.M3_per_Hour_per_M2
    SummerHRVHumidityRecovery: float
    FoundationInterfaces: Optional[List[FoundationInterface]]
    InternalGainsAdditionalData: Optional[InternalGainsAdditionalData]
    MechanicalRoomTemperature: unit.DegreeC
    IndoorTemperature: unit.DegreeC
    OverheatingTemperatureThreshold: unit.DegreeC
    NonCombustibleMaterials: bool

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class PassivehouseData(BaseModel):
    PH_CertificateCriteria: int
    PH_SelectionTargetData: int
    AnnualHeatingDemand: unit.kWh_per_M2
    AnnualCoolingDemand: unit.kWh_per_M2
    PeakHeatingLoad: unit.Watts_per_M2
    PeakCoolingLoad: unit.Watts_per_M2
    PH_Buildings: List[PH_Building]
    UseWUFIMeanMonthShading: bool

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Plugin(BaseModel):
    InsertPlugIn: Optional[bool]
    Name_dll: Optional[Any]
    StatusPlugIn: Optional[Any]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Variant(BaseModel):
    IdentNr: int
    Name: Optional[str]
    Remarks: Optional[str]
    PlugIn: Optional[Plugin]
    Graphics_3D: Graphics_3D
    Building: Building
    PassivehouseData: PassivehouseData
    HVAC: Systems
    ClimateLocation: ClimateLocation  # Be sure this comes AFTER PassiveHouseData to validate...

    @validator("HVAC", pre=True)
    def unpack_hvac(cls, v):
        return v

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)

    @validator("ClimateLocation", pre=False)
    def check_source_energy_factors(cls, v: ClimateLocation, values: Dict[str, Any]):
        """Ensure the ClimateLocation's Energy and CO2 conversion factor lists are populated properly.

        If the XML file is set to one of the 'standard' factor sets (USA, Germany, etc..),
        in that case the XML file not have any values, so load those from the Standards-Library.
        """
        if not v.PH_ClimateLocation:
            return v

        passivehouse_data: PassivehouseData = values["PassivehouseData"]

        if not v.PH_ClimateLocation.CO2FactorsUserDef:
            v.PH_ClimateLocation.set_standard_pe_factors(passivehouse_data.PH_CertificateCriteria)

        if not v.PH_ClimateLocation.PEFactorsUserDef:
            v.PH_ClimateLocation.set_standard_co2_factors(passivehouse_data.PH_CertificateCriteria)

        return v


# ------------------------------------------------------------------------------
# -- Constructions


class Material(BaseModel):
    Name: str
    ThermalConductivity: unit.Watts_per_MK
    BulkDensity: unit.KG_per_M3
    Porosity: unit._Percentage
    HeatCapacity: unit.Joule_per_KGK
    WaterVaporResistance: unit.WUFI_Vapor_Resistance_Factor
    ReferenceWaterContent: unit.KG_per_M3

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class DivisionV(BaseModel):
    Distance: unit.M
    ExpandingContracting: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class DivisionH(BaseModel):
    Distance: unit.M
    ExpandingContracting: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class MaterialIDNr(BaseModel):
    Type: int
    IdentNr_Object: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Layer(BaseModel):
    Thickness: unit.M
    Material: Material
    ExchangeDivisionHorizontal: Optional[List[DivisionH]]
    ExchangeDivisionVertical: Optional[List[DivisionV]]
    ExchangeMaterialIdentNrs: Optional[List[MaterialIDNr]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class ExchangeMaterial(BaseModel):
    IdentNr: int
    Name: str
    ThermalConductivity: unit.Watts_per_MK
    BulkDensity: unit.KG_per_M3
    HeatCapacity: unit.Joule_per_KGK

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Assembly(BaseModel):
    IdentNr: int
    Name: str
    Order_Layers: int
    Grid_Kind: int
    Layers: List[Layer]
    ExchangeMaterials: Optional[List[ExchangeMaterial]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WindowType(BaseModel):
    IdentNr: int
    Name: str
    Uw_Detailed: bool
    GlazingFrameDetailed: bool
    FrameFactor: unit._Percentage
    U_Value: unit.Watts_per_M2K
    U_Value_Glazing: unit.Watts_per_M2K
    MeanEmissivity: unit._Percentage
    g_Value: unit._Percentage
    SHGC_Hemispherical: unit._Percentage
    U_Value_Frame: unit.Watts_per_M2K

    # -- WUFI might not provide these...
    Frame_Width_Left: Optional[unit.M]
    Frame_Psi_Left: Optional[unit.Watts_per_MK]
    Frame_U_Left: Optional[unit.Watts_per_M2K]
    Glazing_Psi_Left: Optional[unit.Watts_per_MK]

    Frame_Width_Right: Optional[unit.M]
    Frame_Psi_Right: Optional[unit.Watts_per_MK]
    Frame_U_Right: Optional[unit.Watts_per_M2K]
    Glazing_Psi_Right: Optional[unit.Watts_per_MK]

    Frame_Width_Top: Optional[unit.M]
    Frame_Psi_Top: Optional[unit.Watts_per_MK]
    Frame_U_Top: Optional[unit.Watts_per_M2K]
    Glazing_Psi_Top: Optional[unit.Watts_per_MK]

    Frame_Width_Bottom: Optional[unit.M]
    Frame_Psi_Bottom: Optional[unit.Watts_per_MK]
    Frame_U_Bottom: Optional[unit.Watts_per_M2K]
    Glazing_Psi_Bottom: Optional[unit.Watts_per_MK]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class SolarProtectionType(BaseModel):
    IdentNr: int
    Name: str
    OperationMode: int
    MaxRedFactorRadiation: Optional[unit._Percentage]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Patterns (Schedules)


class UtilizationPatternVent(BaseModel):
    Name: str
    IdentNr: int
    OperatingDays: float
    OperatingWeeks: float
    Maximum_DOS: float
    Maximum_PDF: float
    Standard_DOS: float
    Standard_PDF: float
    Basic_DOS: float
    Basic_PDF: float
    Minimum_DOS: float
    Minimum_PDF: float

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class UtilizationPattern(BaseModel):
    IdentNr: int
    Name: str
    HeightUtilizationLevel: float
    BeginUtilization: unit.Hour
    EndUtilization: unit.Hour
    AnnualUtilizationDays: unit.Days_per_Year
    IlluminationLevel: unit.Lux
    RelativeAbsenteeism: unit._Percentage
    PartUseFactorPeriodForLighting: unit._Percentage

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Project


class Date_Project(BaseModel):
    Year: int
    Month: int
    Day: int
    Hour: int
    Minutes: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class ProjectData(BaseModel):
    Year_Construction: Optional[int]
    OwnerIsClient: Optional[bool]
    WhiteBackgroundPictureBuilding: Optional[bool]
    Customer_Name: Optional[str]
    Customer_Street: Optional[str]
    Customer_Locality: Optional[str]
    Customer_PostalCode: Optional[str]
    Customer_Tel: Optional[str]
    Customer_Email: Optional[str]
    Building_Name: Optional[str]
    Building_Street: Optional[str]
    Building_Locality: Optional[str]
    Building_PostalCode: Optional[str]
    Owner_Name: Optional[str]
    Owner_Street: Optional[str]
    Owner_Locality: Optional[str]
    Owner_PostalCode: Optional[str]
    Responsible_Name: Optional[str]
    Responsible_Street: Optional[str]
    Responsible_Locality: Optional[str]
    Responsible_PostalCode: Optional[str]
    Responsible_Tel: Optional[str]
    Responsible_LicenseNr: Optional[str]
    Responsible_Email: Optional[str]
    Date_Project: Optional[Date_Project]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Root


class WUFIplusProject(BaseModel):
    DataVersion: int
    UnitSystem: int
    ProgramVersion: str
    Scope: int
    DimensionsVisualizedGeometry: int
    ProjectData: ProjectData
    UtilizationPatternsPH: Optional[List[UtilizationPattern]]
    UtilisationPatternsVentilation: Optional[List[UtilizationPatternVent]]
    WindowTypes: Optional[List[WindowType]]
    Assemblies: Optional[List[Assembly]]
    Variants: Optional[List[Variant]]
    SolarProtectionTypes: Optional[List[SolarProtectionType]]

    @validator("UnitSystem", pre=True)
    def unpack_unit_system(cls, v) -> int:
        """
        Since the model gets converted to SI units when it is read in,
        always set this to 1, no matter what.
        """
        return 1

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)
