# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Pydantic Model for reading in WUFI-XML file format."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from honeybee_ph_standards.sourcefactors import factors, phius_CO2_factors, phius_source_energy_factors
from ph_units.converter import convert
from pydantic import BaseModel, validator

from PHX.from_WUFI_XML import wufi_file_types as wufi_unit
from PHX.from_WUFI_XML.read_WUFI_XML_file import Tag
from PHX.model.enums.phius_certification import PhiusCertificationProgram

# ------------------------------------------------------------------------------
# -- Unit Types

TagList = List[Tag]
TagDict = Dict[str, Tag]
UnitDict = Dict[str, Any]


def unpack_xml_tag(_input: Union[TagList, TagDict, UnitDict, Tag]) -> Union[TagList, TagDict, UnitDict, str, None]:
    """This validator should run first before any unit-conversion. This will
    unpack the Tag object and return the .text, or a dict with the unit and the
    value if it is a unit-type.


    _value can be:
        * List: [...]
        * Dict: {'Year': Tag(...), 'Month': Tag(...), 'Day': Tag(...), 'Hour': Tag(...), 'Minutes': Tag(...)}
        * Tag (no unit):  Tag(text='New York, NY', tag='Customer_Locality', attrib={})
        * Tag (with unit):  Tag(text='7.5', tag='BeginUtilization', attrib={'unit': 'hr'})
    """

    if isinstance(_input, Tag):
        # print(f"  <{type(_input).__name__}> {_input}")
        # -- If it is a unit-type, pass back a dict with the unit and the value
        # -- this will get unpacked and used by the unit-type converter.
        unit_type = getattr(_input, "attrib", {}).get("unit", None)
        if unit_type:
            return {"value": _input.text, "unit_type": unit_type}

        # -- Otherwise, just pass back the .text attribute of the Tag
        if _input.text == "None":
            return None
        else:
            return _input.text
    else:
        # print(f"{type(_input).__name__}")
        return _input


# ------------------------------------------------------------------------------
# -- Climate


class WufiCO2FactorsUserDef(BaseModel):
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


class WufiPEFactorsUserDef(BaseModel):
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


class WufiMonthlyClimateTemp_Item(BaseModel):
    Item: Optional[wufi_unit.DegreeC] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiMonthlyClimateRadiation_Item(BaseModel):
    Item: Optional[wufi_unit.kWh_per_M2] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPH_ClimateLocation(BaseModel):
    Selection: int
    Name: Optional[str] = None
    Comment: Optional[str] = None
    DailyTemperatureSwingSummer: wufi_unit.DegreeDeltaK
    AverageWindSpeed: wufi_unit.M_per_Second

    Latitude: wufi_unit.CardinalDegrees
    Longitude: wufi_unit.CardinalDegrees
    dUTC: int

    HeightNNWeatherStation: Optional[wufi_unit.M] = wufi_unit.M(0)
    HeightNNBuilding: Optional[wufi_unit.M] = wufi_unit.M(0)

    ClimateZone: int
    GroundThermalConductivity: wufi_unit.Watts_per_MK
    GroundHeatCapacitiy: wufi_unit.Joule_per_KGK
    GroundDensity: wufi_unit.KG_per_M3
    DepthGroundwater: wufi_unit.M
    FlowRateGroundwater: wufi_unit.M_per_Day

    TemperatureMonthly: List[Optional[WufiMonthlyClimateTemp_Item]]
    DewPointTemperatureMonthly: List[Optional[WufiMonthlyClimateTemp_Item]]
    SkyTemperatureMonthly: List[Optional[WufiMonthlyClimateTemp_Item]]

    NorthSolarRadiationMonthly: List[Optional[WufiMonthlyClimateRadiation_Item]]
    EastSolarRadiationMonthly: List[Optional[WufiMonthlyClimateRadiation_Item]]
    SouthSolarRadiationMonthly: List[Optional[WufiMonthlyClimateRadiation_Item]]
    WestSolarRadiationMonthly: List[Optional[WufiMonthlyClimateRadiation_Item]]
    GlobalSolarRadiationMonthly: List[Optional[WufiMonthlyClimateRadiation_Item]]

    TemperatureHeating1: Optional[wufi_unit.DegreeC] = None
    NorthSolarRadiationHeating1: Optional[wufi_unit.Watts_per_M2] = None
    EastSolarRadiationHeating1: Optional[wufi_unit.Watts_per_M2] = None
    SouthSolarRadiationHeating1: Optional[wufi_unit.Watts_per_M2] = None
    WestSolarRadiationHeating1: Optional[wufi_unit.Watts_per_M2] = None
    GlobalSolarRadiationHeating1: Optional[wufi_unit.Watts_per_M2] = None

    TemperatureHeating2: Optional[wufi_unit.DegreeC] = None
    NorthSolarRadiationHeating2: Optional[wufi_unit.Watts_per_M2] = None
    EastSolarRadiationHeating2: Optional[wufi_unit.Watts_per_M2] = None
    SouthSolarRadiationHeating2: Optional[wufi_unit.Watts_per_M2] = None
    WestSolarRadiationHeating2: Optional[wufi_unit.Watts_per_M2] = None
    GlobalSolarRadiationHeating2: Optional[wufi_unit.Watts_per_M2] = None

    TemperatureCooling: Optional[wufi_unit.DegreeC] = None
    NorthSolarRadiationCooling: Optional[wufi_unit.Watts_per_M2] = None
    EastSolarRadiationCooling: Optional[wufi_unit.Watts_per_M2] = None
    SouthSolarRadiationCooling: Optional[wufi_unit.Watts_per_M2] = None
    WestSolarRadiationCooling: Optional[wufi_unit.Watts_per_M2] = None
    GlobalSolarRadiationCooling: Optional[wufi_unit.Watts_per_M2] = None

    TemperatureCooling2: Optional[wufi_unit.DegreeC] = None
    NorthSolarRadiationCooling2: Optional[wufi_unit.Watts_per_M2] = None
    EastSolarRadiationCooling2: Optional[wufi_unit.Watts_per_M2] = None
    SouthSolarRadiationCooling2: Optional[wufi_unit.Watts_per_M2] = None
    WestSolarRadiationCooling2: Optional[wufi_unit.Watts_per_M2] = None
    GlobalSolarRadiationCooling2: Optional[wufi_unit.Watts_per_M2] = None

    SelectionPECO2Factor: int
    PEFactorsUserDef: Optional[List[WufiPEFactorsUserDef]] = None
    CO2FactorsUserDef: Optional[List[WufiCO2FactorsUserDef]] = None

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
            self.PEFactorsUserDef.append(WufiPEFactorsUserDef.parse_obj(x))

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
            self.CO2FactorsUserDef.append(WufiCO2FactorsUserDef.parse_obj(x))


