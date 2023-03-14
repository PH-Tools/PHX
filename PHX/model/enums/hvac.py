# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Valid 'types' for Mech Equipment Options."""

from enum import Enum
from honeybee_energy_ph.hvac.hot_water import PhSHWTankType


class FuelType(Enum):
    GAS = 1
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
    WATER_STORAGE = 8


class DeviceType(Enum):
    VENTILATION = 1
    ELECTRIC = 2
    BOILER = 3
    DISTRICT_HEAT = 4
    HEAT_PUMP = 5
    WATER_STORAGE = 8


class HeatPumpType(Enum):
    COMBINED = 2
    ANNUAL = 3
    RATED_MONTHLY = 4
    HOT_WATER = 5


class CoolingType(Enum):
    VENTILATION = 1
    RECIRCULATION = 2
    DEHUMIDIFICATION = 3
    PANEL = 4


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


class PhxExhaustVentType(Enum):
    DRYER = 1
    KITCHEN_HOOD = 2
    USER_DEFINED = 3


class PhxVentDuctType(Enum):
    SUPPLY = 1
    EXHAUST = 2