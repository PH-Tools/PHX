# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP PER Worksheet."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Collection, Dict, List, Optional, Sequence, Tuple, Union

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model as shp
from PHX.PHPP.sheet_io.io_exceptions import FindSectionMarkerException, PerReferenceAreaException
from PHX.xl.xl_app import XLConnection

# -----------------------------------------------------------------------------


class BaseBlock:
    """Base class for all PER Data Blocks (Heating, Cooling, etc..)"""

    def __init__(
        self,
        _host: PER,
        _xl: XLConnection,
        _shape: shp.PerDataBlock,
    ):
        self.host = _host
        self.xl = _xl
        self.shape = _shape
        self._phpp_data: Optional[Dict[str, List[Union[str, Unit]]]] = None
        self._block_header_row: Optional[int] = None
        self._block_start_row: Optional[int] = None
        self._block_end_row: Optional[int] = None
        self._reference_area_address: Optional[str] = None
        self._reference_area: Optional[float] = None

    @property
    def block_start_row(self) -> int:
        """Return the row number for the first row of the data block."""
        if not self._block_start_row:
            self._block_start_row = self.find_block_start_row()
        return self._block_start_row

    @property
    def block_end_row(self) -> int:
        """Return the row number for the last row of the data block."""
        if not self._block_end_row:
            self._block_end_row = self.find_block_end_row()
        return self._block_end_row

    @property
    def phpp_data(self) -> Dict[str, List[Union[str, Unit]]]:
        """Return all the Block PHPP Data as a Dict of Lists of values.

        -> {
            'P': ['Electricity (HP compact unit)', 'Electricity (heat pump)', ...],
            'T': [0.0 (KBTU/FT2), 0.8733713455642654 (KBTU/FT2), ...],
            'X': [0.0 (KBTU/FT2), 2.27076549846709 (KBTU/FT2), ...],
            }
        """
        if not self._phpp_data:
            self._phpp_data = self.get_data()
        return self._phpp_data

    @property
    def reference_area_address(self) -> str:
        """Return the range address for the Data type's Reference Area (TFA/ Footprint)."""
        if not self._reference_area_address:
            self._reference_area_address = self.host.shape.addresses.tfa  # Default
        return self._reference_area_address

    @property
    def reference_area(self) -> float:
        """Return the Data type's Reference Area (TFA/ Footprint)."""
        if not self._reference_area:
            try:
                self._reference_area = float(
                    self.xl.get_single_data_item(self.worksheet_name, self.reference_area_address)  # type: ignore
                )
            except:
                raise PerReferenceAreaException(self.worksheet_name, self.reference_area_address)

        return self._reference_area

    @property
    def block_header_row(self) -> int:
        """Return the Row number where the block 'Heading' is found."""
        if not self._block_header_row:
            self._block_header_row = self.find_block_header_row()
        return self._block_header_row

    @property
    def worksheet_name(self) -> str:
        """Return the Name of the PER worksheet."""
        return self.host.shape.name

    @property
    def locator_column(self) -> str:
        """Return the column letter for the 'locator' column."""
        return self.host.shape.locator_col

    @property
    def column_final_energy(self) -> str:
        """Return the column letter for the 'Final' (Site) Energy Demand."""
        return self.host.shape.columns.final_energy

    @property
    def column_pe_energy(self) -> str:
        """Return the column letter for the 'Primary' (Source) Energy Demand."""
        return self.host.shape.columns.pe_energy

    @property
    def column_co2_emissions(self) -> str:
        """Return the column letter for the 'CO2 Emissions'."""
        return self.host.shape.columns.co2_emissions

    def find_block_header_row(self) -> int:
        """Locate the row number for the block heading"""
        data = self.xl.get_single_column_data(
            self.worksheet_name,
            self.locator_column,
            self.host.heading_row,
            self.host.heading_row + 100,
        )
        search_string = self.shape.locator_string_heading
        row_number = self.xl.find_row(search_string, data, self.host.heading_row)
        if not row_number:
            raise FindSectionMarkerException(search_string, self.worksheet_name, self.locator_column)
        return row_number

    def find_block_start_row(self) -> int:
        """Locate the row number for the first row of the data block."""
        data = self.xl.get_single_column_data(
            self.worksheet_name,
            self.locator_column,
            self.block_header_row,
            self.block_header_row + 10,
        )

        search_string = self.shape.locator_string_start
        row_number = self.xl.find_row(search_string, data, self.block_header_row)
        if not row_number:
            raise FindSectionMarkerException(search_string, self.worksheet_name, self.locator_column)
        return row_number

    def find_block_end_row(self) -> int:
        """Locate the row number for the last row of the data block."""
        data = self.xl.get_single_column_data(
            self.worksheet_name,
            self.locator_column,
            self.block_start_row,
            self.block_start_row + 25,
        )

        search_string = self.shape.locator_string_end
        row_number = self.xl.find_row(search_string, data, self.block_start_row)
        if not row_number:
            raise FindSectionMarkerException(search_string, self.worksheet_name, self.locator_column)
        return row_number

    def get_data(self) -> Dict[str, List[Union[str, Unit]]]:
        """Return all the Block's data from Excel"""
        start = f"{self.locator_column}{self.block_start_row}"
        end = f"{self.column_co2_emissions}{self.block_end_row}"
        address = f"{start}:{end}"
        xl_raw_data = self.xl.get_data_with_column_letters(self.worksheet_name, address)
        """
        xl_raw_data = {
            'P': ['Electricity (HP compact unit)', 'Electricity (heat pump)', ...], 
            'Q': [12.3, 1.9, 45.6, ...],
            ...
            'Z': [0.0, 0.0, 0.0, ...],
        }
        """

        # ----------------------------------------------------------------------
        # -- convert the raw numeric values to Units
        unit_dict: Dict[str, List[Union[str, Unit]]] = {}

        # -- Grab the index column data first
        unit_dict[self.locator_column] = [str(_) for _ in xl_raw_data[self.locator_column]]

        # -- Get the numeric values as units
        unit_dict[self.host.shape.columns.final_energy] = [
            Unit(_, self.host.shape.unit) for _ in xl_raw_data[self.host.shape.columns.final_energy]
        ]
        unit_dict[self.host.shape.columns.pe_energy] = [
            Unit(_, self.host.shape.unit) for _ in xl_raw_data[self.host.shape.columns.pe_energy]
        ]

        return unit_dict

    def get_final_energy_by_fuel_type(self) -> Dict[str, Unit]:
        """Return the Block's Final (Site) Energy as a dict of Unit values.

        -> {
            'Electricity (HP compact unit)': 0.0 (KBTU/FT2),
            'Electricity (heat pump)': 0.8733713455642654 (KBTU/FT2),
            ...
            }
        """
        use_types: List[str] = self.phpp_data[self.locator_column]  # type: ignore
        site_energy: List[Unit] = self.phpp_data[self.column_final_energy]  # type: ignore
        return {str(use_type): value for use_type, value in zip(use_types, site_energy)}

    def get_primary_energy_by_fuel_type(self) -> Dict[str, Unit]:
        """Return the Block's Primary (Source)) Energy as a dict of values.

        -> {
            'Electricity (HP compact unit)': 0.0 (KBTU/FT2),
            'Electricity (heat pump)': 0.8733713455642654 (KBTU/FT2),
            ...
            }
        """
        use_types: List[str] = self.phpp_data[self.locator_column]  # type: ignore
        source_energy: List[Unit] = self.phpp_data[self.column_pe_energy]  # type: ignore
        return {str(t): e for t, e in zip(use_types, source_energy)}