class WufiClimateLocation(BaseModel):
    Selection: int

    Latitude_DB: Optional[wufi_unit.CardinalDegrees] = None
    Longitude_DB: Optional[wufi_unit.CardinalDegrees] = None
    HeightNN_DB: Optional[wufi_unit.M] = None
    dUTC_DB: Optional[float] = None

    Albedo: int
    GroundReflShort: wufi_unit._Percentage
    GroundReflLong: wufi_unit._Percentage
    GroundEmission: wufi_unit._Percentage
    CloudIndex: wufi_unit._Percentage
    CO2concenration: wufi_unit.MG_per_M3
    Unit_CO2concentration: wufi_unit.PartsPerMillionByVolume
    PH_ClimateLocation: Optional[WufiPH_ClimateLocation] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Geometry


class WufiVertix(BaseModel):
    # Note: Bizarrely, even in IP units WUFI XML, the Vertices are in Meters.
    IdentNr: int
    X: float
    Y: float
    Z: float

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiIdentNr(BaseModel):
    IdentNr: int
    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPolygon(BaseModel):
    IdentNr: int
    NormalVectorX: float
    NormalVectorY: float
    NormalVectorZ: float
    IdentNrPoints: List[WufiIdentNr]
    IdentNrPolygonsInside: Optional[List[WufiIdentNr]] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiGraphics_3D(BaseModel):
    Vertices: List[WufiVertix]
    Polygons: List[WufiPolygon]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Building and Components


