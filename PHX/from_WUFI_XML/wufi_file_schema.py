# -*- Python Version: 3.10 -*-

"""Pydantic Model for reading in WUFI-XML file format."""

from __future__ import annotations

from typing import Any

from honeybee_ph_standards.sourcefactors import factors, phius_CO2_factors, phius_source_energy_factors
from ph_units.converter import convert
from pydantic import BaseModel, validator

from PHX.from_WUFI_XML import wufi_file_types as wufi_unit
from PHX.from_WUFI_XML.read_WUFI_XML_file import Tag
from PHX.model.enums.phius_certification import PhiusCertificationProgram

# ------------------------------------------------------------------------------
# -- Unit Types

TagList = list[Tag]
TagDict = dict[str, Tag]
UnitDict = dict[str, Any]


def unpack_xml_tag(_input: TagList | TagDict | UnitDict | Tag) -> TagList | TagDict | UnitDict | str | None:
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
        input_dict: dict = unpack_xml_tag(input_tag)  # type: ignore
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
        input_dict: dict = unpack_xml_tag(input_tag)  # type: ignore
        result = convert(input_dict["value"], str(input_dict["unit_type"]), "KWH/KWH")
        if not result:
            msg = f"Error converting {input_dict['value']} from {input_dict['unit_type']} to KWH/KWH"
            raise Exception(msg)
        return float(result)


class WufiMonthlyClimateTemp_Item(BaseModel):
    Item: wufi_unit.DegreeC | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiMonthlyClimateRadiation_Item(BaseModel):
    Item: wufi_unit.kWh_per_M2 | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPH_ClimateLocation(BaseModel):
    Selection: int
    Name: str | None = None
    Comment: str | None = None
    DailyTemperatureSwingSummer: wufi_unit.DegreeDeltaK
    AverageWindSpeed: wufi_unit.M_per_Second

    Latitude: wufi_unit.CardinalDegrees
    Longitude: wufi_unit.CardinalDegrees
    dUTC: int

    HeightNNWeatherStation: wufi_unit.M | None = wufi_unit.M(0)
    HeightNNBuilding: wufi_unit.M | None = wufi_unit.M(0)

    ClimateZone: int
    GroundThermalConductivity: wufi_unit.Watts_per_MK
    GroundHeatCapacitiy: wufi_unit.Joule_per_KGK
    GroundDensity: wufi_unit.KG_per_M3
    DepthGroundwater: wufi_unit.M
    FlowRateGroundwater: wufi_unit.M_per_Day

    TemperatureMonthly: list[WufiMonthlyClimateTemp_Item | None]
    DewPointTemperatureMonthly: list[WufiMonthlyClimateTemp_Item | None]
    SkyTemperatureMonthly: list[WufiMonthlyClimateTemp_Item | None]

    NorthSolarRadiationMonthly: list[WufiMonthlyClimateRadiation_Item | None]
    EastSolarRadiationMonthly: list[WufiMonthlyClimateRadiation_Item | None]
    SouthSolarRadiationMonthly: list[WufiMonthlyClimateRadiation_Item | None]
    WestSolarRadiationMonthly: list[WufiMonthlyClimateRadiation_Item | None]
    GlobalSolarRadiationMonthly: list[WufiMonthlyClimateRadiation_Item | None]

    TemperatureHeating1: wufi_unit.DegreeC | None = None
    NorthSolarRadiationHeating1: wufi_unit.Watts_per_M2 | None = None
    EastSolarRadiationHeating1: wufi_unit.Watts_per_M2 | None = None
    SouthSolarRadiationHeating1: wufi_unit.Watts_per_M2 | None = None
    WestSolarRadiationHeating1: wufi_unit.Watts_per_M2 | None = None
    GlobalSolarRadiationHeating1: wufi_unit.Watts_per_M2 | None = None

    TemperatureHeating2: wufi_unit.DegreeC | None = None
    NorthSolarRadiationHeating2: wufi_unit.Watts_per_M2 | None = None
    EastSolarRadiationHeating2: wufi_unit.Watts_per_M2 | None = None
    SouthSolarRadiationHeating2: wufi_unit.Watts_per_M2 | None = None
    WestSolarRadiationHeating2: wufi_unit.Watts_per_M2 | None = None
    GlobalSolarRadiationHeating2: wufi_unit.Watts_per_M2 | None = None

    TemperatureCooling: wufi_unit.DegreeC | None = None
    NorthSolarRadiationCooling: wufi_unit.Watts_per_M2 | None = None
    EastSolarRadiationCooling: wufi_unit.Watts_per_M2 | None = None
    SouthSolarRadiationCooling: wufi_unit.Watts_per_M2 | None = None
    WestSolarRadiationCooling: wufi_unit.Watts_per_M2 | None = None
    GlobalSolarRadiationCooling: wufi_unit.Watts_per_M2 | None = None

    TemperatureCooling2: wufi_unit.DegreeC | None = None
    NorthSolarRadiationCooling2: wufi_unit.Watts_per_M2 | None = None
    EastSolarRadiationCooling2: wufi_unit.Watts_per_M2 | None = None
    SouthSolarRadiationCooling2: wufi_unit.Watts_per_M2 | None = None
    WestSolarRadiationCooling2: wufi_unit.Watts_per_M2 | None = None
    GlobalSolarRadiationCooling2: wufi_unit.Watts_per_M2 | None = None

    SelectionPECO2Factor: int
    PEFactorsUserDef: list[WufiPEFactorsUserDef] | None = None
    CO2FactorsUserDef: list[WufiCO2FactorsUserDef] | None = None

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

    Latitude_DB: wufi_unit.CardinalDegrees | None = None
    Longitude_DB: wufi_unit.CardinalDegrees | None = None
    HeightNN_DB: wufi_unit.M | None = None
    dUTC_DB: float | None = None

    Albedo: int
    GroundReflShort: wufi_unit._Percentage
    GroundReflLong: wufi_unit._Percentage
    GroundEmission: wufi_unit._Percentage
    CloudIndex: wufi_unit._Percentage
    CO2concenration: wufi_unit.MG_per_M3
    Unit_CO2concentration: wufi_unit.PartsPerMillionByVolume
    PH_ClimateLocation: WufiPH_ClimateLocation | None = None

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
    IdentNrPoints: list[WufiIdentNr]
    IdentNrPolygonsInside: list[WufiIdentNr] | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiGraphics_3D(BaseModel):
    Vertices: list[WufiVertix]
    Polygons: list[WufiPolygon]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Building and Components


