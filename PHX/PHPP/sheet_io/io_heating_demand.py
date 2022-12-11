# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Classes for the PHPP 'Heating' (Annual Heating Energy Demand) Worksheet."""

from __future__ import annotations
from typing import Dict, Any

from PHX.xl import xl_app
from PHX.PHPP.phpp_localization import shape_model


class HeatingDemand:
    """IO Controller for the PHPP 'Heating' (Annual Heating Energy Demand) Worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.HeatingDemand):
        self.xl = _xl
        self.shape = _shape

    def get_demand_kWh_year(self) -> Dict[str, Any]:
        """Return a Dict of all the Heating Energy Demand data (kWh-yr)."""
        qT = f"{self.shape.col_kWh_year}{self.shape.row_total_losses_transmission}"
        qV = f"{self.shape.col_kWh_year}{self.shape.row_total_losses_ventilation}"
        qL = f"{self.shape.col_kWh_year}{self.shape.row_total_losses}"
        qS = f"{self.shape.col_kWh_year}{self.shape.row_total_gains_solar}"
        qI = f"{self.shape.col_kWh_year}{self.shape.row_total_gains_internal}"
        util = f"{self.shape.col_kWh_year}{self.shape.row_utilization_factor}"
        qG = f"{self.shape.col_kWh_year}{self.shape.row_useful_gains}"
        qH = f"{self.shape.col_kWh_year}{self.shape.row_annual_demand}"
        return {
            "losses_transmission": self.xl.get_data(self.shape.name, qT),
            "losses_ventilation": self.xl.get_data(self.shape.name, qV),
            "gains_solar": self.xl.get_data(self.shape.name, qS),
            "gains_internal": self.xl.get_data(self.shape.name, qI),
            "utilization_factor": self.xl.get_data(self.shape.name, util),
            "heating_demand": self.xl.get_data(self.shape.name, qH),
        }

    def get_demand_kWh_m2_year(self) -> Dict[str, Any]:
        """Return a Dict of all the Specific Heating Energy Demand data (kWh/m2-yr)."""
        qT = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_losses_transmission}"
        qV = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_losses_ventilation}"
        qL = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_losses}"
        qS = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_gains_solar}"
        qI = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_gains_internal}"
        util = f"{self.shape.col_kWh_year}{self.shape.row_utilization_factor}"
        qG = f"{self.shape.col_kWh_m2_year}{self.shape.row_useful_gains}"
        qH = f"{self.shape.col_kWh_m2_year}{self.shape.row_annual_demand}"
        return {
            "heating_demand": self.xl.get_data(self.shape.name, qH),
            "losses_transmission": self.xl.get_data(self.shape.name, qT),
            "losses_ventilation": self.xl.get_data(self.shape.name, qV),
            "total_loss": self.xl.get_data(self.shape.name, qL),
            "gains_solar": self.xl.get_data(self.shape.name, qS),
            "gains_internal": self.xl.get_data(self.shape.name, qI),
            "utilization_factor": self.xl.get_data(self.shape.name, util),
        }