class WufiRoom(BaseModel):
    Name: str
    Type: int
    IdentNrUtilizationPatternVent: int
    IdentNrVentilationUnit: int
    Quantity: int
    AreaRoom: Optional[wufi_unit.M2] = None
    ClearRoomHeight: Optional[wufi_unit.M] = None
    DesignVolumeFlowRateSupply: wufi_unit.M3_per_Hour
    DesignVolumeFlowRateExhaust: wufi_unit.M3_per_Hour

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiLoadPerson(BaseModel):
    Name: str
    IdentNrUtilizationPattern: int
    ChoiceActivityPersons: int
    NumberOccupants: wufi_unit._Float
    FloorAreaUtilizationZone: wufi_unit.M2

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiLoadsLighting(BaseModel):
    Name: str
    RoomCategory: int
    ChoiceLightTransmissionGlazing: int
    LightingControl: int
    WithinThermalEnvelope: bool
    MotionDetector: bool
    FacadeIncludingWindows: bool
    FractionTreatedFloorArea: wufi_unit._Percentage
    DeviationFromNorth: wufi_unit.AngleDegree
    RoomDepth: wufi_unit.M
    RoomWidth: wufi_unit.M
    RoomHeight: wufi_unit.M
    LintelHeight: wufi_unit.M
    WindowWidth: wufi_unit.M
    InstalledLightingPower: wufi_unit.Watts_per_M2
    LightingFullLoadHours: wufi_unit.Hours_per_Year

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiExhaustVent(BaseModel):
    Name: Optional[str] = None
    Type: int
    ExhaustVolumeFlowRate: Optional[wufi_unit.M3_per_Hour] = None
    RunTimePerYear: Optional[wufi_unit.Hours_per_Year] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiHomeDevice(BaseModel):
    # -- Basic
    Comment: Optional[str] = None
    ReferenceQuantity: Optional[int] = None
    Quantity: Optional[int] = None
    InConditionedSpace: Optional[bool] = None
    ReferenceEnergyDemandNorm: Optional[int] = None
    EnergyDemandNorm: Optional[wufi_unit.kWh] = None
    EnergyDemandNormUse: Optional[wufi_unit.kWh] = None
    CEF_CombinedEnergyFactor: Optional[wufi_unit._Percentage] = None
    Type: int

    # -- Cook-tops
    CookingWith: Optional[int] = None

    # -- Lighting
    FractionHightEfficiency: Optional[wufi_unit._Percentage] = None

    # -- Dishwasher
    CookingWith: Optional[int] = None

    # -- Dryer
    Dryer_Choice: Optional[int] = None
    GasConsumption: Optional[wufi_unit.kWh] = None
    EfficiencyFactorGas: Optional[wufi_unit._Percentage] = None
    FieldUtilizationFactorPreselection: Optional[int] = None
    FieldUtilizationFactor: Optional[wufi_unit._Float] = None

    #  -- Washer
    Connection: Optional[int] = None
    UtilizationFactor: Optional[wufi_unit._Float] = None
    CapacityClothesWasher: Optional[wufi_unit.M3] = None
    MEF_ModifiedEnergyFactor: Optional[wufi_unit._Float] = None

    # -- Dishwasher
    DishwasherCapacityPreselection: Optional[int] = None
    DishwasherCapacityInPlace: Optional[wufi_unit._Float] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiIdentNrPolygons(BaseModel):
    IdentNr: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiComponent(BaseModel):
    IdentNr: int
    Name: Optional[str] = None
    Visual: bool
    Type: int
    IdentNrColorI: int
    IdentNrColorE: int
    InnerAttachment: int
    OuterAttachment: int
    IdentNr_ComponentInnerSurface: Optional[int] = None
    IdentNrAssembly: Optional[int] = None
    IdentNrWindowType: Optional[int] = None
    IdentNrPolygons: List[WufiIdentNrPolygons]

    # Window-Specific Attributes
    DepthWindowReveal: Optional[wufi_unit.M] = None
    IdentNrSolarProtection: Optional[int] = None
    IdentNrOverhang: Optional[int] = None
    DefaultCorrectionShadingMonth: Optional[wufi_unit._Percentage] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiThermalBridge(BaseModel):
    Name: Optional[str] = None
    Type: int
    Length: Optional[wufi_unit.M] = None
    PsiValue: Optional[wufi_unit.Watts_per_MK] = None
    IdentNrOptionalClimate: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiZone(BaseModel):
    Name: str
    KindZone: int
    KindAttachedZone: Optional[int] = None
    TemperatureReductionFactorUserDefined: Optional[wufi_unit._Percentage] = None
    IdentNr: int
    RoomsVentilation: Optional[List[WufiRoom]] = None
    LoadsPersonsPH: Optional[List[WufiLoadPerson]] = None
    LoadsLightingsPH: Optional[List[WufiLoadsLighting]] = None
    GrossVolume_Selection: int
    GrossVolume: Optional[wufi_unit.M3] = None
    NetVolume_Selection: int
    NetVolume: Optional[wufi_unit.M3] = None
    FloorArea_Selection: int
    FloorArea: Optional[wufi_unit.M2] = None
    ClearanceHeight_Selection: int
    ClearanceHeight: Optional[wufi_unit.M] = None
    SpecificHeatCapacity_Selection: int
    SpecificHeatCapacity: wufi_unit.Wh_per_M2K
    IdentNrPH_Building: int
    OccupantQuantityUserDef: wufi_unit._Int
    NumberBedrooms: Optional[wufi_unit._Int] = None
    SummerNaturalVentilationDay: Optional[wufi_unit.ACH] = None
    SummerNaturalVentilationNight: Optional[wufi_unit.ACH] = None

    HomeDevice: Optional[List[WufiHomeDevice]] = None
    ExhaustVents: Optional[List[WufiExhaustVent]] = None
    ThermalBridges: Optional[List[WufiThermalBridge]] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiBuilding(BaseModel):
    Components: List[WufiComponent]
    Zones: List[WufiZone]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- HVAC