class WufiRoom(BaseModel):
    Name: str
    Type: int
    IdentNrUtilizationPatternVent: int
    IdentNrVentilationUnit: int
    Quantity: int
    AreaRoom: wufi_unit.M2 | None = None
    ClearRoomHeight: wufi_unit.M | None = None
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
    Name: str | None = None
    Type: int
    ExhaustVolumeFlowRate: wufi_unit.M3_per_Hour | None = None
    RunTimePerYear: wufi_unit.Hours_per_Year | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiHomeDevice(BaseModel):
    # -- Basic
    Comment: str | None = None
    ReferenceQuantity: int | None = None
    Quantity: int | None = None
    InConditionedSpace: bool | None = None
    ReferenceEnergyDemandNorm: int | None = None
    EnergyDemandNorm: wufi_unit.kWh | None = None
    EnergyDemandNormUse: wufi_unit.kWh | None = None
    CEF_CombinedEnergyFactor: wufi_unit._Percentage | None = None
    Type: int

    # -- Cook-tops
    CookingWith: int | None = None

    # -- Lighting
    FractionHightEfficiency: wufi_unit._Percentage | None = None

    # -- Dishwasher
    CookingWith: int | None = None

    # -- Dryer
    Dryer_Choice: int | None = None
    GasConsumption: wufi_unit.kWh | None = None
    EfficiencyFactorGas: wufi_unit._Percentage | None = None
    FieldUtilizationFactorPreselection: int | None = None
    FieldUtilizationFactor: wufi_unit._Float | None = None

    #  -- Washer
    Connection: int | None = None
    UtilizationFactor: wufi_unit._Float | None = None
    CapacityClothesWasher: wufi_unit.M3 | None = None
    MEF_ModifiedEnergyFactor: wufi_unit._Float | None = None

    # -- Dishwasher
    DishwasherCapacityPreselection: int | None = None
    DishwasherCapacityInPlace: wufi_unit._Float | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiIdentNrPolygons(BaseModel):
    IdentNr: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiComponent(BaseModel):
    IdentNr: int
    Name: str | None = None
    Visual: bool
    Type: int
    IdentNrColorI: int
    IdentNrColorE: int
    InnerAttachment: int
    OuterAttachment: int
    IdentNr_ComponentInnerSurface: int | None = None
    IdentNrAssembly: int | None = None
    IdentNrWindowType: int | None = None
    IdentNrPolygons: list[WufiIdentNrPolygons]

    # Window-Specific Attributes
    DepthWindowReveal: wufi_unit.M | None = None
    IdentNrSolarProtection: int | None = None
    IdentNrOverhang: int | None = None
    DefaultCorrectionShadingMonth: wufi_unit._Percentage | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiThermalBridge(BaseModel):
    Name: str | None = None
    Type: int
    Length: wufi_unit.M | None = None
    PsiValue: wufi_unit.Watts_per_MK | None = None
    IdentNrOptionalClimate: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiZone(BaseModel):
    Name: str
    KindZone: int
    KindAttachedZone: int | None = None
    TemperatureReductionFactorUserDefined: wufi_unit._Percentage | None = None
    IdentNr: int
    RoomsVentilation: list[WufiRoom] | None = None
    LoadsPersonsPH: list[WufiLoadPerson] | None = None
    LoadsLightingsPH: list[WufiLoadsLighting] | None = None
    GrossVolume_Selection: int
    GrossVolume: wufi_unit.M3 | None = None
    NetVolume_Selection: int
    NetVolume: wufi_unit.M3 | None = None
    FloorArea_Selection: int
    FloorArea: wufi_unit.M2 | None = None
    ClearanceHeight_Selection: int
    ClearanceHeight: wufi_unit.M | None = None
    SpecificHeatCapacity_Selection: int
    SpecificHeatCapacity: wufi_unit.Wh_per_M2K
    IdentNrPH_Building: int
    OccupantQuantityUserDef: wufi_unit._Int
    NumberBedrooms: wufi_unit._Int | None = None
    SummerNaturalVentilationDay: wufi_unit.ACH | None = None
    SummerNaturalVentilationNight: wufi_unit.ACH | None = None

    HomeDevice: list[WufiHomeDevice] | None = None
    ExhaustVents: list[WufiExhaustVent] | None = None
    ThermalBridges: list[WufiThermalBridge] | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiBuilding(BaseModel):
    Components: list[WufiComponent]
    Zones: list[WufiZone]

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- HVAC


