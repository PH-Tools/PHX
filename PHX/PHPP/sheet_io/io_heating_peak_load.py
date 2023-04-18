# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Classes for the PHPP 'Heating Load' (Peak Heating Load) Worksheet."""

from __future__ import annotations
from typing import Dict, Any

from PHX.xl import xl_app
from PHX.PHPP.phpp_localization import shape_model


class HeatingPeakLoad:
    """IO Controller Classes for the PHPP 'Heating Load' (Peak Heating Load) Worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.HeatingPeakLoad):
        self.xl = _xl
        self.shape = _shape

    def get_load_W1(self) -> Dict[str, Any]:
        """Return a Dict of all the Weather-1 Peak Heating Load data (Watts)"""
        pT = f"{self.shape.col_Watts1}{self.shape.row_total_losses_transmission}"
        pV = f"{self.shape.col_Watts1}{self.shape.row_total_losses_ventilation}"
        pL = f"{self.shape.col_Watts1}{self.shape.row_total_losses}"
        pS = f"{self.shape.col_Watts1}{self.shape.row_total_gains_solar}"
        pI = f"{self.shape.col_Watts1}{self.shape.row_total_gains_internal}"
        pG = f"{self.shape.col_Watts1}{self.shape.row_total_gains}"
        pH = f"{self.shape.col_Watts1}{self.shape.row_total_load}"
        return {
            "losses_transmission": self.xl.get_data(self.shape.name, pT),
            "losses_ventilation": self.xl.get_data(self.shape.name, pV),
            "losses_total": self.xl.get_data(self.shape.name, pL),
            "gains_solar": self.xl.get_data(self.shape.name, pS),
            "gains_internal": self.xl.get_data(self.shape.name, pI),
            "gains_total": self.xl.get_data(self.shape.name, pG),
            "peak_heating_load": self.xl.get_data(self.shape.name, pH),
        }

    def get_load_W2(self) -> Dict[str, Any]:
        """Return a Dict of all the Weather-2 Peak Heating Load data (Watts)"""
        pT = f"{self.shape.col_Watts2}{self.shape.row_total_losses_transmission}"
        pV = f"{self.shape.col_Watts2}{self.shape.row_total_losses_ventilation}"
        pL = f"{self.shape.col_Watts2}{self.shape.row_total_losses}"
        pS = f"{self.shape.col_Watts2}{self.shape.row_total_gains_solar}"
        pI = f"{self.shape.col_Watts2}{self.shape.row_total_gains_internal}"
        pG = f"{self.shape.col_Watts2}{self.shape.row_total_gains}"
        pH = f"{self.shape.col_Watts2}{self.shape.row_total_load}"
        return {
            "losses_transmission": self.xl.get_data(self.shape.name, pT),
            "losses_ventilation": self.xl.get_data(self.shape.name, pV),
            "losses_total": self.xl.get_data(self.shape.name, pL),
            "gains_solar": self.xl.get_data(self.shape.name, pS),
            "gains_internal": self.xl.get_data(self.shape.name, pI),
            "gains_total": self.xl.get_data(self.shape.name, pG),
            "peak_heating_load": self.xl.get_data(self.shape.name, pH),
        }