class WufiTwig(BaseModel):
    Name: str
    IdentNr: int
    PipingLength: Optional[wufi_unit.M] = None
    PipeMaterial: int
    PipingDiameter: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiBranch(BaseModel):
    Name: Optional[str] = None
    IdentNr: int
    PipingLength: Optional[wufi_unit.M] = None
    PipeMaterial: int
    PipingDiameter: int
    Twigs: Optional[List[WufiTwig]] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiTrunc(BaseModel):
    Name: Optional[str] = None
    IdentNr: int
    PipingLength: Optional[wufi_unit.M] = None
    PipeMaterial: int
    PipingDiameter: int
    CountUnitsOrFloors: int
    DemandRecirculation: bool
    Branches: Optional[List[WufiBranch]] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDistributionDHW(BaseModel):
    CalculationMethodIndividualPipes: int
    DemandRecirculation: bool
    SelectionhotWaterFixtureEff: int
    NumberOfBathrooms: Optional[int] = None
    AllPipesAreInsulated: bool
    SelectionUnitsOrFloors: int
    PipeMaterialSimplifiedMethod: int
    PipeDiameterSimplifiedMethod: Optional[float] = None
    TemperatureRoom_WR: Optional[wufi_unit.DegreeC] = None
    DesignFlowTemperature_WR: Optional[wufi_unit.DegreeC] = None
    DailyRunningHoursCirculation_WR: Optional[wufi_unit.Hour] = None
    LengthCirculationPipes_WR: Optional[wufi_unit.M] = None
    HeatLossCoefficient_WR: Optional[wufi_unit.Watts_per_MK] = None
    LengthIndividualPipes_WR: Optional[wufi_unit.M] = None
    ExteriorPipeDiameter_WR: Optional[wufi_unit.M] = None
    Truncs: Optional[List[WufiTrunc]] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDistributionCooling(BaseModel):
    CoolingViaRecirculation: Optional[bool] = None
    RecirculatingAirOnOff: Optional[bool] = None
    MaxRecirculationAirCoolingPower: Optional[wufi_unit.KiloWatt] = None
    MinTempCoolingCoilRecirculatingAir: Optional[wufi_unit.DegreeC] = None
    RecirculationCoolingCOP: Optional[wufi_unit._Percentage] = None
    RecirculationAirVolume: Optional[wufi_unit.M3_per_Hour]
    ControlledRecirculationVolumeFlow: bool

    # -- Ventilation Air
    CoolingViaVentilationAir: Optional[bool] = None
    SupplyAirCoolingOnOff: Optional[bool] = None
    SupplyAirCoolinCOP: Optional[wufi_unit._Percentage] = None
    MaxSupplyAirCoolingPower: Optional[wufi_unit.KiloWatt] = None
    MinTemperatureCoolingCoilSupplyAir: Optional[wufi_unit.DegreeC] = None

    # -- Dehumidification
    Dehumidification: Optional[bool] = None
    DehumdificationCOP: Optional[wufi_unit._Percentage] = None
    UsefullDehumidificationHeatLoss: Optional[bool] = None

    # -- Panel
    PanelCooling: Optional[bool] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiSupportiveDevice(BaseModel):
    Name: Optional[str] = None
    Type: int
    Quantity: int
    InConditionedSpace: Optional[bool] = None
    NormEnergyDemand: Optional[wufi_unit.Watts] = None
    Controlled: Optional[bool] = None
    PeriodOperation: Optional[wufi_unit.KiloHours_per_Year] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiAssignedVentUnit(BaseModel):
    IdentNrVentUnit: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDuct(BaseModel):
    Name: Optional[str] = None
    IdentNr: int
    DuctDiameter: Optional[wufi_unit.MM] = None
    DuctShapeHeight: Optional[wufi_unit.MM] = None
    DuctShapeWidth: Optional[wufi_unit.MM] = None
    DuctLength: Optional[wufi_unit.M] = None
    InsulationThickness: Optional[wufi_unit.MM] = None
    ThermalConductivity: Optional[wufi_unit.Watts_per_MK] = None
    Quantity: Optional[wufi_unit._Int] = None
    DuctType: int
    DuctShape: int
    IsReflective: bool
    AssignedVentUnits: Optional[List[WufiAssignedVentUnit]] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPHDistribution(BaseModel):
    # TODO DistributionHeating: DistributionHeating
    DistributionDHW: Optional[WufiDistributionDHW] = None
    DistributionCooling: Optional[WufiDistributionCooling] = None
    DistributionVentilation: Optional[List[WufiDuct]] = None
    UseDefaultValues: bool
    DeviceInConditionedSpace: Optional[bool] = None
    SupportiveDevices: Optional[List[WufiSupportiveDevice]] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiZoneCoverage(BaseModel):
    IdentNrZone: int
    CoverageHeating: float
    CoverageCooling: float
    CoverageVentilation: float
    CoverageHumidification: float
    CoverageDehumidification: float

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPH_Parameters(BaseModel):
    # -- Heat Pump
    InConditionedSpace: Optional[bool] = None
    AuxiliaryEnergy: Optional[wufi_unit.Watts] = None
    AuxiliaryEnergyDHW: Optional[wufi_unit.Watts] = None
    AnnualCOP: Optional[wufi_unit.kWh_per_kWh] = None
    TotalSystemPerformanceRatioHeatGenerator: Optional[wufi_unit._Percentage] = None
    HPType: Optional[int] = None
    RatedCOP1: Optional[wufi_unit._Percentage] = None
    RatedCOP2: Optional[wufi_unit._Percentage] = None
    AmbientTemperature1: Optional[wufi_unit.DegreeC] = None
    AmbientTemperature2: Optional[wufi_unit.DegreeC] = None

    # -- Ventilation
    Quantity: Optional[int] = None
    HumidityRecoveryEfficiency: Optional[wufi_unit._Percentage] = None
    ElectricEfficiency: Optional[wufi_unit.Wh_per_M3] = None
    DefrostRequired: Optional[bool] = None
    FrostProtection: Optional[bool] = None
    TemperatureBelowDefrostUsed: Optional[wufi_unit.DegreeC] = None
    NoSummerBypass: Optional[bool] = None

    # -- HP Water Heater
    HPWH_EF: Optional[wufi_unit._Percentage] = None

    # -- Water Storage
    QauntityWS: Optional[int] = None
    SolarThermalStorageCapacity: Optional[wufi_unit.Liter] = None
    StorageLossesStandby: Optional[wufi_unit.Watts_per_DegreeK] = None
    TotalSolarThermalStorageLosses: Optional[wufi_unit.Watts_per_DegreeK] = None
    InputOption: Optional[int] = None
    AverageHeatReleaseStorage: Optional[wufi_unit.Watts] = None
    TankRoomTemp: Optional[wufi_unit.DegreeC] = None
    TypicalStorageWaterTemperature: Optional[wufi_unit.DegreeC] = None

    # -- PV System
    SelectionLocation: Optional[int] = None
    SelectionOnSiteUtilization: Optional[int] = None
    SelectionUtilization: Optional[int] = None
    ArraySizePV: Optional[float] = None
    PhotovoltaicRenewableEnergy: Optional[wufi_unit.kWh] = None
    OnsiteUtilization: Optional[wufi_unit._Percentage] = None

    # -- Boilers
    EnergySourceBoilerType: Optional[int] = None
    CondensingBoiler: Optional[bool] = None
    BoilerEfficiency30: Optional[wufi_unit._Percentage] = None
    BoilerEfficiencyNominalOutput: Optional[float] = None
    AverageReturnTemperatureMeasured30Load: Optional[float] = None
    AverageBoilerTemperatureDesign70_55: Optional[float] = None
    AverageBoilerTemperatureDesign55_45: Optional[float] = None
    AverageBoilerTemperatureDesign35_28: Optional[float] = None
    StandbyHeatLossBoiler70: Optional[float] = None
    MaximalBoilerPower: Optional[float] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDHW_Parameters(BaseModel):
    CoverageWithinSystem: wufi_unit._Percentage
    Unit: float
    Selection: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiHeating_Parameters(BaseModel):
    CoverageWithinSystem: wufi_unit._Percentage
    Unit: float
    Selection: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiCooling_Parameters(BaseModel):
    CoverageWithinSystem: Optional[wufi_unit._Percentage] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiVentilation_Parameters(BaseModel):
    CoverageWithinSystem: Optional[wufi_unit._Percentage] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDevice(BaseModel):
    Name: Optional[str] = None
    IdentNr: int
    SystemType: int
    TypeDevice: int

    UsedFor_Heating: bool
    UsedFor_DHW: bool
    UsedFor_Cooling: bool
    UsedFor_Ventilation: bool
    UsedFor_Humidification: bool
    UsedFor_Dehumidification: bool

    PH_Parameters: Optional[WufiPH_Parameters] = None
    DHW_Parameters: Optional[WufiDHW_Parameters] = None
    Heating_Parameters: Optional[WufiHeating_Parameters] = None
    Cooling_Parameters: Optional[WufiCooling_Parameters] = None
    Ventilation_Parameters: Optional[WufiVentilation_Parameters] = None

    HeatRecovery: Optional[wufi_unit._Percentage] = None
    MoistureRecovery: Optional[wufi_unit._Percentage] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiSystem(BaseModel):
    Name: str
    Type: int
    IdentNr: int
    ZonesCoverage: List[WufiZoneCoverage]
    PHDistribution: WufiPHDistribution
    Devices: List[WufiDevice]

    @validator("ZonesCoverage", allow_reuse=True, pre=True)
    def unpack_zone_coverage(cls, v):
        return v

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiSystems(BaseModel):
    Systems: List[WufiSystem]