# -----------------------------------------------------------------------------


class Heating(BaseBlock):
    """Heating Data Block."""

    def __init__(self, _host: PER, _xl: XLConnection, _shape: shp.PerDataBlock):
        super().__init__(_host, _xl, _shape)
        self._reference_area_address = self.host.shape.addresses.tfa


class Cooling(BaseBlock):
    """Cooling Energy"""

    def __init__(self, _host: PER, _xl: XLConnection, _shape: shp.PerDataBlock):
        super().__init__(_host, _xl, _shape)
        self._reference_area_address = self.host.shape.addresses.tfa


class DHW(BaseBlock):
    """Hot-Water Energy"""

    def __init__(self, _host: PER, _xl: XLConnection, _shape: shp.PerDataBlock):
        super().__init__(_host, _xl, _shape)
        self._reference_area_address = self.host.shape.addresses.tfa


class HouseholdElectric(BaseBlock):
    """Household Electric (Lighting, Appliances, etc)"""

    def __init__(self, _host: PER, _xl: XLConnection, _shape: shp.PerDataBlock):
        super().__init__(_host, _xl, _shape)
        self._reference_area_address = self.host.shape.addresses.tfa


class AdditionalGas(BaseBlock):
    """Gas for cooking, dryers"""

    def __init__(self, _host: PER, _xl: XLConnection, _shape: shp.PerDataBlock):
        super().__init__(_host, _xl, _shape)
        self._reference_area_address = self.host.shape.addresses.tfa


