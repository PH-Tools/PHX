# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Valid 'types' for Mech Equipment Options."""

from enum import Enum

from honeybee_phhvac.hot_water_devices import PhHvacHotWaterTankType


class PhxFuelType(Enum):
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
    VENTILATION = 1
    ELECTRIC = 2
    BOILER = 3
    DISTRICT_HEAT = 4
    HEAT_PUMP = 5
    WATER_STORAGE = 8
    PHOTOVOLTAIC = 10


class HeatPumpType(Enum):
    COMBINED = 2
    ANNUAL = 3
    RATED_MONTHLY = 4
    HOT_WATER = 5


class CoolingType(Enum):
    NONE = 0
    VENTILATION = 1
    RECIRCULATION = 2
    DEHUMIDIFICATION = 3
    PANEL = 4


class PhxHotWaterPipingCalcMethod(Enum):
    SIMPLIFIED_INDIVIDUAL_PIPES = 1
    SIMPLIFIED_HOT_WATER_CALCULATOR = 2
    HOT_WATER_PIPING_UNIT_METHOD = 3
    HOT_WATER_PIPING_FLOOR_METHOD = 4


class PhxHotWaterPipingMaterial(Enum):
    COPPER_M = 1
    COPPER_L = 2
    COPPER_K = 3
    CPVC_CTS_SDR = 4
    CPVC_SCH_40 = 5
    PEX = 6
    PE = 7
    PEX_CTS_SDR = 8


class PhxHotWaterPipingInchDiameterType(Enum):
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
            fraction = "{}".format(float(parts[1]) / float(parts[2]))
        except ZeroDivisionError:
            fraction = 0.0

        # -- Return the whole
        return float(parts[0]) + float(fraction)

    @classmethod
    def nearest_key(cls, value: float) -> "PhxHotWaterPipingInchDiameterType":
        """Return a new Enum object which most closely matches the supplied value."""
        return min(PhxHotWaterPipingInchDiameterType, key=lambda d: abs(d.name_as_float - value))


class PhxHotWaterInputOptions(Enum):
    SPEC_TOTAL_LOSSES = 1
    SPEC_STANDBY_LOSSES = 2
    TOTAL_LOSSES = 3


class PhxHotWaterTankType(Enum):
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
    PH_CASE = 1
    USER_DETERMINED = 2


class PhxExhaustVentType(Enum):
    DRYER = 1
    KITCHEN_HOOD = 2
    USER_DEFINED = 3


class PhxVentDuctType(Enum):
    SUPPLY = 1
    EXHAUST = 2


class PhxSupportiveDeviceType(Enum):
    HEAT_CIRCULATING_PUMP = 4
    DHW_CIRCULATING_PUMP = 6
    DHW_STORAGE_LOAD_PUMP = 7
    OTHER = 10


class PhxSummerBypassMode(Enum):
    NONE = 1
    TEMP_CONTROLLED = 2
    ENTHALPY_CONTROLLED = 3
    ALWAYS = 4