# ------------------------------------------------------------------------------
# -- Foundations


class WufiFoundationInterface(BaseModel):
    # -- Common Attributes
    Name: Optional[str] = None
    SettingFloorSlabType: int
    FloorSlabType: int

    # -- Heated Basement
    FloorSlabArea: Optional[wufi_unit.M2] = None
    U_ValueBasementSlab: Optional[wufi_unit.Watts_per_M2K] = None
    FloorSlabPerimeter: Optional[wufi_unit.M] = None
    U_ValueBasementWall: Optional[wufi_unit.Watts_per_M2K] = None
    DepthBasementBelowGroundSurface: Optional[wufi_unit.M] = None

    # -- Unheated Basement
    HeightBasementWallAboveGrade: Optional[wufi_unit.M] = None
    FloorCeilingArea: Optional[wufi_unit.M2] = None
    U_ValueCeilingToUnheatedCellar: Optional[wufi_unit.Watts_per_M2K] = None
    U_ValueWallAboveGround: Optional[wufi_unit.Watts_per_M2K] = None
    BasementVolume: Optional[wufi_unit.M3] = None

    # -- Slab on Grade
    PositionPerimeterInsulation: Optional[int] = None
    PerimeterInsulationWidthDepth: Optional[wufi_unit.M] = None
    ConductivityPerimeterInsulation: Optional[wufi_unit.Watts_per_MK] = None
    ThicknessPerimeterInsulation: Optional[wufi_unit.M] = None

    # -- Vented Crawlspace
    U_ValueCrawlspaceFloor: Optional[wufi_unit.Watts_per_M2K] = None
    CrawlspaceVentOpenings: Optional[wufi_unit.M2] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Variants


