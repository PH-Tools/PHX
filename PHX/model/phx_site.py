# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Site (Location and Climate) Dataclasses"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generator, List, Optional, Tuple, Union

from PHX.model.enums.phx_site import SiteClimateSelection, SiteEnergyFactorSelection, SiteSelection


@dataclass
class PhxGround:
    ground_thermal_conductivity: float = 2.0
    ground_heat_capacity: float = 1000.0
    ground_density: float = 2000.0
    depth_groundwater: float = 3.0
    flow_rate_groundwater: float = 0.05

    def __eq__(self, other: PhxGround) -> bool:
        TOLERANCE = 0.0001
        return (
            abs(self.ground_thermal_conductivity - other.ground_thermal_conductivity) < TOLERANCE
            and abs(self.ground_heat_capacity - other.ground_heat_capacity) < TOLERANCE
            and abs(self.ground_density - other.ground_density) < TOLERANCE
            and abs(self.depth_groundwater - other.depth_groundwater) < TOLERANCE
            and abs(self.flow_rate_groundwater - other.flow_rate_groundwater) < TOLERANCE
        )


@dataclass
class PhxPEFactor:
    """Conversion Factors for Site-Energy->Primary-Energy"""

    value: float = 0.0
    unit: str = ""
    fuel_name: str = ""

    def __eq__(self, other: PhxPEFactor) -> bool:
        TOLERANCE = 0.0001
        return (
            abs(self.value - other.value) < TOLERANCE and self.unit == other.unit and self.fuel_name == other.fuel_name
        )


@dataclass
class PhxCO2Factor:
    """Conversion Factors for Site->CO2"""

    value: float = 0.0
    unit: str = ""
    fuel_name: str = ""

    def __eq__(self, other: PhxCO2Factor) -> bool:
        TOLERANCE = 0.0001
        return (
            abs(self.value - other.value) < TOLERANCE and self.unit == other.unit and self.fuel_name == other.fuel_name
        )


PhxEnergyFactorAlias = Union[PhxPEFactor, PhxCO2Factor]


@dataclass
class PhxSiteEnergyFactors:
    selection_pe_co2_factor: SiteEnergyFactorSelection = SiteEnergyFactorSelection.USER_DEFINED
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
            "ELECTRICITY_PV": PhxPEFactor(0.7, "kWh/kWh", "ELECTRICITY_PV"),
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
            "HARD_COAL_CGS_70_CHP": PhxCO2Factor(239.9864, "g/kWh", "HARD_COAL_CGS_70_CHP"),
            "HARD_COAL_CGS_35_CHP": PhxCO2Factor(319.9932, "g/kWh", "HARD_COAL_CGS_35_CHP"),
            "HARD_COAL_CGS_0_CHP": PhxCO2Factor(409.9966, "g/kWh", "HARD_COAL_CGS_0_CHP"),
            "GAS_CGS_70_CHP": PhxCO2Factor(-70.0102, "g/kWh", "GAS_CGS_70_CHP"),
            "GAS_CGS_35_CHP": PhxCO2Factor(129.9898, "g/kWh", "GAS_CGS_35_CHP"),
            "GAS_CGS_0_CHP": PhxCO2Factor(319.9932, "g/kWh", "GAS_CGS_0_CHP"),
            "OIL_CGS_70_CHP": PhxCO2Factor(100, "g/kWh", "OIL_CGS_70_CHP"),
            "OIL_CGS_35_CHP": PhxCO2Factor(250.0171, "g/kWh", "OIL_CGS_35_CHP"),
            "OIL_CGS_0_CHP": PhxCO2Factor(409.9966, "g/kWh", "OIL_CGS_0_CHP"),
        }

    def __eq__(self, other: PhxSiteEnergyFactors) -> bool:
        return (
            self.selection_pe_co2_factor == other.selection_pe_co2_factor
            and self.pe_factors == other.pe_factors
            and self.co2_factors == other.co2_factors
        )


@dataclass
class PhxLocation:
    """The physical location of the building."""

    latitude: float = 40.6
    longitude: float = -73.8
    site_elevation: Optional[float] = None
    climate_zone: int = 1
    hours_from_UTC: int = -4

    def __eq__(self, other: PhxLocation) -> bool:
        TOLERANCE = 0.001
        return (
            abs(self.latitude - other.latitude) < TOLERANCE
            and abs(self.longitude - other.longitude) < TOLERANCE
            and abs((self.site_elevation or 0.0) - (other.site_elevation or 0.0)) < TOLERANCE
            and self.climate_zone == other.climate_zone
            and self.hours_from_UTC == other.hours_from_UTC
        )