class WufiTwig(BaseModel):
    Name: str
    IdentNr: int
    PipingLength: wufi_unit.M | None = None
    PipeMaterial: int
    PipingDiameter: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiBranch(BaseModel):
    Name: str | None = None
    IdentNr: int
    PipingLength: wufi_unit.M | None = None
    PipeMaterial: int
    PipingDiameter: int
    Twigs: list[WufiTwig] | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiTrunc(BaseModel):
    Name: str | None = None
    IdentNr: int
    PipingLength: wufi_unit.M | None = None
    PipeMaterial: int
    PipingDiameter: int
    CountUnitsOrFloors: int
    DemandRecirculation: bool
    Branches: list[WufiBranch] | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDistributionDHW(BaseModel):
    CalculationMethodIndividualPipes: int
    DemandRecirculation: bool
    SelectionhotWaterFixtureEff: int
    NumberOfBathrooms: int | None = None
    AllPipesAreInsulated: bool
    SelectionUnitsOrFloors: int
    PipeMaterialSimplifiedMethod: int
    PipeDiameterSimplifiedMethod: float | None = None
    TemperatureRoom_WR: wufi_unit.DegreeC | None = None
    DesignFlowTemperature_WR: wufi_unit.DegreeC | None = None
    DailyRunningHoursCirculation_WR: wufi_unit.Hour | None = None
    LengthCirculationPipes_WR: wufi_unit.M | None = None
    HeatLossCoefficient_WR: wufi_unit.Watts_per_MK | None = None
    LengthIndividualPipes_WR: wufi_unit.M | None = None
    ExteriorPipeDiameter_WR: wufi_unit.M | None = None
    Truncs: list[WufiTrunc] | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDistributionCooling(BaseModel):
    CoolingViaRecirculation: bool | None = None
    RecirculatingAirOnOff: bool | None = None
    MaxRecirculationAirCoolingPower: wufi_unit.KiloWatt | None = None
    MinTempCoolingCoilRecirculatingAir: wufi_unit.DegreeC | None = None
    RecirculationCoolingCOP: wufi_unit._Percentage | None = None
    RecirculationAirVolume: wufi_unit.M3_per_Hour | None
    ControlledRecirculationVolumeFlow: bool

    # -- Ventilation Air
    CoolingViaVentilationAir: bool | None = None
    SupplyAirCoolingOnOff: bool | None = None
    SupplyAirCoolinCOP: wufi_unit._Percentage | None = None
    MaxSupplyAirCoolingPower: wufi_unit.KiloWatt | None = None
    MinTemperatureCoolingCoilSupplyAir: wufi_unit.DegreeC | None = None

    # -- Dehumidification
    Dehumidification: bool | None = None
    DehumdificationCOP: wufi_unit._Percentage | None = None
    UsefullDehumidificationHeatLoss: bool | None = None

    # -- Panel
    PanelCooling: bool | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiSupportiveDevice(BaseModel):
    Name: str | None = None
    Type: int
    Quantity: int
    InConditionedSpace: bool | None = None
    NormEnergyDemand: wufi_unit.Watts | None = None
    Controlled: bool | None = None
    PeriodOperation: wufi_unit.KiloHours_per_Year | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiAssignedVentUnit(BaseModel):
    IdentNrVentUnit: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDuct(BaseModel):
    Name: str | None = None
    IdentNr: int
    DuctDiameter: wufi_unit.MM | None = None
    DuctShapeHeight: wufi_unit.MM | None = None
    DuctShapeWidth: wufi_unit.MM | None = None
    DuctLength: wufi_unit.M | None = None
    InsulationThickness: wufi_unit.MM | None = None
    ThermalConductivity: wufi_unit.Watts_per_MK | None = None
    Quantity: wufi_unit._Int | None = None
    DuctType: int
    DuctShape: int
    IsReflective: bool
    AssignedVentUnits: list[WufiAssignedVentUnit] | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPHDistribution(BaseModel):
    # TODO DistributionHeating: DistributionHeating
    DistributionDHW: WufiDistributionDHW | None = None
    DistributionCooling: WufiDistributionCooling | None = None
    DistributionVentilation: list[WufiDuct] | None = None
    UseDefaultValues: bool
    DeviceInConditionedSpace: bool | None = None
    SupportiveDevices: list[WufiSupportiveDevice] | None = None

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
    InConditionedSpace: bool | None = None
    AuxiliaryEnergy: wufi_unit.Watts | None = None
    AuxiliaryEnergyDHW: wufi_unit.Watts | None = None
    AnnualCOP: wufi_unit.kWh_per_kWh | None = None
    TotalSystemPerformanceRatioHeatGenerator: wufi_unit._Percentage | None = None
    HPType: int | None = None
    RatedCOP1: wufi_unit._Percentage | None = None
    RatedCOP2: wufi_unit._Percentage | None = None
    AmbientTemperature1: wufi_unit.DegreeC | None = None
    AmbientTemperature2: wufi_unit.DegreeC | None = None

    # -- Ventilation
    Quantity: int | None = None
    HumidityRecoveryEfficiency: wufi_unit._Percentage | None = None
    ElectricEfficiency: wufi_unit.Wh_per_M3 | None = None
    DefrostRequired: bool | None = None
    FrostProtection: bool | None = None
    TemperatureBelowDefrostUsed: wufi_unit.DegreeC | None = None
    NoSummerBypass: bool | None = None

    # -- HP Water Heater
    HPWH_EF: wufi_unit._Percentage | None = None

    # -- Water Storage
    QauntityWS: int | None = None
    SolarThermalStorageCapacity: wufi_unit.Liter | None = None
    StorageLossesStandby: wufi_unit.Watts_per_DegreeK | None = None
    TotalSolarThermalStorageLosses: wufi_unit.Watts_per_DegreeK | None = None
    InputOption: int | None = None
    AverageHeatReleaseStorage: wufi_unit.Watts | None = None
    TankRoomTemp: wufi_unit.DegreeC | None = None
    TypicalStorageWaterTemperature: wufi_unit.DegreeC | None = None

    # -- PV System
    SelectionLocation: int | None = None
    SelectionOnSiteUtilization: int | None = None
    SelectionUtilization: int | None = None
    ArraySizePV: float | None = None
    PhotovoltaicRenewableEnergy: wufi_unit.kWh | None = None
    OnsiteUtilization: wufi_unit._Percentage | None = None

    # -- Boilers
    EnergySourceBoilerType: int | None = None
    CondensingBoiler: bool | None = None
    BoilerEfficiency30: wufi_unit._Percentage | None = None
    BoilerEfficiencyNominalOutput: float | None = None
    AverageReturnTemperatureMeasured30Load: float | None = None
    AverageBoilerTemperatureDesign70_55: float | None = None
    AverageBoilerTemperatureDesign55_45: float | None = None
    AverageBoilerTemperatureDesign35_28: float | None = None
    StandbyHeatLossBoiler70: float | None = None
    MaximalBoilerPower: float | None = None

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
    CoverageWithinSystem: wufi_unit._Percentage | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiVentilation_Parameters(BaseModel):
    CoverageWithinSystem: wufi_unit._Percentage | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiDevice(BaseModel):
    Name: str | None = None
    IdentNr: int
    SystemType: int
    TypeDevice: int

    UsedFor_Heating: bool
    UsedFor_DHW: bool
    UsedFor_Cooling: bool
    UsedFor_Ventilation: bool
    UsedFor_Humidification: bool
    UsedFor_Dehumidification: bool

    PH_Parameters: WufiPH_Parameters | None = None
    DHW_Parameters: WufiDHW_Parameters | None = None
    Heating_Parameters: WufiHeating_Parameters | None = None
    Cooling_Parameters: WufiCooling_Parameters | None = None
    Ventilation_Parameters: WufiVentilation_Parameters | None = None

    HeatRecovery: wufi_unit._Percentage | None = None
    MoistureRecovery: wufi_unit._Percentage | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiSystem(BaseModel):
    Name: str
    Type: int
    IdentNr: int
    ZonesCoverage: list[WufiZoneCoverage]
    PHDistribution: WufiPHDistribution
    Devices: list[WufiDevice]

    @validator("ZonesCoverage", allow_reuse=True, pre=True)
    def unpack_zone_coverage(cls, v):
        return v

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiSystems(BaseModel):
    Systems: list[WufiSystem]


