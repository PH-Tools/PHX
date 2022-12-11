# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP PER Worksheet."""

from __future__ import annotations
from typing import Optional, List, Dict, Any

from PHX.xl import xl_app, xl_data
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.sheet_io.io_exceptions import FindSectionMarkerException


# -----------------------------------------------------------------------------


class BaseBlock:
    """Base class for all PER Data Blocks (Heating, Cooling, etc..)"""

    def __init__(
        self,
        _host: PER,
        _xl: xl_app.XLConnection,
        _shape: shape_model.PerDataBlock,
    ):
        self.host = _host
        self.xl = _xl
        self.shape = _shape
        self._phpp_data: Optional[Dict[str, List[xl_data.xl_range_single_value]]] = None
        self._block_header_row: Optional[int] = None
        self._block_start_row: Optional[int] = None
        self._block_end_row: Optional[int] = None

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
    def block_header_row(self) -> int:
        """Return the Row number where the block 'Heading' is found."""
        if not self._block_header_row:
            self._block_header_row = self.find_block_header_row()
        return self._block_header_row

    def find_block_header_row(self) -> int:
        """Locate the row number for the block heading"""
        data = self.xl.get_single_column_data(
            self.host.shape.name,
            self.host.column_locator,
            self.host.heading_row,
            self.host.heading_row + 100,
        )
        search_string = self.shape.locator_string_heading
        row_number = self.xl.find_row(search_string, data, self.host.heading_row)
        if not row_number:
            raise FindSectionMarkerException(
                search_string, self.host.shape.name, self.host.column_locator
            )
        return row_number

    def find_block_start_row(self) -> int:
        """Locate the row number for the first row of the data block."""
        data = self.xl.get_single_column_data(
            self.host.shape.name,
            self.host.column_locator,
            self.block_header_row,
            self.block_header_row + 10,
        )

        search_string = self.shape.locator_string_start
        row_number = self.xl.find_row(search_string, data, self.block_header_row)
        if not row_number:
            raise FindSectionMarkerException(
                search_string, self.host.shape.name, self.host.column_locator
            )
        return row_number

    def find_block_end_row(self) -> int:
        """Locate the row number for the last row of the data block."""
        data = self.xl.get_single_column_data(
            self.host.shape.name,
            self.host.column_locator,
            self.block_start_row,
            self.block_start_row + 25,
        )

        search_string = self.shape.locator_string_end
        row_number = self.xl.find_row(search_string, data, self.block_start_row)
        if not row_number:
            raise FindSectionMarkerException(
                search_string, self.host.shape.name, self.host.column_locator
            )
        return row_number

    def get_data(self) -> Dict[str, List[xl_data.xl_range_single_value]]:
        """Return all the Block's data from Excel"""
        address = f"{self.host.shape.locator_col}{self.block_start_row}:{self.host.column_co2_emissions}{self.block_end_row}"
        return self.xl.get_data_with_column_letters(self.host.shape.name, address)

    def get_site_energy_by_fuel_type(self) -> Dict[str, xl_data.xl_range_single_value]:
        """Return the Block's Site Energy as a dict of values."""
        use_types = self.phpp_data[self.host.shape.locator_col]

        # Override because they changed the location, but only for generation. Sigh.
        column_site_demand = getattr(
            self, "column_site_demand", self.host.column_site_demand
        )

        site_energy = self.phpp_data[column_site_demand]
        return {str(t): e for t, e in zip(use_types, site_energy)}


# -----------------------------------------------------------------------------


class Heating(BaseBlock):
    """Heating Data Block."""

    def __init__(self, _host: PER, _xl: xl_app.XLConnection, _shape: shape_model.Per):
        super().__init__(_host, _xl, _shape.heating)


class Cooling(BaseBlock):
    """Cooling Energy"""

    def __init__(self, _host: PER, _xl: xl_app.XLConnection, _shape: shape_model.Per):
        super().__init__(_host, _xl, _shape.cooling)


class DHW(BaseBlock):
    """Hot-Water Energy"""

    def __init__(self, _host: PER, _xl: xl_app.XLConnection, _shape: shape_model.Per):
        super().__init__(_host, _xl, _shape.dhw)


class HouseholdElectric(BaseBlock):
    """Household Electric (Lighting, Appliances, etc)"""

    def __init__(self, _host: PER, _xl: xl_app.XLConnection, _shape: shape_model.Per):
        super().__init__(_host, _xl, _shape.household_electric)


class AdditionalGas(BaseBlock):
    """Gas for cooking, dryers"""

    def __init__(self, _host: PER, _xl: xl_app.XLConnection, _shape: shape_model.Per):
        super().__init__(_host, _xl, _shape.additional_gas)


class EnergyGeneration(BaseBlock):
    """Solar, Wind Energy Generation"""

    def __init__(self, _host: PER, _xl: xl_app.XLConnection, _shape: shape_model.Per):
        super().__init__(_host, _xl, _shape.energy_generation)
        # Override because they changed the location, but only for generation. Sigh.
        self.column_site_demand: str = "S"


# -----------------------------------------------------------------------------


class PER:
    """IO Controller for the PHPP 'PER' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Per):
        self.xl = _xl
        self.shape = _shape
        self.heating: Heating = Heating(self, _xl, _shape)
        self.cooling: Cooling = Cooling(self, _xl, _shape)
        self.dhw: DHW = DHW(self, _xl, _shape)
        self.household_electric: HouseholdElectric = HouseholdElectric(self, _xl, _shape)
        self.additional_gas: AdditionalGas = AdditionalGas(self, _xl, _shape)
        self.energy_generation: EnergyGeneration = EnergyGeneration(self, _xl, _shape)

    @property
    def column_locator(self) -> str:
        return self.shape.locator_col

    @property
    def heading_row(self) -> int:
        return 15

    @property
    def column_site_demand(self) -> str:
        return "T"

    @property
    def column_per_factor(self) -> str:
        return "U"

    @property
    def column_per_demand(self) -> str:
        return "V"

    @property
    def column_pe_factor(self) -> str:
        return "W"

    @property
    def column_pe_demand(self) -> str:
        return "X"

    @property
    def column_co2_factor(self) -> str:
        return "Y"

    @property
    def column_co2_emissions(self) -> str:
        return "Z"

    def get_site_energy_by_fuel_type(self) -> Dict[str, Any]:
        """Return a Dict of all the Site (Final) Energy by use-type."""
        self.xl.get_sheet_by_name(self.shape.name).activate()

        return {
            "heating": self.heating.get_site_energy_by_fuel_type(),
            "cooling": self.cooling.get_site_energy_by_fuel_type(),
            "dhw": self.dhw.get_site_energy_by_fuel_type(),
            "household_electric": self.household_electric.get_site_energy_by_fuel_type(),
            "additional_gas": self.additional_gas.get_site_energy_by_fuel_type(),
            "energy_generation": self.energy_generation.get_site_energy_by_fuel_type(),
        }