class EnergyGeneration(BaseBlock):
    """Solar, Wind Energy Generation"""

    def __init__(self, _host: PER, _xl: XLConnection, _shape: shp.PerDataBlock):
        super().__init__(_host, _xl, _shape)
        self._reference_area_address = self.host.shape.addresses.footprint


# -----------------------------------------------------------------------------


@dataclass
class HeatingDeviceUsage:
    """Convenience class for organizing and cleaning the data."""

    device_type_name: str = "-"
    device_heating_percentage: Unit = field(default_factory=Unit)
    device_dhw_percentage: Unit = field(default_factory=Unit)

    @classmethod
    def from_phpp_data_row(cls, row: Sequence) -> HeatingDeviceUsage:
        """Create a new instance from a row of data from PHPP."""
        obj = cls()

        if not row:
            return obj

        if row[0] not in ["-", "", "None", None]:
            obj.device_type_name = str(row[0])

        if row[3] not in ["-", "", "None", None]:
            obj.device_heating_percentage = Unit(row[3], "-")

        if row[4] not in ["-", "", "None", None]:
            obj.device_dhw_percentage = Unit(row[4], "-")

        return obj


class PER:
    """IO Controller for the PHPP 'PER' worksheet."""

    def __init__(self, _xl: XLConnection, _shape: shp.Per):
        self.xl = _xl
        self.shape = _shape
        self.heating = Heating(self, _xl, _shape.heating)
        self.cooling = Cooling(self, _xl, _shape.cooling)
        self.dhw = DHW(self, _xl, _shape.dhw)
        self.household_electric = HouseholdElectric(self, _xl, _shape.household_electric)
        self.additional_gas = AdditionalGas(self, _xl, _shape.additional_gas)
        self.energy_generation = EnergyGeneration(self, _xl, _shape.energy_generation)
        self._heating_device_data = None  # local cache

    @property
    def heading_row(self) -> int:
        return 15

    @property
    def heating_device_data(self) -> Tuple[HeatingDeviceUsage]:
        """Return a list of HeatingDeviceUsage objects."""
        if not self._heating_device_data:
            self._heating_device_data = self.get_heating_device_type_data()
        return self._heating_device_data

    def get_final_kWh_m2_by_use_type(
        self,
    ) -> Dict[str, Dict[str, Unit]]:
        """Return a Dict of all the Site (Final) Energy [kWh/m2] by use-type."""
        return {
            "heating": self.heating.get_final_energy_by_fuel_type(),
            "cooling": self.cooling.get_final_energy_by_fuel_type(),
            "dhw": self.dhw.get_final_energy_by_fuel_type(),
            "household_electric": self.household_electric.get_final_energy_by_fuel_type(),
            "additional_gas": self.additional_gas.get_final_energy_by_fuel_type(),
            "energy_generation": self.energy_generation.get_final_energy_by_fuel_type(),
        }

    def get_final_kWh_by_fuel_type(self) -> Dict[str, Dict[str, Unit]]:
        """Return a Dict of all the Site (Final) Energy [kWh | kBtu] by use and fuel-type.

        -> {
            'heating': {
                'Electricity (HP compact unit)': 0.0 (KBTU/FT2),
                ...
            'cooling': {
                'Electricity cooling (HP)': 1.1129088978478676 (KBTU/FT2),
                ...
                },
            'dhw': {
                'Electricity (HP compact unit)': 0.0 (KBTU/FT2),
                ...
                },
            'household_electric': {
                'User electricity (lighting, electrical devices, etc.)': 2.5064700097780253 (KBTU/FT2),
                ...
                },
            'energy_generation':{
                'PV electricity': 19.687188186419185 (KBTU/FT2),
                ...
                }
        }
        """
        kwh_m2_data = self.get_final_kWh_m2_by_use_type()
        d: Dict[str, Dict[str, Unit]] = {}
        for use_type_name, use_type_values_by_fuel in kwh_m2_data.items():
            d[use_type_name] = {}
            energy_type = getattr(self, use_type_name)
            area_m2: float = energy_type.reference_area  # TFA or Footprint
            for fuel_type_name, fuel_type_values in use_type_values_by_fuel.items():
                try:
                    d[use_type_name][fuel_type_name] = fuel_type_values * area_m2
                except:
                    d[use_type_name][fuel_type_name] = fuel_type_values
        return d

    def get_primary_kWh_m2_by_use_type(self) -> Dict[str, Dict[str, Unit]]:
        """Return a Dict of all the Source (Primary) Energy [kWh/m2] by use-type."""
        self.xl.get_sheet_by_name(self.shape.name).activate()
        return {
            "heating": self.heating.get_primary_energy_by_fuel_type(),
            "cooling": self.cooling.get_primary_energy_by_fuel_type(),
            "dhw": self.dhw.get_primary_energy_by_fuel_type(),
            "household_electric": self.household_electric.get_primary_energy_by_fuel_type(),
            "additional_gas": self.additional_gas.get_primary_energy_by_fuel_type(),
            "energy_generation": self.energy_generation.get_primary_energy_by_fuel_type(),
        }

    def get_primary_kWh_by_fuel_type(self) -> Dict[str, Dict[str, Unit]]:
        """Return a Dict of all the Primary (Source) Energy [kWh | kBtu] by use and fuel type

        -> {
            'heating': {
                'Electricity (HP compact unit)': 0.0 (KBTU/FT2),
                ...
            'cooling': {
                'Electricity cooling (HP)': 1.1129088978478676 (KBTU/FT2),
                ...
                },
            'dhw': {
                'Electricity (HP compact unit)': 0.0 (KBTU/FT2),
                ...
                },
            'household_electric': {
                'User electricity (lighting, electrical devices, etc.)': 2.5064700097780253 (KBTU/FT2),
                ...
                },
            'energy_generation':{
                'PV electricity': 19.687188186419185 (KBTU/FT2),
                ...
                }
        }
        """
        kwh_m2_data = self.get_primary_kWh_m2_by_use_type()
        d: Dict[str, Dict[str, Unit]] = {}
        for use_type_name, use_type_values_by_fuel in kwh_m2_data.items():
            d[use_type_name] = {}
            energy_type = getattr(self, use_type_name)
            area_m2: float = energy_type.reference_area  # TFA or Footprint
            for fuel_type_name, fuel_type_values in use_type_values_by_fuel.items():
                try:
                    d[use_type_name][fuel_type_name] = fuel_type_values * area_m2
                except:
                    d[use_type_name][fuel_type_name] = fuel_type_values
        return d

    def get_heating_device_type_data(self) -> Tuple[HeatingDeviceUsage]:
        """Return a Tuple of HeatingDeviceUsage objects from the PER worksheet."""
        data = self.xl.get_data(
            self.shape.name,
            f"{self.shape.heating_types.range_start}:{self.shape.heating_types.range_end}",
        )

        if not isinstance(data, Collection):
            raise ValueError(
                "There was a problem getting the heating-generation "
                f"type data from PHPP worksheet {self.shape.name}?"
            )

        return tuple(HeatingDeviceUsage.from_phpp_data_row(row) for row in data)
