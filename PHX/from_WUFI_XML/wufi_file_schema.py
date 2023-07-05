# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Pydantic Model for WUFI-XML file format."""

from __future__ import annotations
from typing import Optional, List, Dict, Union, Any
from pydantic import BaseModel, validator
from PHX.from_WUFI_XML.read_WUFI_XML_file import Tag
from ph_units.converter import convert
from PHX.from_WUFI_XML import wufi_file_types as unit

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
    PEFactorsUserDef: List[PEFactorsUserDef]
    CO2FactorsUserDef: List[CO2FactorsUserDef]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


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
    AreaRoom: unit.M2
    ClearRoomHeight: unit.M
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


class H_Device(BaseModel):
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

    # -- Cooktops
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
    Name: str
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
    IdentNr: int
    RoomsVentilation: List[Room]
    LoadsPersonsPH: Optional[List[LoadPerson]]
    LoadsLightingsPH: Optional[List[LoadsLighting]]
    GrossVolume_Selection: int
    GrossVolume: unit.M3
    NetVolume_Selection: int
    NetVolume: unit.M3
    FloorArea_Selection: int
    FloorArea: unit.M2
    ClearanceHeight_Selection: int
    ClearanceHeight: unit.M
    SpecificHeatCapacity_Selection: int
    SpecificHeatCapacity: unit.Wh_per_M2K
    IdentNrPH_Building: int
    OccupantQuantityUserDef: unit._Int
    NumberBedrooms: unit._Int
    SummerNaturalVentilationDay: unit.ACH
    SummerNaturalVentilationNight: unit.ACH

    HomeDevice: Optional[List[H_Device]]
    ExhaustVents: Optional[List[ExhaustVent]]
    ThermalBridges: Optional[List[ThermalBridge]]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Building(BaseModel):
    Components: List[Component]
    Zones: List[Zone]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- HVAC


class DistributionDHW(BaseModel):
    CalculationMethodIndividualPipes: int
    DemandRecirculation: bool
    SelectionhotWaterFixtureEff: int
    NumberOfBathrooms: int
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

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class SupportiveDevice(BaseModel):
    Name: Optional[str]
    Type: int
    Quantity: int
    InConditionedSpace: Optional[bool]
    NormEnergyDemand: Optional[unit.Watts]
    Controlled: Optional[bool]
    PeriodOperation: Optional[float]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class PHDistribution(BaseModel):
    DistributionDHW: Optional[DistributionDHW]
    # TODO DistributionHeating: DistributionHeating
    # TODO DistributionCooling: DistributionCooling
    # TODO DistributionVentilation: List[Duct]
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
    RatedCOP1: Optional[float]
    RatedCOP2: Optional[float]
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


class Device(BaseModel):
    Name: str
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
    Name: str
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
    ClimateLocation: ClimateLocation
    PassivehouseData: PassivehouseData
    HVAC: Systems

    @validator("HVAC", pre=True)
    def unpack_hvac(cls, v):
        return v

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


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


class Layer(BaseModel):
    Thickness: unit.M
    Material: Material

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class Assembly(BaseModel):
    IdentNr: int
    Name: str
    Order_Layers: int
    Grid_Kind: int
    Layers: List[Layer]

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

    Frame_Width_Left: unit.M
    Frame_Psi_Left: unit.Watts_per_MK
    Frame_U_Left: unit.Watts_per_M2K
    Glazing_Psi_Left: unit.Watts_per_MK

    Frame_Width_Right: unit.M
    Frame_Psi_Right: unit.Watts_per_MK
    Frame_U_Right: unit.Watts_per_M2K
    Glazing_Psi_Right: unit.Watts_per_MK

    Frame_Width_Top: unit.M
    Frame_Psi_Top: unit.Watts_per_MK
    Frame_U_Top: unit.Watts_per_M2K
    Glazing_Psi_Top: unit.Watts_per_MK

    Frame_Width_Bottom: unit.M
    Frame_Psi_Bottom: unit.Watts_per_MK
    Frame_U_Bottom: unit.Watts_per_M2K
    Glazing_Psi_Bottom: unit.Watts_per_MK

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
    Year_Construction: int
    OwnerIsClient: bool
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
    UtilizationPatternsPH: List[UtilizationPattern]
    UtilisationPatternsVentilation: List[UtilizationPatternVent]
    WindowTypes: List[WindowType]
    Assemblies: List[Assembly]
    Variants: List[Variant]
    SolarProtectionTypes: Optional[List[SolarProtectionType]]

    @validator("UnitSystem", pre=True)
    def unpack_unit_system(cls, v):
        """
        Since the model gets converted to SI units, always set this to 1, no matter what.
        """
        return 1

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)
