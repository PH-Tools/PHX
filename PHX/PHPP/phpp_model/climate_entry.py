# -*- Python Version: 3.10 -*-

"""Data-entry constructor for the Climate Worksheet."""

from dataclasses import dataclass
from functools import partial
from typing import ClassVar

from PHX.model import phx_site
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


@dataclass
class ClimateSettings:
    """The active climate data selections."""

    __slots__ = ("shape", "phx_site")
    shape: shape_model.Climate
    phx_site: phx_site.PhxSite

    def create_selector_xl_items(
        self,
        _sheet_name: str,
        _country_code: str | None = None,
        _region_code: str | None = None,
        _dataset_name: str | None = None,
    ) -> list[xl_data.XlItem]:
        """Return a list of the XL items to write to the worksheet."""
        XLItemClimate = partial(xl_data.XlItem, _sheet_name)
        country_code = self.phx_site.phpp_codes.country_code if _country_code is None else _country_code
        region_code = self.phx_site.phpp_codes.region_code if _region_code is None else _region_code
        dataset_name = self.phx_site.phpp_codes.dataset_name if _dataset_name is None else _dataset_name

        return [
            XLItemClimate(self.shape.named_ranges.country, country_code),
            XLItemClimate(self.shape.named_ranges.region, region_code),
            XLItemClimate(self.shape.named_ranges.data_set, dataset_name),
        ]

    def create_elevation_xl_item(self, _sheet_name: str) -> xl_data.XlItem:
        """Return the site-elevation override item."""
        XLItemClimate = partial(xl_data.XlItem, _sheet_name)
        if self.phx_site.location.site_elevation:
            return XLItemClimate(
                self.shape.defined_ranges.site_altitude,
                self.phx_site.location.site_elevation,
                "M",
                self.shape.ud_block.input_columns.elevation_unit,
            )
        return XLItemClimate(
            self.shape.defined_ranges.site_altitude,
            f"={self.shape.defined_ranges.weather_station_altitude}",
        )

    def create_xl_items(
        self,
        _sheet_name: str,
        _start_row: int | None = None,
        *,
        _country_code: str | None = None,
        _region_code: str | None = None,
        _dataset_name: str | None = None,
    ) -> list[xl_data.XlItem]:
        """Return selector and elevation items for the active climate.

        ``_start_row`` remains accepted for compatibility; named ranges now
        define the selector locations.
        """
        return [
            *self.create_selector_xl_items(
                _sheet_name,
                _country_code,
                _region_code,
                _dataset_name,
            ),
            self.create_elevation_xl_item(_sheet_name),
        ]


@dataclass
class ClimateDataBlock:
    """A single Climate / Weather-Station entry block."""

    month_order: ClassVar[list[str]] = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    __slots__ = ("shape", "phx_site")
    shape: shape_model.Climate
    phx_site: phx_site.PhxSite

    def _create_range(self, _field_name: str, _row_offset: int, _start_row: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.ud_block.input_columns, _field_name)
        return f"{col}{_start_row + _row_offset}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.ud_block.input_rows, _field_name).unit

    def _get_input_unit(self, _input_name):
        INPUT_UNITS = {
            "radiation": "KWH/M2",
            "temperature": "C",
        }
        for k in INPUT_UNITS:
            if k in _input_name:
                return INPUT_UNITS[k]

    def create_xl_items(self, _sheet_name: str, _start_row: int) -> list[xl_data.XlItem]:
        """Return a list of the XL items to write to the worksheet."""
        create_range = partial(self._create_range, _start_row=_start_row)
        XLItemClimate = partial(xl_data.XlItem, _sheet_name)
        phx_climate = self.phx_site.climate
        phx_site = self.phx_site.location

        block_name_range = self.shape.named_ranges.ud_block_name or create_range("name", 0)
        block_comment_range = self.shape.named_ranges.ud_block_comment or create_range("comment", 9)

        # -- Build the Header assembly attributes
        xl_items_list: list[xl_data.XlItem] = [
            XLItemClimate(block_name_range, self.phx_site.display_name),
            XLItemClimate(create_range("latitude", 0), phx_site.latitude),
            XLItemClimate(create_range("longitude", 0), phx_site.longitude),
            XLItemClimate(
                create_range("elevation", 0),
                phx_climate.station_elevation,
                "M",
                self.shape.ud_block.input_columns.elevation_unit,
            ),
            XLItemClimate(
                create_range("summer_delta_t", 0),
                phx_climate.daily_temp_swing,
                "DELTA-C",
                self.shape.ud_block.input_columns.summer_delta_t_unit,
            ),
            XLItemClimate(block_comment_range, self.phx_site.source),
        ]

        # -- Add the monthly climate data
        row_shape = sorted(
            [(k, v) for k, v in vars(self.shape.ud_block.input_rows).items()],
            key=lambda t: t[1].row,
        )
        for i, month in enumerate(self.month_order, start=0):
            for row in row_shape:
                row_name, row_input_item = row
                xl_items_list.append(
                    XLItemClimate(
                        create_range(month, row_input_item.row),
                        getattr(phx_climate, row_name)[i],
                        self._get_input_unit(row_name),
                        self._get_target_unit(row_name),
                    )
                )

        # -- Add in the peak-load data
        for col_name in [
            "peak_heating_1",
            "peak_heating_2",
            "peak_cooling_1",
            "peak_cooling_2",
        ]:
            for row in row_shape:
                row_name, row_input_item = row
                try:
                    xl_items_list.append(
                        XLItemClimate(
                            create_range(col_name, row_input_item.row),
                            getattr(getattr(phx_climate, col_name), row_name),
                            self._get_input_unit(row_name),
                            self._get_target_unit(row_name),
                        )
                    )
                except AttributeError:
                    continue

        return xl_items_list