# ------------------------------------------------------------------------------
# -- Foundations


class WufiFoundationInterface(BaseModel):
    # -- Common Attributes
    Name: str | None = None
    SettingFloorSlabType: int
    FloorSlabType: int

    # -- Heated Basement
    FloorSlabArea: wufi_unit.M2 | None = None
    U_ValueBasementSlab: wufi_unit.Watts_per_M2K | None = None
    FloorSlabPerimeter: wufi_unit.M | None = None
    U_ValueBasementWall: wufi_unit.Watts_per_M2K | None = None
    DepthBasementBelowGroundSurface: wufi_unit.M | None = None

    # -- Unheated Basement
    HeightBasementWallAboveGrade: wufi_unit.M | None = None
    FloorCeilingArea: wufi_unit.M2 | None = None
    U_ValueCeilingToUnheatedCellar: wufi_unit.Watts_per_M2K | None = None
    U_ValueWallAboveGround: wufi_unit.Watts_per_M2K | None = None
    BasementVolume: wufi_unit.M3 | None = None

    # -- Slab on Grade
    PositionPerimeterInsulation: int | None = None
    PerimeterInsulationWidthDepth: wufi_unit.M | None = None
    ConductivityPerimeterInsulation: wufi_unit.Watts_per_MK | None = None
    ThicknessPerimeterInsulation: wufi_unit.M | None = None

    # -- Vented Crawlspace
    U_ValueCrawlspaceFloor: wufi_unit.Watts_per_M2K | None = None
    CrawlspaceVentOpenings: wufi_unit.M2 | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


