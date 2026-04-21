# -*- Python Version: 3.10 -*-

"""Valid 'types' for Mech Equipment Options."""

from enum import Enum


class PhxFuelType(Enum):
    """Fuel type for combustion-based heating equipment.

    Values:
        NATURAL_GAS: Natural gas fuel.
        OIL: Fuel oil.
        WOOD_LOG: Wood log fuel.
        WOOD_PELLET: Wood pellet fuel.
    """

    NATURAL_GAS = 1
    OIL = 2
    WOOD_LOG = 3
    WOOD_PELLET = 4
    # HARD_COAL_CGS_70_PHC = 'HARD_COAL_CGS_70_PHC'
    # HARD_COAL_CGS_35_PHC = 'HARD_COAL_CGS_35_PHC'
    # HARD_COAL_HS_0_PHC = 'HARD_COAL_HS_0_PHC'
    # GAS_CGS_70_PHC = 'GAS_CGS_70_PHC'
    # GAS_CGS_35_PHC = 'GAS_CGS_35_PHC'
    # GAS_HS_0_PHC = 'GAS_HS_0_PHC'
    # OIL_CGS_70_PHC = 'OIL_CGS_70_PHC'
    # OIL_CGS_35_PHC = 'OIL_CGS_35_PHC'
    # OIL_HS_0_PHC = 'OIL_HS_0_PHC'


class SystemType(Enum):
    """Classification of mechanical system types in the energy model.

    Values:
        ANY: Matches any system type (wildcard).
        VENTILATION: Mechanical ventilation system (HRV/ERV).
        ELECTRIC: Direct electric heating system.
        BOILER: Combustion boiler system.
        DISTRICT_HEAT: District heating connection.
        HEAT_PUMP: Heat pump system.
        USER_DEFINED: User-specified custom system.
        WATER_STORAGE: Hot water storage tank system.
        PHOTOVOLTAIC: Photovoltaic solar panel system.
    """

    ANY = 0
    VENTILATION = 1
    ELECTRIC = 2
    BOILER = 3
    DISTRICT_HEAT = 4
    HEAT_PUMP = 5
    USER_DEFINED = 7
    WATER_STORAGE = 8
    PHOTOVOLTAIC = 10


class DeviceType(Enum):
    """Classification of individual HVAC device types.

    Values:
        VENTILATION: Ventilation unit (HRV/ERV).
        ELECTRIC: Direct electric heating device.
        BOILER: Combustion boiler device.
        DISTRICT_HEAT: District heating device.
        HEAT_PUMP: Heat pump device.
        WATER_STORAGE: Hot water storage tank.
        PHOTOVOLTAIC: Photovoltaic panel array.
    """

    VENTILATION = 1
    ELECTRIC = 2
    BOILER = 3
    DISTRICT_HEAT = 4
    HEAT_PUMP = 5
    WATER_STORAGE = 8
    PHOTOVOLTAIC = 10


class HeatPumpType(Enum):
    """Heat pump performance data entry method.

    Values:
        COMBINED: Combined heating and cooling heat pump.
        ANNUAL: Annual average COP performance data.
        RATED_MONTHLY: Monthly rated COP performance data.
        HOT_WATER: Dedicated domestic hot water heat pump.
    """

    COMBINED = 2
    ANNUAL = 3
    RATED_MONTHLY = 4
    HOT_WATER = 5


class CoolingType(Enum):
    """Classification of active cooling delivery methods.

    Values:
        NONE: No active cooling.
        VENTILATION: Cooling via the ventilation supply air.
        RECIRCULATION: Cooling via recirculated air.
        DEHUMIDIFICATION: Cooling via dehumidification.
        PANEL: Cooling via radiant panels.
    """

    NONE = 0
    VENTILATION = 1
    RECIRCULATION = 2
    DEHUMIDIFICATION = 3
    PANEL = 4


class PhxHotWaterPipingCalcMethod(Enum):
    """Calculation method for hot water distribution piping losses.

    Values:
        SIMPLIFIED_INDIVIDUAL_PIPES: Simplified method specifying individual pipe runs.
        SIMPLIFIED_HOT_WATER_CALCULATOR: Simplified method using the hot water calculator.
        HOT_WATER_PIPING_UNIT_METHOD: Detailed method based on per-unit piping lengths.
        HOT_WATER_PIPING_FLOOR_METHOD: Detailed method based on per-floor piping lengths.
    """

    SIMPLIFIED_INDIVIDUAL_PIPES = 1
    SIMPLIFIED_HOT_WATER_CALCULATOR = 2
    HOT_WATER_PIPING_UNIT_METHOD = 3
    HOT_WATER_PIPING_FLOOR_METHOD = 4


class PhxHotWaterPipingMaterial(Enum):
    """Material type for hot water distribution piping.

    Values:
        COPPER_M: Copper pipe, Type M (thin wall).
        COPPER_L: Copper pipe, Type L (medium wall).
        COPPER_K: Copper pipe, Type K (thick wall).
        CPVC_CTS_SDR: CPVC pipe, CTS SDR rating.
        CPVC_SCH_40: CPVC pipe, Schedule 40.
        PEX: Cross-linked polyethylene (PEX) pipe.
        PE: Polyethylene (PE) pipe.
        PEX_CTS_SDR: PEX pipe, CTS SDR rating.
    """

    COPPER_M = 1
    COPPER_L = 2
    COPPER_K = 3
    CPVC_CTS_SDR = 4
    CPVC_SCH_40 = 5
    PEX = 6
    PE = 7
    PEX_CTS_SDR = 8


