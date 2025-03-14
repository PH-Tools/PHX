# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP Climate worksheet."""

from __future__ import annotations

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import climate_entry
from PHX.xl import xl_app


class Climate:
    """IO Controller for the PHPP Climate Worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Climate):
        self.xl = _xl
        self.shape = _shape
        self.weather_data_start_rows: list[int] = []

    def get_start_rows(self) -> list[int]:
        # TODO: make this find the right starting rows.
        return [self.shape.ud_block.start_row]

    def write_climate_block(self, _climate_entry: climate_entry.ClimateDataBlock) -> None:
        if not self.weather_data_start_rows:
            self.weather_data_start_rows = self.get_start_rows()

        # Just use the first one for now....
        # TODO: Write all variants to different slots
        start_row = self.weather_data_start_rows[0]

        for item in _climate_entry.create_xl_items(self.shape.name, start_row):
            self.xl.write_xl_item(item)

    def write_active_climate(self, _active_climate: climate_entry.ClimateSettings) -> None:
        start_row = 9
        for item in _active_climate.create_xl_items(self.shape.name, start_row):
            self.xl.write_xl_item(item)

    def read_active_country(self) -> str:
        return str(self.xl.get_single_data_item(self.shape.name, self.shape.named_ranges.country))

    def read_active_region(self) -> str:
        return str(self.xl.get_single_data_item(self.shape.name, self.shape.named_ranges.region))

    def read_active_data_set(self) -> str:
        return str(self.xl.get_single_data_item(self.shape.name, self.shape.named_ranges.data_set))

    def read_station_elevation(self) -> str:
        return str(self.xl.get_single_data_item(self.shape.name, self.shape.defined_ranges.weather_station_altitude))

    def read_site_elevation(self) -> str:
        return str(self.xl.get_single_data_item(self.shape.name, self.shape.defined_ranges.site_altitude))

    def read_latitude(self) -> float:
        return float(self.xl.get_single_data_item(self.shape.name, self.shape.defined_ranges.latitude) or 0.0)

    def read_longitude(self) -> float:
        return float(self.xl.get_single_data_item(self.shape.name, self.shape.defined_ranges.longitude) or 0.0)

    def read_active_monthly_data(self) -> list[list]:
        """Return the Monthly Climate data for the currently active set from the 'Climate' worksheet.

        Data is returned 'by column' from the results section of the worksheet.
        """

        rng = f"{self.shape.active_block.start_col}{self.shape.active_block.start_row}:{self.shape.active_block.end_col}{self.shape.active_block.end_row}"
        data = self.xl.get_data_by_columns(
            _sheet_name=self.shape.name,
            _range_address=rng,
        )
        return data