# ------------------------------------------------------------------------------
# -- Variants


class WufiInternalGainsAdditionalData(BaseModel):
    EvaporationHeatPerPerson: wufi_unit.Watts
    HeatLossFluschingWC: bool
    QuantityWCs: wufi_unit._Int
    RoomCategory: int
    UseDefaultValuesSchool: bool
    MarginalPerformanceRatioDHW: wufi_unit._Percentage | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPH_Building(BaseModel):
    IdentNr: int
    BuildingCategory: int
    OccupancyTypeResidential: int | None = None
    OccupancyTypeNonResidential: int | None = None
    BuildingStatus: int
    BuildingType: int
    OccupancySettingMethod: int
    NumberUnits: wufi_unit._Int | None = None
    CountStories: int | None = None
    InfiltrationACH50: wufi_unit.ACH | None = None
    NetAirVolumePressTest: wufi_unit.M3 | None = None
    EnvelopeAirtightnessCoefficient: wufi_unit.M3_per_Hour_per_M2 | None = None
    SummerHRVHumidityRecovery: float
    FoundationInterfaces: list[WufiFoundationInterface] | None = None
    InternalGainsAdditionalData: WufiInternalGainsAdditionalData | None = None
    MechanicalRoomTemperature: wufi_unit.DegreeC
    IndoorTemperature: wufi_unit.DegreeC
    OverheatingTemperatureThreshold: wufi_unit.DegreeC
    NonCombustibleMaterials: bool
    BuildingWindExposure: int = 1

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)

    @validator("BuildingWindExposure", allow_reuse=True, pre=True)
    def validate_wind_exposure(cls, v: int | None):
        if v is None:
            return 1
        return v