class WufiInternalGainsAdditionalData(BaseModel):
    EvaporationHeatPerPerson: wufi_unit.Watts
    HeatLossFluschingWC: bool
    QuantityWCs: wufi_unit._Int
    RoomCategory: int
    UseDefaultValuesSchool: bool
    MarginalPerformanceRatioDHW: Optional[wufi_unit._Percentage] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPH_Building(BaseModel):
    IdentNr: int
    BuildingCategory: int
    OccupancyTypeResidential: Optional[int] = None
    OccupancyTypeNonResidential: Optional[int] = None
    BuildingStatus: int
    BuildingType: int
    OccupancySettingMethod: int
    NumberUnits: Optional[wufi_unit._Int] = None
    CountStories: Optional[int] = None
    EnvelopeAirtightnessCoefficient: wufi_unit.M3_per_Hour_per_M2
    SummerHRVHumidityRecovery: float
    FoundationInterfaces: Optional[List[WufiFoundationInterface]] = None
    InternalGainsAdditionalData: Optional[WufiInternalGainsAdditionalData] = None
    MechanicalRoomTemperature: wufi_unit.DegreeC
    IndoorTemperature: wufi_unit.DegreeC
    OverheatingTemperatureThreshold: wufi_unit.DegreeC
    NonCombustibleMaterials: bool
    BuildingWindExposure: int = 1

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)

    @validator("BuildingWindExposure", allow_reuse=True, pre=True)
    def validate_wind_exposure(cls, v: int | None):
        if v == None:
            return 1
        return v