@dataclass
class PhxClimatePeakLoad:
    temperature_air: Optional[float] = 0.0
    radiation_north: Optional[float] = 0.0
    radiation_east: Optional[float] = 0.0
    radiation_south: Optional[float] = 0.0
    radiation_west: Optional[float] = 0.0
    radiation_global: Optional[float] = 0.0

    def __eq__(self, other: PhxClimatePeakLoad) -> bool:
        TOLERANCE = 0.001
        if self.temperature_air and other.temperature_air:
            if abs(self.temperature_air - other.temperature_air) > TOLERANCE:
                return False
        if self.radiation_north and other.radiation_north:
            if abs(self.radiation_north - other.radiation_north) > TOLERANCE:
                return False
        if self.radiation_east and other.radiation_east:
            if abs(self.radiation_east - other.radiation_east) > TOLERANCE:
                return False
        if self.radiation_south and other.radiation_south:
            if abs(self.radiation_south - other.radiation_south) > TOLERANCE:
                return False
        if self.radiation_west and other.radiation_west:
            if abs(self.radiation_west - other.radiation_west) > TOLERANCE:
                return False
        if self.radiation_global and other.radiation_global:
            if abs(self.radiation_global - other.radiation_global) > TOLERANCE:
                return False
        return True


@dataclass
class PhxClimateIterOutput:
    """Wrapper class for organizing output of the 'PhxClimate.monthly_values' property."""

    month_name: str
    month_hours: float
    temperature_air: float
    temperature_dewpoint: float
    temperature_sky: float
    radiation_north: float
    radiation_east: float
    radiation_south: float
    radiation_west: float
    radiation_global: float


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

    @staticmethod
    def _list_eq(list_a: List[float], list_b: List[float]) -> bool:
        TOLERANCE = 0.001
        for a, b in zip(list_a, list_b):
            if abs(a - b) > TOLERANCE:
                return False
        return True

    def __eq__(self, other) -> bool:
        TOLERANCE = 0.01
        return (
            abs(self.station_elevation - other.station_elevation) < TOLERANCE
            and self.selection == other.selection
            and abs(self.daily_temp_swing - other.daily_temp_swing) < TOLERANCE
            and abs(self.avg_wind_speed - other.avg_wind_speed) < TOLERANCE
            and self._list_eq(self.temperature_air, other.temperature_air)
            and self._list_eq(self.temperature_dewpoint, other.temperature_dewpoint)
            and self._list_eq(self.temperature_sky, other.temperature_sky)
            and self._list_eq(self.radiation_north, other.radiation_north)
            and self._list_eq(self.radiation_east, other.radiation_east)
            and self._list_eq(self.radiation_south, other.radiation_south)
            and self._list_eq(self.radiation_west, other.radiation_west)
            and self._list_eq(self.radiation_global, other.radiation_global)
            and self.peak_heating_1 == other.peak_heating_1
            and self.peak_heating_2 == other.peak_heating_2
            and self.peak_cooling_1 == other.peak_cooling_1
            and self.peak_cooling_2 == other.peak_cooling_2
        )

    @property
    def max_temperature_air(self) -> float:
        """The maximum air temperature in the dataset."""
        return max(self.temperature_air)

    @property
    def min_temperature_air(self) -> float:
        """The minimum air temperature in the dataset."""
        return min(self.temperature_air)

    @property
    def max_air_temperature_amplitude(self) -> float:
        """The absolute difference between the maximum and minimum air temperature."""
        return self.max_temperature_air - self.min_temperature_air

    @property
    def average_temperature_amplitude(self) -> float:
        """The Average between the maximum and minimum air temperature.
        This value is primarily used to calculate the ground heat loss in PHPP.
        """
        return (self.max_air_temperature_amplitude) / 2

    @property
    def monthly_hours(self) -> List[Tuple[str, int]]:
        """The a ordered (Jan-Dec) list of tuples containing the month-name and the number of hours in that month."""
        return [
            ("JAN", 744),
            ("FEB", 672),
            ("MAR", 744),
            ("APR", 720),
            ("MAY", 744),
            ("JUN", 720),
            ("JUL", 744),
            ("AUG", 744),
            ("SEP", 720),
            ("OCT", 744),
            ("NOV", 720),
            ("DEC", 744),
        ]

    @property
    def monthly_values(self) -> Generator[PhxClimateIterOutput, Any, Any]:
        """A generator that yields the monthly values one at a time for the climate data."""
        for i in range(len(self.monthly_hours)):
            try:
                yield PhxClimateIterOutput(
                    self.monthly_hours[i][0],
                    self.monthly_hours[i][1],
                    self.temperature_air[i],
                    self.temperature_dewpoint[i],
                    self.temperature_sky[i],
                    self.radiation_north[i],
                    self.radiation_east[i],
                    self.radiation_south[i],
                    self.radiation_west[i],
                    self.radiation_global[i],
                )
            except IndexError:
                msg = "Error: Climate data lengths do not match?"
                raise IndexError(msg)


@dataclass
class PhxPHPPCodes:
    country_code: str = "US-United States of America"
    region_code: str = "New York"
    dataset_name = "US0055b-New York"

    def __eq__(self, other) -> bool:
        return (
            self.country_code == other.country_code
            and self.region_code == other.region_code
            and self.dataset_name == other.dataset_name
        )


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

    def __eq__(self, other) -> bool:
        return (
            self.display_name == other.display_name
            and self.source == other.source
            and self.selection == other.selection
            and self.location == other.location
            and self.climate == other.climate
            and self.phpp_codes == other.phpp_codes
            and self.ground == other.ground
            and self.energy_factors == other.energy_factors
        )