class WufiPassivehouseData(BaseModel):
    PH_CertificateCriteria: int
    PH_SelectionTargetData: int
    AnnualHeatingDemand: wufi_unit.kWh_per_M2
    AnnualCoolingDemand: wufi_unit.kWh_per_M2
    PeakHeatingLoad: wufi_unit.Watts_per_M2
    PeakCoolingLoad: wufi_unit.Watts_per_M2
    PH_Buildings: list[WufiPH_Building]
    UseWUFIMeanMonthShading: bool

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiPlugin(BaseModel):
    InsertPlugIn: bool | None = None
    Name_dll: Any | None = None
    StatusPlugIn: Any | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiVariant(BaseModel):
    IdentNr: int
    Name: str | None = None
    Remarks: str | None = None
    PlugIn: WufiPlugin | None = None
    Graphics_3D: WufiGraphics_3D
    Building: WufiBuilding
    PassivehouseData: WufiPassivehouseData
    HVAC: WufiSystems
    ClimateLocation: WufiClimateLocation  # Be sure this comes AFTER PassiveHouseData to validate...

    @validator("HVAC", allow_reuse=True, pre=True)
    def unpack_hvac(cls, v: WufiSystems):
        return v

    @validator("ClimateLocation", pre=False)
    def check_source_energy_factors(cls, v: WufiClimateLocation, values: dict[str, Any]):
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


