# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Site (Location and Climate) Dataclasses"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union, Optional

from PHX.model.enums.phx_site import (
    SiteSelection,
    SiteClimateSelection,
    SiteEnergyFactorSelection,
)


@dataclass
class PhxGround:
    ground_thermal_conductivity: float = 2
    ground_heat_capacity: float = 1000
    ground_density: float = 2000
    depth_groundwater: float = 3
    flow_rate_groundwater: float = 0.05


@dataclass
class PhxPEFactor:
    """Conversion Factors for Site-Energy->Primary-Energy"""

    value: float = 0.0
    unit: str = ""
    fuel_name: str = ""


@dataclass
class PhxCO2Factor:
    """Conversion Factors for Site->CO2"""

    value: float = 0.0
    unit: str = ""
    fuel_name: str = ""


PhxEnergyFactorAlias = Union[PhxPEFactor, PhxCO2Factor]


@dataclass
class PhxSiteEnergyFactors:
    selection_pe_co2_factor: SiteEnergyFactorSelection = (
        SiteEnergyFactorSelection.USER_DEFINED
    )
    pe_factors: dict[str, PhxEnergyFactorAlias] = field(default_factory=dict)
    co2_factors: dict[str, PhxEnergyFactorAlias] = field(default_factory=dict)

    def __post_init__(self):
        self.pe_factors = {
            "OIL": PhxPEFactor(1.1, "kWh/kWh", "OIL"),
            "NATURAL_GAS": PhxPEFactor(1.1, "kWh/kWh", "NATURAL_GAS"),
            "LPG": PhxPEFactor(1.1, "kWh/kWh", "LPG"),
            "HARD_COAL": PhxPEFactor(1.1, "kWh/kWh", "HARD_COAL"),
            "WOOD": PhxPEFactor(0.2, "kWh/kWh", "WOOD"),
            "ELECTRICITY_MIX": PhxPEFactor(1.8, "kWh/kWh", "ELECTRICITY_MIX"),
            "ELECTRICITY_PV": PhxPEFactor(1.7, "kWh/kWh", "ELECTRICITY_PV"),
            "HARD_COAL_CGS_70_CHP": PhxPEFactor(0.8, "kWh/kWh", "HARD_COAL_CGS_70_CHP"),
            "HARD_COAL_CGS_35_CHP": PhxPEFactor(1.1, "kWh/kWh", "HARD_COAL_CGS_35_CHP"),
            "HARD_COAL_CGS_0_CHP": PhxPEFactor(1.5, "kWh/kWh", "HARD_COAL_CGS_0_CHP"),
            "GAS_CGS_70_CHP": PhxPEFactor(0.7, "kWh/kWh", "GAS_CGS_70_CHP"),
            "GAS_CGS_35_CHP": PhxPEFactor(1.1, "kWh/kWh", "GAS_CGS_35_CHP"),
            "GAS_CGS_0_CHP": PhxPEFactor(1.5, "kWh/kWh", "GAS_CGS_0_CHP"),
            "OIL_CGS_70_CHP": PhxPEFactor(0.8, "kWh/kWh", "OIL_CGS_70_CHP"),
            "OIL_CGS_35_CHP": PhxPEFactor(1.1, "kWh/kWh", "OIL_CGS_35_CHP"),
            "OIL_CGS_0_CHP": PhxPEFactor(1.5, "kWh/kWh", "OIL_CGS_0_CHP"),
        }
        self.co2_factors: dict[str, PhxEnergyFactorAlias] = {
            "OIL": PhxCO2Factor(309.9966, "g/kWh", "OIL"),
            "NATURAL_GAS": PhxCO2Factor(250.0171, "g/kWh", "NATURAL_GAS"),
            "LPG": PhxCO2Factor(270.0102, "g/kWh", "LPG"),
            "HARD_COAL": PhxCO2Factor(439.9864, "g/kWh", "HARD_COAL"),
            "WOOD": PhxCO2Factor(53.4289, "g/kWh", "WOOD"),
            "ELECTRICITY_MIX": PhxCO2Factor(680.0068, "g/kWh", "ELECTRICITY_MIX"),
            "ELECTRICITY_PV": PhxCO2Factor(250.0171, "g/kWh", "ELECTRICITY_PV"),
            "HARD_COAL_CGS_70_CHP": PhxCO2Factor(
                239.9864, "g/kWh", "HARD_COAL_CGS_70_CHP"
            ),
            "HARD_COAL_CGS_35_CHP": PhxCO2Factor(
                319.9932, "g/kWh", "HARD_COAL_CGS_35_CHP"
            ),
            "HARD_COAL_CGS_0_CHP": PhxCO2Factor(409.9966, "g/kWh", "HARD_COAL_CGS_0_CHP"),
            "GAS_CGS_70_CHP": PhxCO2Factor(-70.0102, "g/kWh", "GAS_CGS_70_CHP"),
            "GAS_CGS_35_CHP": PhxCO2Factor(129.9898, "g/kWh", "GAS_CGS_35_CHP"),
            "GAS_CGS_0_CHP": PhxCO2Factor(319.9932, "g/kWh", "GAS_CGS_0_CHP"),
            "OIL_CGS_70_CHP": PhxCO2Factor(100, "g/kWh", "OIL_CGS_70_CHP"),
            "OIL_CGS_35_CHP": PhxCO2Factor(250.0171, "g/kWh", "OIL_CGS_35_CHP"),
            "OIL_CGS_0_CHP": PhxCO2Factor(409.9966, "g/kWh", "OIL_CGS_0_CHP"),
        }