class WufiPassivehouseData(BaseModel):
    PH_CertificateCriteria: int
    PH_SelectionTargetData: int
    AnnualHeatingDemand: wufi_unit.kWh_per_M2
    AnnualCoolingDemand: wufi_unit.kWh_per_M2
    PeakHeatingLoad: wufi_unit.Watts_per_M2
    PeakCoolingLoad: wufi_unit.Watts_per_M2
    PH_Buildings: List[WufiPH_Building]
    UseWUFIMeanMonthShading: bool

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPlugin(BaseModel):
    InsertPlugIn: Optional[bool] = None
    Name_dll: Optional[Any] = None
    StatusPlugIn: Optional[Any] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiVariant(BaseModel):
    IdentNr: int
    Name: Optional[str] = None
    Remarks: Optional[str] = None
    PlugIn: Optional[WufiPlugin] = None
    Graphics_3D: WufiGraphics_3D
    Building: WufiBuilding
    PassivehouseData: WufiPassivehouseData
    HVAC: WufiSystems
    ClimateLocation: WufiClimateLocation  # Be sure this comes AFTER PassiveHouseData to validate...

    @validator("HVAC", allow_reuse=True, pre=True)
    def unpack_hvac(cls, v: WufiSystems):
        return v

    @validator("ClimateLocation", pre=False)
    def check_source_energy_factors(cls, v: WufiClimateLocation, values: Dict[str, Any]):
        """Ensure the ClimateLocation's Energy and CO2 conversion factor lists are populated properly.

        If the XML file is set to one of the 'standard' factor sets (USA, Germany, etc..),
        in that case the XML file not have any values, so load those from the Standards-Library.
        """
        if not v.PH_ClimateLocation:
            return v

        passivehouse_data: WufiPassivehouseData = values["PassivehouseData"]

        if not v.PH_ClimateLocation.CO2FactorsUserDef:
            v.PH_ClimateLocation.set_standard_pe_factors(passivehouse_data.PH_CertificateCriteria)

        if not v.PH_ClimateLocation.PEFactorsUserDef:
            v.PH_ClimateLocation.set_standard_co2_factors(passivehouse_data.PH_CertificateCriteria)

        return v

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Constructions


class WufiMaterial(BaseModel):
    Name: str
    ThermalConductivity: wufi_unit.Watts_per_MK
    BulkDensity: wufi_unit.KG_per_M3
    Porosity: wufi_unit._Percentage
    HeatCapacity: wufi_unit.Joule_per_KGK
    WaterVaporResistance: wufi_unit.WUFI_Vapor_Resistance_Factor
    ReferenceWaterContent: wufi_unit.KG_per_M3

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDivisionV(BaseModel):
    Distance: wufi_unit.M
    ExpandingContracting: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDivisionH(BaseModel):
    Distance: wufi_unit.M
    ExpandingContracting: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiMaterialIDNr(BaseModel):
    Type: int
    IdentNr_Object: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiLayer(BaseModel):
    Thickness: wufi_unit.M
    Material: WufiMaterial
    ExchangeDivisionHorizontal: Optional[List[WufiDivisionH]] = None
    ExchangeDivisionVertical: Optional[List[WufiDivisionV]] = None
    ExchangeMaterialIdentNrs: Optional[List[WufiMaterialIDNr]] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiExchangeMaterial(BaseModel):
    IdentNr: int
    Name: str
    ThermalConductivity: wufi_unit.Watts_per_MK
    BulkDensity: wufi_unit.KG_per_M3
    HeatCapacity: wufi_unit.Joule_per_KGK

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiAssembly(BaseModel):
    IdentNr: int
    Name: str
    Order_Layers: int
    Grid_Kind: int
    Layers: List[WufiLayer]
    ExchangeMaterials: Optional[List[WufiExchangeMaterial]] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiWindowType(BaseModel):
    IdentNr: int
    Name: str
    Uw_Detailed: bool
    GlazingFrameDetailed: bool
    FrameFactor: wufi_unit._Percentage
    U_Value: wufi_unit.Watts_per_M2K
    U_Value_Glazing: wufi_unit.Watts_per_M2K
    MeanEmissivity: wufi_unit._Percentage
    g_Value: wufi_unit._Percentage
    SHGC_Hemispherical: wufi_unit._Percentage
    U_Value_Frame: wufi_unit.Watts_per_M2K

    # -- WUFI might not provide these...
    Frame_Width_Left: Optional[wufi_unit.M] = None
    Frame_Psi_Left: Optional[wufi_unit.Watts_per_MK] = None
    Frame_U_Left: Optional[wufi_unit.Watts_per_M2K] = None
    Glazing_Psi_Left: Optional[wufi_unit.Watts_per_MK] = None

    Frame_Width_Right: Optional[wufi_unit.M] = None
    Frame_Psi_Right: Optional[wufi_unit.Watts_per_MK] = None
    Frame_U_Right: Optional[wufi_unit.Watts_per_M2K] = None
    Glazing_Psi_Right: Optional[wufi_unit.Watts_per_MK] = None

    Frame_Width_Top: Optional[wufi_unit.M] = None
    Frame_Psi_Top: Optional[wufi_unit.Watts_per_MK] = None
    Frame_U_Top: Optional[wufi_unit.Watts_per_M2K] = None
    Glazing_Psi_Top: Optional[wufi_unit.Watts_per_MK] = None

    Frame_Width_Bottom: Optional[wufi_unit.M] = None
    Frame_Psi_Bottom: Optional[wufi_unit.Watts_per_MK] = None
    Frame_U_Bottom: Optional[wufi_unit.Watts_per_M2K] = None
    Glazing_Psi_Bottom: Optional[wufi_unit.Watts_per_MK] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiSolarProtectionType(BaseModel):
    IdentNr: int
    Name: str
    OperationMode: int
    MaxRedFactorRadiation: Optional[wufi_unit._Percentage] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Patterns (Schedules)