class PhxHotWaterPipingInchDiameterType(Enum):
    """Nominal pipe diameter in inches for hot water piping.

    Member names encode the diameter as ``_W_N_D_IN`` where W is the whole
    number, N is the numerator, and D is the denominator of the fractional inch.

    Values:
        _0_3_8_IN: 3/8 inch diameter.
        _0_1_2_IN: 1/2 inch diameter.
        _0_5_8_IN: 5/8 inch diameter.
        _0_3_4_IN: 3/4 inch diameter.
        _1_0_0_IN: 1 inch diameter.
        _1_1_4_IN: 1-1/4 inch diameter.
        _1_1_2_IN: 1-1/2 inch diameter.
        _2_0_0_IN: 2 inch diameter.
    """

    _0_3_8_IN = 1
    _0_1_2_IN = 2
    _0_5_8_IN = 3
    _0_3_4_IN = 4
    _1_0_0_IN = 5
    _1_1_4_IN = 6
    _1_1_2_IN = 7
    _2_0_0_IN = 8

    @property
    def name_as_float(self) -> float:
        """Return the name as a float. Oh my fucking god IP units are so stupid."""
        # -- Remove the '_IN' suffix
        name = str(self.name).split("_IN")[0]

        # -- Remove the prefix underscore
        name = name[1:]

        # -- Split the fraction
        parts = str(name).split("_")
        try:
            fraction = f"{float(parts[1]) / float(parts[2])}"
        except ZeroDivisionError:
            fraction = 0.0

        # -- Return the whole
        return float(parts[0]) + float(fraction)

    @classmethod
    def nearest_key(cls, value: float) -> "PhxHotWaterPipingInchDiameterType":
        """Return a new Enum object which most closely matches the supplied value."""
        return min(PhxHotWaterPipingInchDiameterType, key=lambda d: abs(d.name_as_float - value))


class PhxHotWaterInputOptions(Enum):
    """Input method for hot water storage tank loss specification.

    Values:
        SPEC_TOTAL_LOSSES: Specify total storage losses directly.
        SPEC_STANDBY_LOSSES: Specify standby losses from the tank data sheet.
        TOTAL_LOSSES: Use calculated total losses.
    """

    SPEC_TOTAL_LOSSES = 1
    SPEC_STANDBY_LOSSES = 2
    TOTAL_LOSSES = 3


class PhxHotWaterTankType(Enum):
    """Hot water storage tank usage classification.

    Values:
        NONE: No storage tank.
        DHW_AND_HEATING: Tank serves both domestic hot water and space heating.
        DHW_ONLY: Tank serves domestic hot water only.
    """

    NONE = 0
    DHW_AND_HEATING = 1
    DHW_ONLY = 2

    @classmethod
    def from_hbph_type(cls, _hbph_type):
        """Return a new PhxHotWaterTankType based on the Honeybee-PH Tank Type."""
        _mapping = {
            "0-NO STORAGE TANK": cls.NONE,
            "1-DHW AND HEATING": cls.DHW_AND_HEATING,
            "2-DHW ONLY": cls.DHW_ONLY,
        }
        return _mapping[_hbph_type]


class PhxHotWaterSelectionUnitsOrFloors(Enum):
    """Selection basis for hot water piping calculation scope.

    Values:
        PH_CASE: Use the PH case default (number of dwelling units).
        USER_DETERMINED: User specifies the number of units or floors.
    """

    PH_CASE = 1
    USER_DETERMINED = 2


class PhxExhaustVentType(Enum):
    """Type of dedicated exhaust ventilation device.

    Values:
        DRYER: Clothes dryer exhaust.
        KITCHEN_HOOD: Kitchen range hood exhaust.
        USER_DEFINED: User-specified exhaust device.
    """

    DRYER = 1
    KITCHEN_HOOD = 2
    USER_DEFINED = 3


class PhxVentDuctType(Enum):
    """Ventilation duct direction classification.

    Values:
        SUPPLY: Supply air duct (outdoor air to rooms).
        EXHAUST: Exhaust air duct (rooms to outdoors).
    """

    SUPPLY = 1
    EXHAUST = 2


class PhxSupportiveDeviceType(Enum):
    """Type of supportive (auxiliary) mechanical device.

    Values:
        HEAT_CIRCULATING_PUMP: Circulation pump for the heating loop.
        DHW_CIRCULATING_PUMP: Recirculation pump for the DHW loop.
        DHW_STORAGE_LOAD_PUMP: Pump loading the DHW storage tank.
        OTHER: Other auxiliary device.
    """

    HEAT_CIRCULATING_PUMP = 4
    DHW_CIRCULATING_PUMP = 6
    DHW_STORAGE_LOAD_PUMP = 7
    OTHER = 10


class PhxSummerBypassMode(Enum):
    """Summer bypass mode for the heat recovery ventilator.

    Values:
        NONE: No summer bypass.
        TEMP_CONTROLLED: Bypass activated by temperature differential.
        ENTHALPY_CONTROLLED: Bypass activated by enthalpy differential.
        ALWAYS: Bypass always active in summer.
    """

    NONE = 1
    TEMP_CONTROLLED = 2
    ENTHALPY_CONTROLLED = 3
    ALWAYS = 4


class PhxNighttimeVentilationControl(Enum):
    """Control strategy for nighttime ventilation cooling.

    Values:
        TEMPERATURE_CONTROLLED: Nighttime ventilation activated by temperature.
        HUMIDITY_CONTROLLED: Nighttime ventilation activated by humidity.
    """

    TEMPERATURE_CONTROLLED = 1
    HUMIDITY_CONTROLLED = 2