@dataclass
class PhxLocation:
    """The physical location of the building."""

    latitude: float = 40.6
    longitude: float = -73.8
    site_elevation: Optional[float] = None
    climate_zone: int = 1
    hours_from_UTC: int = -4


@dataclass
class PhxClimatePeakLoad:
    temperature_air: float = 0
    radiation_north: float = 0
    radiation_east: float = 0
    radiation_south: float = 0
    radiation_west: float = 0
    radiation_global: float = 0


@dataclass
class PhxClimate:
    """Monthly Climate Date for the building location."""

    station_elevation: float = 3.0
    selection: SiteClimateSelection = SiteClimateSelection.USER_DEFINED
    daily_temp_swing: float = 8.0
    avg_wind_speed: float = 4.0

    temperature_air: list[float] = field(default_factory=list)
    temperature_dewpoint: list[float] = field(default_factory=list)
    temperature_sky: list[float] = field(default_factory=list)

    radiation_north: list[float] = field(default_factory=list)
    radiation_east: list[float] = field(default_factory=list)
    radiation_south: list[float] = field(default_factory=list)
    radiation_west: list[float] = field(default_factory=list)
    radiation_global: list[float] = field(default_factory=list)

    peak_heating_1: PhxClimatePeakLoad = field(default_factory=PhxClimatePeakLoad)
    peak_heating_2: PhxClimatePeakLoad = field(default_factory=PhxClimatePeakLoad)
    peak_cooling_1: PhxClimatePeakLoad = field(default_factory=PhxClimatePeakLoad)
    peak_cooling_2: PhxClimatePeakLoad = field(default_factory=PhxClimatePeakLoad)


@dataclass
class PhxPHPPCodes:
    country_code: str = "US-United States of America"
    region_code: str = "New York"
    dataset_name = "US0055b-New York"


@dataclass
class PhxSite:
    """The climate and location date for the building's site."""

    display_name: str = "New York"

    source: str = "__unknown__"
    selection: SiteSelection = SiteSelection.USER_DEFINED

    location: PhxLocation = field(default_factory=PhxLocation)
    climate: PhxClimate = field(default_factory=PhxClimate)
    phpp_codes: PhxPHPPCodes = field(default_factory=PhxPHPPCodes)
    ground: PhxGround = field(default_factory=PhxGround)

    energy_factors: PhxSiteEnergyFactors = field(default_factory=PhxSiteEnergyFactors)