class WufiUtilizationPatternVent(BaseModel):
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


class WufiUtilizationPattern(BaseModel):
    IdentNr: int
    Name: str
    HeightUtilizationLevel: float
    BeginUtilization: wufi_unit.Hour
    EndUtilization: wufi_unit.Hour
    AnnualUtilizationDays: wufi_unit.Days_per_Year
    IlluminationLevel: wufi_unit.Lux
    RelativeAbsenteeism: wufi_unit._Percentage
    PartUseFactorPeriodForLighting: wufi_unit._Percentage

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Project


class WufiDateProject(BaseModel):
    Year: int
    Month: int
    Day: int
    Hour: int
    Minutes: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiProjectData(BaseModel):
    Year_Construction: Optional[int] = None
    OwnerIsClient: Optional[bool] = None
    WhiteBackgroundPictureBuilding: Optional[bool] = None
    Customer_Name: Optional[str] = None
    Customer_Street: Optional[str] = None
    Customer_Locality: Optional[str] = None
    Customer_PostalCode: Optional[str] = None
    Customer_Tel: Optional[str] = None
    Customer_Email: Optional[str] = None
    Building_Name: Optional[str] = None
    Building_Street: Optional[str] = None
    Building_Locality: Optional[str] = None
    Building_PostalCode: Optional[str] = None
    Owner_Name: Optional[str] = None
    Owner_Street: Optional[str] = None
    Owner_Locality: Optional[str] = None
    Owner_PostalCode: Optional[str] = None
    Responsible_Name: Optional[str] = None
    Responsible_Street: Optional[str] = None
    Responsible_Locality: Optional[str] = None
    Responsible_PostalCode: Optional[str] = None
    Responsible_Tel: Optional[str] = None
    Responsible_LicenseNr: Optional[str] = None
    Responsible_Email: Optional[str] = None
    Date_Project: Optional[WufiDateProject] = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Root


class WUFIplusProject(BaseModel):
    DataVersion: int
    UnitSystem: int
    ProgramVersion: str
    Scope: int
    DimensionsVisualizedGeometry: int
    ProjectData: WufiProjectData
    UtilizationPatternsPH: Optional[List[WufiUtilizationPattern]] = None
    UtilisationPatternsVentilation: Optional[List[WufiUtilizationPatternVent]] = None
    WindowTypes: Optional[List[WufiWindowType]] = None
    Assemblies: Optional[List[WufiAssembly]] = None
    Variants: Optional[List[WufiVariant]] = None
    SolarProtectionTypes: Optional[List[WufiSolarProtectionType]] = None

    @validator("UnitSystem", allow_reuse=True, pre=True)
    def unpack_unit_system(cls, v) -> int:
        """
        Since the model gets converted to SI units when it is read in,
        always set this to 1, no matter what.
        """
        return 1

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)