class WufiColor(BaseModel):
    Alpha: int
    Red: int
    Green: int
    Blue: int

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiMaterial(BaseModel):
    Name: str
    ThermalConductivity: wufi_unit.Watts_per_MK
    BulkDensity: wufi_unit.KG_per_M3
    Porosity: wufi_unit._Percentage
    HeatCapacity: wufi_unit.Joule_per_KGK
    WaterVaporResistance: wufi_unit.WUFI_Vapor_Resistance_Factor
    ReferenceWaterContent: wufi_unit.KG_per_M3
    Color: WufiColor | None = None

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
    ExchangeDivisionHorizontal: list[WufiDivisionH] | None = None
    ExchangeDivisionVertical: list[WufiDivisionV] | None = None
    ExchangeMaterialIdentNrs: list[WufiMaterialIDNr] | None = None

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
    Layers: list[WufiLayer]
    ExchangeMaterials: list[WufiExchangeMaterial] | None = None

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
    Frame_Width_Left: wufi_unit.M | None = None
    Frame_Psi_Left: wufi_unit.Watts_per_MK | None = None
    Frame_U_Left: wufi_unit.Watts_per_M2K | None = None
    Glazing_Psi_Left: wufi_unit.Watts_per_MK | None = None

    Frame_Width_Right: wufi_unit.M | None = None
    Frame_Psi_Right: wufi_unit.Watts_per_MK | None = None
    Frame_U_Right: wufi_unit.Watts_per_M2K | None = None
    Glazing_Psi_Right: wufi_unit.Watts_per_MK | None = None

    Frame_Width_Top: wufi_unit.M | None = None
    Frame_Psi_Top: wufi_unit.Watts_per_MK | None = None
    Frame_U_Top: wufi_unit.Watts_per_M2K | None = None
    Glazing_Psi_Top: wufi_unit.Watts_per_MK | None = None

    Frame_Width_Bottom: wufi_unit.M | None = None
    Frame_Psi_Bottom: wufi_unit.Watts_per_MK | None = None
    Frame_U_Bottom: wufi_unit.Watts_per_M2K | None = None
    Glazing_Psi_Bottom: wufi_unit.Watts_per_MK | None = None

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)


class WufiSolarProtectionType(BaseModel):
    IdentNr: int
    Name: str
    OperationMode: int
    MaxRedFactorRadiation: wufi_unit._Percentage | None = None

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
    Year_Construction: int | None = None
    OwnerIsClient: bool | None = None
    WhiteBackgroundPictureBuilding: bool | None = None
    Customer_Name: str | None = None
    Customer_Street: str | None = None
    Customer_Locality: str | None = None
    Customer_PostalCode: str | None = None
    Customer_Tel: str | None = None
    Customer_Email: str | None = None
    Building_Name: str | None = None
    Building_Street: str | None = None
    Building_Locality: str | None = None
    Building_PostalCode: str | None = None
    Owner_Name: str | None = None
    Owner_Street: str | None = None
    Owner_Locality: str | None = None
    Owner_PostalCode: str | None = None
    Responsible_Name: str | None = None
    Responsible_Street: str | None = None
    Responsible_Locality: str | None = None
    Responsible_PostalCode: str | None = None
    Responsible_Tel: str | None = None
    Responsible_LicenseNr: str | None = None
    Responsible_Email: str | None = None
    Date_Project: WufiDateProject | None = None

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
    UtilizationPatternsPH: list[WufiUtilizationPattern] | None = None
    UtilisationPatternsVentilation: list[WufiUtilizationPatternVent] | None = None
    WindowTypes: list[WufiWindowType] | None = None
    Assemblies: list[WufiAssembly] | None = None
    Variants: list[WufiVariant] | None = None
    SolarProtectionTypes: list[WufiSolarProtectionType] | None = None

    @validator("UnitSystem", allow_reuse=True, pre=True)
    def unpack_unit_system(cls, v) -> int:
        """
        Since the model gets converted to SI units when it is read in,
        always set this to 1, no matter what.
        """
        return 1

    _unpack_xml_tag_name = validator("*", allow_reuse=True, pre=True)(unpack_xml_tag)
