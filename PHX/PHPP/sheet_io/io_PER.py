# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP PER Worksheet."""

from __future__ import annotations
from typing import Optional, List, Dict, Any

from PHX.xl import xl_data
from PHX.xl.xl_app import XLConnection
from PHX.PHPP.phpp_localization import shape_model as shp
from PHX.PHPP.sheet_io.io_exceptions import (
    FindSectionMarkerException,
    PerReferenceAreaException,
)


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
        self._phpp_data: Optional[Dict[str, List[xl_data.xl_range_single_value]]] = None
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
    def phpp_data(self) -> Dict[str, List[xl_data.xl_range_single_value]]:
        """Return all the Block PHPP Data as a Dict of Lists of values."""
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
                    self.xl.get_single_data_item(
                        self.worksheet_name, self.reference_area_address
                    )  # type: ignore
                )
            except:
                raise PerReferenceAreaException(
                    self.worksheet_name, self.reference_area_address
                )

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
            raise FindSectionMarkerException(
                search_string, self.worksheet_name, self.locator_column
            )
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
            raise FindSectionMarkerException(
                search_string, self.worksheet_name, self.locator_column
            )
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
            raise FindSectionMarkerException(
                search_string, self.worksheet_name, self.locator_column
            )
        return row_number

    def get_data(self) -> Dict[str, List[xl_data.xl_range_single_value]]:
        """Return all the Block's data from Excel"""
        address = f"{self.locator_column}{self.block_start_row}:{self.column_co2_emissions}{self.block_end_row}"
        return self.xl.get_data_with_column_letters(self.worksheet_name, address)

    def get_final_energy_by_fuel_type(self) -> Dict[str, xl_data.xl_range_single_value]:
        """Return the Block's Final (Site) Energy as a dict of values."""
        use_types = self.phpp_data[self.locator_column]
        site_energy = self.phpp_data[self.column_final_energy]
        return {str(t): e for t, e in zip(use_types, site_energy)}

    def get_primary_energy_by_fuel_type(self) -> Dict[str, xl_data.xl_range_single_value]:
        """Return the Block's Primary (Source)) Energy as a dict of values."""
        use_types = self.phpp_data[self.locator_column]
        source_energy = self.phpp_data[self.column_pe_energy]
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

    @property
    def heading_row(self) -> int:
        return 15

    def get_final_kWh_m2_by_fuel_type(
        self,
    ) -> Dict[str, Dict[str, xl_data.xl_range_single_value]]:
        """Return a Dict of all the Site (Final) Energy [kWh/m2] by use-type."""
        self.xl.get_sheet_by_name(self.shape.name).activate()

        return {
            "heating": self.heating.get_final_energy_by_fuel_type(),
            "cooling": self.cooling.get_final_energy_by_fuel_type(),
            "dhw": self.dhw.get_final_energy_by_fuel_type(),
            "household_electric": self.household_electric.get_final_energy_by_fuel_type(),
            "additional_gas": self.additional_gas.get_final_energy_by_fuel_type(),
            "energy_generation": self.energy_generation.get_final_energy_by_fuel_type(),
        }

    def get_final_kWh_by_fuel_type(self) -> Dict[str, Dict[str, Any]]:
        """Return a Dict of all the Site (Final) Energy [kWh] by use-type."""
        kwh_m2_data = self.get_final_kWh_m2_by_fuel_type()
        d: Dict[str, Dict] = {}
        for k, v in kwh_m2_data.items():
            d[k] = {}
            energy_type = getattr(self, k)
            area_m2: float = energy_type.reference_area  # TFA or Footprint
            for k2, v2 in v.items():
                try:
                    d[k][k2] = v2 * area_m2  # type: ignore
                except:
                    d[k][k2] = v2
        return d

    def get_primary_kWh_m2_by_fuel_type(self) -> Dict[str, Any]:
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

    def get_primary_kWh_by_fuel_type(self) -> Dict[str, Dict[str, Any]]:
        """Return a Dict of all the Primary (Source) Energy [kWh] by use-type."""
        kwh_m2_data = self.get_primary_kWh_m2_by_fuel_type()
        d: Dict[str, Dict] = {}
        for k, v in kwh_m2_data.items():
            d[k] = {}
            energy_type = getattr(self, k)
            area_m2: float = energy_type.reference_area  # TFA or Footprint
            for k2, v2 in v.items():
                try:
                    d[k][k2] = v2 * area_m2  # type: ignore
                except:
                    d[k][k2] = v2
        return d
