# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP "SolarPV" worksheet."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Any, Dict, List

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_app


@dataclass
class SolarPVData:
    """Convenience class for organizing and cleaning the data."""

    display_name: str = ""
    footprint: Unit = field(default_factory=Unit)
    size: Unit = field(default_factory=Unit)
    annual_pv_energy: Unit = field(default_factory=Unit)

    @classmethod
    def from_PHPP_data(cls, _data: Dict[str, Any]) -> SolarPVData:
        """Clean up the data coming in from PHPP"""
        obj = cls()

        obj.display_name = _data["display_name"]
        obj.footprint = Unit(_data["footprint"], _data["footprint_unit"])
        obj.size = Unit(_data["size"], "KW")
        obj.annual_pv_energy = Unit(_data["pv_energy"], _data["energy_unit"])

        return obj


class SolarPV:
    """IO Controller for the PHPP 'Solar PV' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.SolarPv) -> None:
        self.xl = _xl
        self.shape = _shape

    def get_phpp_data(self) -> List[SolarPVData]:
        """Get the data from the PHPP worksheet."""
        start = f"{self.shape.columns.systems_start}{self.shape.rows.systems_start}"
        end = f"{self.shape.columns.systems_end}{self.shape.rows.systems_end}"
        phpp_data = self.xl.get_data_by_columns(self.shape.name, f"{start}:{end}")

        pv_systems = []
        for i, sys_data in enumerate(phpp_data, start=self.shape.rows.systems_start):
            try:
                current = float(sys_data[self.shape.rows.current - i])  # type: ignore
                voltage = float(sys_data[self.shape.rows.voltage - i])  # type: ignore
                num_panes = float(sys_data[self.shape.rows.num_panels - i])  # type: ignore
                calculated_size_kw = (current * voltage * num_panes) / 1000
            except:
                calculated_size_kw = 0.0

            pv_sys = SolarPVData.from_PHPP_data(
                {
                    "footprint_unit": self.shape.footprint_unit,
                    "energy_unit": self.shape.energy_unit,
                    "display_name": sys_data[self.shape.rows.name - i],
                    "footprint": sys_data[self.shape.rows.footprint - i],
                    "size": calculated_size_kw,
                    "pv_energy": sys_data[self.shape.rows.annual_energy - i],
                }
            )

            pv_systems.append(pv_sys)

        return pv_systems
