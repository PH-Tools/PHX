# -*- Python Version: 3.10 -*-

"""PHX Site (Location and Climate) Dataclasses"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any, Union

from PHX.model.enums.phx_site import SiteClimateSelection, SiteEnergyFactorSelection, SiteSelection


@dataclass
class PhxGround:
    """Soil and groundwater thermal properties for ground heat loss calculations.

    Attributes:
        ground_thermal_conductivity (float): Soil thermal conductivity in W/(mK). Default: 2.0.
        ground_heat_capacity (float): Soil volumetric heat capacity in J/(kgK). Default: 1000.0.
        ground_density (float): Soil density in kg/m3. Default: 2000.0.
        depth_groundwater (float): Depth to groundwater table in m. Default: 3.0.
        flow_rate_groundwater (float): Groundwater flow rate in m/day. Default: 0.05.
    """

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
    """Primary energy (PE) conversion factor for a single fuel type.

    Converts site energy to primary energy for PH certification calculations.

    Attributes:
        value (float): PE conversion factor. Default: 0.0.
        unit (str): Unit label (e.g. "kWh/kWh"). Default: "".
        fuel_name (str): Fuel type identifier (e.g. "ELECTRICITY_MIX"). Default: "".
    """

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
    """CO2 emission factor for a single fuel type.

    Converts site energy consumption to CO2 emissions for PH certification calculations.

    Attributes:
        value (float): CO2 emission factor. Default: 0.0.
        unit (str): Unit label (e.g. "g/kWh"). Default: "".
        fuel_name (str): Fuel type identifier (e.g. "NATURAL_GAS"). Default: "".
    """

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
    """Collection of primary energy (PE) and CO2 conversion factors for the site.

    Initialized with PHI default PE and CO2 factors for standard fuel types.
    The selection field controls whether standard or user-defined factors are used.

    Attributes:
        selection_pe_co2_factor (SiteEnergyFactorSelection): Factor dataset source selection.
            Default: USER_DEFINED.
        pe_factors (dict[str, PhxEnergyFactorAlias]): PE factors keyed by fuel name.
            Default: PHI standard values (populated in __post_init__).
        co2_factors (dict[str, PhxEnergyFactorAlias]): CO2 factors keyed by fuel name.
            Default: PHI standard values (populated in __post_init__).
    """

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
    """Geographic coordinates and site metadata for the building location.

    Attributes:
        latitude (float): Site latitude in decimal degrees. Default: 40.6.
        longitude (float): Site longitude in decimal degrees. Default: -73.8.
        site_elevation (float | None): Site elevation above sea level in m. Default: None.
        climate_zone (int): ASHRAE climate zone number. Default: 1.
        hours_from_UTC (int): UTC offset in hours. Default: -4.
    """

    latitude: float = 40.6
    longitude: float = -73.8
    site_elevation: float | None = None
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
    """Climate conditions at a single peak-load design point (heating or cooling).

    Stores the outdoor air temperature, directional solar radiation, and optional
    dewpoint/sky/ground temperatures used for peak heating or cooling load calculations.

    Attributes:
        temperature_air (float | None): Outdoor air temperature in deg. C. Default: 0.0.
        radiation_north (float | None): North-facing solar radiation in W/m2. Default: 0.0.
        radiation_east (float | None): East-facing solar radiation in W/m2. Default: 0.0.
        radiation_south (float | None): South-facing solar radiation in W/m2. Default: 0.0.
        radiation_west (float | None): West-facing solar radiation in W/m2. Default: 0.0.
        radiation_global (float | None): Global horizontal solar radiation in W/m2. Default: 0.0.
        temperature_dewpoint (float | None): Outdoor dewpoint temperature in deg. C. Default: None.
        temperature_sky (float | None): Effective sky temperature in deg. C. Default: None.
        temperature_ground (float | None): Ground surface temperature in deg. C. Default: None.
    """

    temperature_air: float | None = 0.0
    radiation_north: float | None = 0.0
    radiation_east: float | None = 0.0
    radiation_south: float | None = 0.0
    radiation_west: float | None = 0.0
    radiation_global: float | None = 0.0
    temperature_dewpoint: float | None = None
    temperature_sky: float | None = None
    temperature_ground: float | None = None

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
        if self.temperature_dewpoint and other.temperature_dewpoint:
            if abs(self.temperature_dewpoint - self.temperature_dewpoint) > TOLERANCE:
                return False
        if self.temperature_sky and other.temperature_sky:
            if abs(self.temperature_sky - self.temperature_sky) > TOLERANCE:
                return False
        if self.temperature_ground and other.temperature_ground:
            if abs(self.temperature_ground - self.temperature_ground) > TOLERANCE:
                return False
        return True


@dataclass
class PhxClimateIterOutput:
    """Single month of climate data yielded by PhxClimate.monthly_values.

    Attributes:
        month_name (str): Three-letter month abbreviation (e.g. "JAN").
        month_hours (float): Number of hours in the month.
        temperature_air (float): Monthly average outdoor air temperature in deg. C.
        temperature_dewpoint (float): Monthly average dewpoint temperature in deg. C.
        temperature_sky (float): Monthly average effective sky temperature in deg. C.
        radiation_north (float): Monthly north-facing solar radiation in kWh/m2.
        radiation_east (float): Monthly east-facing solar radiation in kWh/m2.
        radiation_south (float): Monthly south-facing solar radiation in kWh/m2.
        radiation_west (float): Monthly west-facing solar radiation in kWh/m2.
        radiation_global (float): Monthly global horizontal solar radiation in kWh/m2.
    """

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
    """Monthly climate dataset for the building location.

    Stores 12-month arrays of temperature and solar radiation data, plus
    peak heating/cooling design-day conditions used in the PH energy balance.

    Attributes:
        station_elevation (float): Weather station elevation above sea level in m. Default: 3.0.
        selection (SiteClimateSelection): Climate data source selection. Default: USER_DEFINED.
        daily_temp_swing (float): Average daily temperature swing in K. Default: 8.0.
        avg_wind_speed (float): Average annual wind speed in m/s. Default: 4.0.
        temperature_air (list[float]): Monthly average outdoor air temperatures in deg. C. Default: [].
        temperature_dewpoint (list[float]): Monthly average dewpoint temperatures in deg. C. Default: [].
        temperature_sky (list[float]): Monthly average effective sky temperatures in deg. C. Default: [].
        radiation_north (list[float]): Monthly north-facing solar radiation in kWh/m2. Default: [].
        radiation_east (list[float]): Monthly east-facing solar radiation in kWh/m2. Default: [].
        radiation_south (list[float]): Monthly south-facing solar radiation in kWh/m2. Default: [].
        radiation_west (list[float]): Monthly west-facing solar radiation in kWh/m2. Default: [].
        radiation_global (list[float]): Monthly global horizontal solar radiation in kWh/m2. Default: [].
        peak_heating_1 (PhxClimatePeakLoad): First peak heating design-day conditions.
            Default: PhxClimatePeakLoad().
        peak_heating_2 (PhxClimatePeakLoad): Second peak heating design-day conditions.
            Default: PhxClimatePeakLoad().
        peak_cooling_1 (PhxClimatePeakLoad): First peak cooling design-day conditions.
            Default: PhxClimatePeakLoad().
        peak_cooling_2 (PhxClimatePeakLoad): Second peak cooling design-day conditions.
            Default: PhxClimatePeakLoad().
    """

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
    def _list_eq(list_a: list[float], list_b: list[float]) -> bool:
        TOLERANCE = 0.001
        return all(abs(a - b) <= TOLERANCE for a, b in zip(list_a, list_b, strict=False))

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
    def monthly_hours(self) -> list[tuple[str, int]]:
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
    """PHPP climate dataset selection codes for country, region, and dataset.

    These codes map to the PHPP climate database entries and are used when
    writing climate data to the PHPP Excel file.

    Attributes:
        country_code (str): PHPP country identifier string. Default: "US-United States of America".
        region_code (str): PHPP region/state name. Default: "New York".
        dataset_name (str): PHPP climate dataset name. Default: "US0055b-New York".
    """

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
    """Top-level container for a building's site location, climate, and energy factors.

    Groups geographic coordinates, monthly climate data, PHPP dataset codes,
    ground thermal properties, and PE/CO2 conversion factors.

    Attributes:
        display_name (str): Human-readable site/city name. Default: "New York".
        source (str): Provenance label for the climate data source. Default: "__unknown__".
        selection (SiteSelection): Site data source selection mode. Default: USER_DEFINED.
        location (PhxLocation): Geographic coordinates and elevation. Default: PhxLocation().
        climate (PhxClimate): Monthly climate dataset and peak-load conditions.
            Default: PhxClimate().
        phpp_codes (PhxPHPPCodes): PHPP climate database selection codes.
            Default: PhxPHPPCodes().
        ground (PhxGround): Soil and groundwater thermal properties. Default: PhxGround().
        energy_factors (PhxSiteEnergyFactors): PE and CO2 conversion factor sets.
            Default: PhxSiteEnergyFactors().
    """

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
