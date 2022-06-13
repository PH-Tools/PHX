# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Data-entry constructor for the Climate Worksheet."""

from dataclasses import dataclass
from typing import Dict, List, Tuple, ClassVar
from functools import partial

from PHX.to_PHPP import xl_data
from PHX.model import phx_site
from PHX.to_PHPP.phpp_localization import shape_model



@dataclass
class ClimateSettings:
    """The active climate data selections."""

    __slots__ = ("shape", "phx_site")
    shape: shape_model.Climate
    phx_site: phx_site.PhxSite

    def _create_range(self, _field_name: str, _row_offset: int, _start_row: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.active_dataset.input_columns, _field_name)
        return f'{col}{_start_row + _row_offset}'

    def create_xl_items(self, _sheet_name: str, _start_row: int) -> List[xl_data.XlItem]:
        """Return a list of the XL items to write to the worksheet."""
        create_range = partial(self._create_range, _start_row=_start_row)

        items: List[Tuple[str, xl_data.xl_writable]] = [
            (create_range('country', 0), self.phx_site.phpp_codes.country_code),
            (create_range('region', 1), self.phx_site.phpp_codes.region_code),
            (create_range('dataset', 3), f"{self.phx_site.phpp_codes.dataset_name}"),
        ]

        if self.phx_site.location.site_elevation:
            items.append(
                 (create_range('elevation_override', 9), self.phx_site.location.site_elevation),
            )
        else:
            # probably shouldn't hardcode D17 here...
            items.append(
                 ('D18', '=D17'),
            )
        return [xl_data.XlItem(_sheet_name, *item) for item in items]


@dataclass
class ClimateDataBlock:
    """A single Climate / Weather-Station entry block."""

    month_order: ClassVar[List[str]] = ['jan', 'feb', 'mar', 'apr',
                                        'may', 'jun', 'jul', 'aug',
                                        'sep', 'oct', 'nov', 'dec']
    __slots__ = ("shape", "phx_site")
    shape: shape_model.Climate
    phx_site: phx_site.PhxSite

    def _create_range(self, _field_name: str, _row_offset: int, _start_row: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.ud_block.input_columns, _field_name)
        return f'{col}{_start_row + _row_offset}'

    def create_xl_items(self, _sheet_name: str, _start_row: int) -> List[xl_data.XlItem]:
        """Return a list of the XL items to write to the worksheet."""
        create_range = partial(self._create_range, _start_row=_start_row)
        phx_climate = self.phx_site.climate
        phx_site = self.phx_site.location

        # -- Build the Header assembly attributes
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (create_range('latitude', 0), phx_site.latitude),
            (create_range('longitude', 0), phx_site.longitude),
            (create_range('elevation', 0), phx_climate.station_elevation),
            (create_range('display_name', 0), self.phx_site.display_name),
            (create_range('summer_delta_t', 0), phx_climate.daily_temp_swing),
            (create_range('source', 0), self.phx_site.source),
        ]

        # -- Add in the monthly data
        for i, month in enumerate(self.month_order, start=0):
            layer_items: List[Tuple[str, xl_data.xl_writable]] = [
                (create_range(month, 1), phx_climate.monthly_temperature_air[i]),
                (create_range(month, 2), phx_climate.monthly_radiation_north[i]),
                (create_range(month, 3), phx_climate.monthly_radiation_east[i]),
                (create_range(month, 4), phx_climate.monthly_radiation_south[i]),
                (create_range(month, 5), phx_climate.monthly_radiation_west[i]),
                (create_range(month, 6), phx_climate.monthly_radiation_global[i]),
                (create_range(month, 7), phx_climate.monthly_temperature_dewpoint[i]),
                (create_range(month, 8), phx_climate.monthly_temperature_sky[i]),
            ]
            items.extend(layer_items)

        # -- Add in the peak-load data
        for col_name in ["peak_heating_1", "peak_heating_2", "peak_cooling_1", "peak_cooling_2"]:
            layer_items: List[Tuple[str, xl_data.xl_writable]] = [
                (create_range(col_name, 1), getattr(phx_climate, col_name).temp),
                (create_range(col_name, 2), getattr(phx_climate, col_name).rad_north),
                (create_range(col_name, 3), getattr(phx_climate, col_name).rad_east),
                (create_range(col_name, 4), getattr(phx_climate, col_name).rad_south),
                (create_range(col_name, 5), getattr(phx_climate, col_name).rad_west),
                (create_range(col_name, 6), getattr(phx_climate, col_name).rad_global),
            ]
            items.extend(layer_items)

        return [xl_data.XlItem(_sheet_name, *item) for item in items]
