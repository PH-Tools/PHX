# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Classes for the PHPP 'Cooling' (Annual Cooling Energy Demand) Worksheet."""

from __future__ import annotations
from typing import Dict, Any

from PHX.xl import xl_app
from PHX.PHPP.phpp_localization import shape_model


class CoolingDemand:
    """IO Controller for the PHPP 'Cooling' (Annual Cooling Energy Demand) Worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.CoolingDemand):
        self.xl = _xl
        self.shape = _shape

    def get_demand_kWh_year(self) -> Dict[str, Any]:
        """Return a Dict of all the Cooling Energy Demand data (kWh-yr)."""
        qT = f"{self.shape.col_kWh_year}{self.shape.row_total_losses_transmission}"
        qV = f"{self.shape.col_kWh_year}{self.shape.row_total_losses_ventilation}"
        qL = f"{self.shape.col_kWh_year}{self.shape.row_total_losses}"
        eta = f"{self.shape.col_kWh_year}{self.shape.row_utilization_factor}"
        qVn = f"{self.shape.col_kWh_year}{self.shape.row_useful_losses}"

        qS = f"{self.shape.col_kWh_year}{self.shape.row_total_gains_solar}"
        qI = f"{self.shape.col_kWh_year}{self.shape.row_total_gains_internal}"
        qF = f"{self.shape.col_kWh_year}{self.shape.row_total_gains}"
        qK = f"{self.shape.col_kWh_year}{self.shape.row_annual_sensible_demand}"
        qDr = f"{self.shape.address_specific_latent_cooling_demand}"

        # -- Latent demand, cus PHPP 9 cooling a mess....
        tfa = self.xl.get_data(self.shape.name, self.shape.address_tfa)
        latent_demand_kWh_m2 = self.xl.get_data(self.shape.name, qDr)
        latent_demand_kWh = latent_demand_kWh_m2 * tfa  # type: ignore

        return {
            "sensible_cooling_demand": self.xl.get_data(self.shape.name, qK),
            "latent_cooling_demand": latent_demand_kWh,
            "losses_transmission": self.xl.get_data(self.shape.name, qT),
            "losses_ventilation": self.xl.get_data(self.shape.name, qV),
            "utilization_factor": self.xl.get_data(self.shape.name, eta),
            "gains_solar": self.xl.get_data(self.shape.name, qS),
            "gains_internal": self.xl.get_data(self.shape.name, qI),
        }

    def get_demand_kWh_m2_year(self) -> Dict[str, Any]:
        """Return a Dict of all the Cooling Energy Demand data (kWh-yr)."""
        qT = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_losses_transmission}"
        qV = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_losses_ventilation}"
        qL = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_losses}"
        eta = f"{self.shape.col_kWh_year}{self.shape.row_utilization_factor}"
        qVn = f"{self.shape.col_kWh_m2_year}{self.shape.row_useful_losses}"

        qS = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_gains_solar}"
        qI = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_gains_internal}"
        qF = f"{self.shape.col_kWh_m2_year}{self.shape.row_total_gains}"
        qK = f"{self.shape.col_kWh_m2_year}{self.shape.row_annual_sensible_demand}"
        qDr = f"{self.shape.address_specific_latent_cooling_demand}"

        return {
            "sensible_cooling_demand": self.xl.get_data(self.shape.name, qK),
            "latent_cooling_demand": self.xl.get_data(self.shape.name, qDr),
            "losses_transmission": self.xl.get_data(self.shape.name, qT),
            "losses_ventilation": self.xl.get_data(self.shape.name, qV),
            "utilization_factor": self.xl.get_data(self.shape.name, eta),
            "gains_solar": self.xl.get_data(self.shape.name, qS),
            "gains_internal": self.xl.get_data(self.shape.name, qI),
        }
