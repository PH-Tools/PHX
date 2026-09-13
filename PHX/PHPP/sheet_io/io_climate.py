# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP Climate worksheet."""

from __future__ import annotations

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import climate_entry
from PHX.xl import xl_app, xl_data


class Climate:
    """IO Controller for the PHPP Climate Worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Climate):
        self.xl = _xl
        self.shape = _shape
        self.weather_data_start_rows: list[int] = []

    def get_start_rows(self) -> list[int]:
        # TODO: make this find the right starting rows.
        return [self.shape.ud_block.start_row]

    def _first_user_defined_block_start_row(self) -> int:
        if not self.weather_data_start_rows:
            self.weather_data_start_rows = self.get_start_rows()
        return self.weather_data_start_rows[0]

    def write_climate_block(self, _climate_entry: climate_entry.ClimateDataBlock) -> None:
        # Just use the first one for now....
        # TODO: Write all variants to different slots
        start_row = self._first_user_defined_block_start_row()

        for item in _climate_entry.create_xl_items(self.shape.name, start_row):
            self.xl.write_xl_item(item)

    def write_active_climate(
        self,
        _active_climate: climate_entry.ClimateSettings,
        _country_code: str | None = None,
        _region_code: str | None = None,
        _dataset_name: str | None = None,
    ) -> None:
        for item in _active_climate.create_xl_items(
            self.shape.name,
            _country_code=_country_code,
            _region_code=_region_code,
            _dataset_name=_dataset_name,
        ):
            self.xl.write_xl_item(item)

    def _write_selector(self, _range: str, _value: str) -> None:
        self.xl.write_xl_item(xl_data.XlItem(self.shape.name, _range, _value))

    def _validation_range_contains(
        self,
        _value: str,
        _validation_range: shape_model.ClimateValidationRange,
    ) -> bool:
        values = self.xl.get_single_column_data(
            self.shape.name,
            _validation_range.column,
            _validation_range.start_row,
            _validation_range.end_row,
        )
        return _value in values

    def try_library_codes(self, _active_climate: climate_entry.ClimateSettings) -> bool | None:
        """Select valid cascading PHPP library codes, or report fallback/unsupported."""
        validation_ranges = self.shape.library_validation_ranges
        if validation_ranges is None or self.shape.user_defined_selectors is None:
            return None

        codes = _active_climate.phx_site.phpp_codes
        self._write_selector(self.shape.named_ranges.country, codes.country_code)
        self.xl.calculate()
        if not self._validation_range_contains(codes.country_code, validation_ranges.country):
            return False

        self._write_selector(self.shape.named_ranges.region, codes.region_code)
        self.xl.calculate()
        if not self._validation_range_contains(codes.region_code, validation_ranges.region):
            return False

        self.xl.calculate()
        if not self._validation_range_contains(codes.dataset_name, validation_ranges.data_set):
            return False

        self._write_selector(self.shape.named_ranges.data_set, codes.dataset_name)
        self.xl.write_xl_item(_active_climate.create_elevation_xl_item(self.shape.name))
        return True

    def write_user_defined_active_climate(self, _active_climate: climate_entry.ClimateSettings) -> None:
        """Select the first user-defined block using this shape's localized literals."""
        selectors = self.shape.user_defined_selectors
        if selectors is None:
            self.write_active_climate(_active_climate)
            return

        start_row = self._first_user_defined_block_start_row()
        block_index = (start_row - self.shape.ud_block.start_row) // 10
        block_name = _active_climate.phx_site.display_name
        self.write_active_climate(
            _active_climate,
            selectors.country,
            selectors.region,
            f"ud---{block_index:02d}-{block_name}",
        )

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
