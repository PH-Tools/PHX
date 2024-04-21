# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Classes for the PHPP 'Heating' (Annual Heating Energy Demand) Worksheet."""

from __future__ import annotations

from typing import Any, Dict

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_app


class HeatingDemand:
    """IO Controller for the PHPP 'Heating' (Annual Heating Energy Demand) Worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.HeatingDemand) -> None:
        self.xl = _xl
        self.shape = _shape

    def _get_annual_demand(self, _col: str) -> Dict[str, Unit]:
        shp = self.shape
        qT = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_losses_transmission}")
        qV = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_losses_ventilation}")
        qL = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_losses}")
        qS = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_gains_solar}")
        qI = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_total_gains_internal}")
        util = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_utilization_factor}")
        qG = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_useful_gains}")
        qH = self.xl.get_single_data_item(shp.name, f"{_col}{shp.row_annual_demand}")

        return {
            "losses_transmission": Unit(float(qT or 0.0), str(shp.unit)),
            "losses_ventilation": Unit(float(qV or 0.0), str(shp.unit)),
            "gains_solar": Unit(float(qS or 0.0), str(shp.unit)),
            "gains_internal": Unit(float(qI or 0.0), str(shp.unit)),
            "utilization_factor": Unit(float(util or 0.0), "%"),
            "heating_demand": Unit(float(qH or 0.0), str(shp.unit)),
        }

    def get_annual_demand(self) -> Dict[str, Unit]:
        """Return a Dict of all the Heating Energy Demand data (kWh-yr)."""
        return self._get_annual_demand(self.shape.col_kWh_year)

    def get_specific_annual_demand(self) -> Dict[str, Unit]:
        """Return a Dict of all the Specific Heating Energy Demand data (kWh/m2-yr)."""
        return self._get_annual_demand(self.shape.col_kWh_m2_year)
