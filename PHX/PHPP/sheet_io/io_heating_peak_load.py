# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Classes for the PHPP 'Heating Load' (Peak Heating Load) Worksheet."""

from __future__ import annotations

from typing import Any, Dict

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_app


class HeatingPeakLoad:
    """IO Controller Classes for the PHPP 'Heating Load' (Peak Heating Load) Worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.HeatingPeakLoad):
        self.xl = _xl
        self.shape = _shape

    def _get_peak_load(self, _col: str) -> Dict[str, Unit]:
        """Return a Dict of all the Peak Heating Load data from the specified column."""
        shp = self.shape

        pT = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_losses_transmission}")
        pV = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_losses_ventilation}")
        pL = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_losses}")
        pS = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_gains_solar}")
        pI = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_gains_internal}")
        pG = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_gains}")
        pH = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_load}")

        return {
            "losses_transmission": Unit(float(pT or 0.0), str(shp.unit)),
            "losses_ventilation": Unit(float(pV or 0.0), str(shp.unit)),
            "losses_total": Unit(float(pL or 0.0), str(shp.unit)),
            "gains_solar": Unit(float(pS or 0.0), str(shp.unit)),
            "gains_internal": Unit(float(pI or 0.0), str(shp.unit)),
            "gains_total": Unit(float(pG or 0.0), str(shp.unit)),
            "peak_heating_load": Unit(float(pH or 0.0), str(shp.unit)),
        }

    def get_peak_load_1_data(self) -> Dict[str, Unit]:
        """Return a Dict of all the Weather-1 Peak Heating Load data (Watts | Btuh)"""
        return self._get_peak_load(self.shape.col_weather_1)

    def get_peak_load_2_data(self) -> Dict[str, Unit]:
        """Return a Dict of all the Weather-2 Peak Heating Load data (Watts | Btuh)"""
        return self._get_peak_load(self.shape.col_weather_2)
