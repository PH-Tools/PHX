# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP "Ventilation" worksheet."""

from __future__ import annotations

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import ventilation_data
from PHX.xl import xl_app


class VentilationInputLocation:
    """Generic input item for Ventilation worksheet items."""

    def __init__(
        self,
        _xl: xl_app.XLConnection,
        _sheet_name: str,
        _search_col: str,
        _search_item: str,
    ):
        self.xl = _xl
        self.sheet_name = _sheet_name
        self.search_col = _search_col
        self.search_item = _search_item

    def find_input_row(self, _row_start: int = 1, _row_end: int = 200) -> int:
        """Return the row number where the search-item is found input."""

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.sheet_name,
            _col=self.search_col,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=_row_start):
            if self.search_item in str(val):
                return i

        raise Exception(
            f'\n\tError: Not able to find the "{self.search_item}" input '
            f'section of the "{self.sheet_name}" worksheet? Please be sure '
            f'the section begins with the "{self.search_item}" flag in column {self.search_col}?'
        )


class Ventilation:
    """IO Controller for the PHPP Ventilation worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Ventilation):
        self.xl = _xl
        self.shape = _shape

        self.io_vent_type = VentilationInputLocation(
            self.xl,
            self.shape.name,
            self.shape.vent_type.locator_col,
            self.shape.vent_type.locator_string,
        )
        self.io_wind_coeff_e = VentilationInputLocation(
            self.xl,
            self.shape.name,
            self.shape.wind_coeff_e.locator_col,
            self.shape.wind_coeff_e.locator_string,
        )
        self.io_wind_coeff_f = VentilationInputLocation(
            self.xl,
            self.shape.name,
            self.shape.wind_coeff_f.locator_col,
            self.shape.wind_coeff_f.locator_string,
        )
        self.io_air_change_rate = VentilationInputLocation(
            self.xl,
            self.shape.name,
            self.shape.airtightness_n50.locator_col,
            self.shape.airtightness_n50.locator_string,
        )
        self.io_net_volume = VentilationInputLocation(
            self.xl,
            self.shape.name,
            self.shape.airtightness_Vn50.locator_col,
            self.shape.airtightness_Vn50.locator_string,
        )
        self.io_multi_vent_worksheet_on = VentilationInputLocation(
            self.xl,
            self.shape.name,
            self.shape.multi_unit_on.locator_col,
            self.shape.multi_unit_on.locator_string,
        )

    def _write_input(
        self,
        _input_item: VentilationInputLocation,
        _phpp_model_item: ventilation_data.VentilationInputItem,
    ) -> None:
        """Generic write input function used by specific input items below."""

        input_row = _input_item.find_input_row()
        xl_item = _phpp_model_item.create_xl_item(self.shape.name, input_row)
        self.xl.write_xl_item(xl_item)

    def write_ventilation_type(self, _phpp_model_obj: ventilation_data.VentilationInputItem) -> None:
        self._write_input(self.io_vent_type, _phpp_model_obj)

    def write_wind_coeff_e(self, _phpp_model_obj: ventilation_data.VentilationInputItem) -> None:
        self._write_input(self.io_wind_coeff_e, _phpp_model_obj)

    def write_wind_coeff_f(self, _phpp_model_obj: ventilation_data.VentilationInputItem) -> None:
        self._write_input(self.io_wind_coeff_f, _phpp_model_obj)

    def write_airtightness_n50(self, _phpp_model_obj: ventilation_data.VentilationInputItem) -> None:
        self._write_input(self.io_air_change_rate, _phpp_model_obj)

    def write_Vn50_volume(self, _phpp_model_obj: ventilation_data.VentilationInputItem) -> None:
        self._write_input(self.io_net_volume, _phpp_model_obj)

    def write_multi_vent_worksheet_on(self, _phpp_model_obj: ventilation_data.VentilationInputItem) -> None:
        self._write_input(self.io_multi_vent_worksheet_on, _phpp_model_obj)

    def activate_variants(self):
        """Link Ventilation Type and Airtightness to the Variants worksheet."""

        # -- Ventilation Type
        self.write_ventilation_type(
            ventilation_data.VentilationInputItem.vent_type(
                self.shape,
                f"={self.shape.variants_col}{self.io_vent_type.find_input_row()}",
            )
        )

        # -- Airtightness
        self.write_airtightness_n50(
            ventilation_data.VentilationInputItem.airtightness_n50(
                self.shape,
                f"={self.shape.variants_col}{self.io_air_change_rate.find_input_row()}",
            )
        )
