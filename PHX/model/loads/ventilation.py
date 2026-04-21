# -*- Python Version: 3.10 -*-

"""PHX Ventilation Load."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PhxLoadVentilation:
    """Ventilation load defining the fresh-air supply, extract, and transfer airflow rates for a PHX zone or space.

    Attributes:
        flow_supply (float): Supply airflow rate (m3/h). Default: 0.0.
        flow_extract (float): Extract airflow rate (m3/h). Default: 0.0.
        flow_transfer (float): Transfer airflow rate (m3/h). Default: 0.0.
    """

    flow_supply: float = 0.0
    flow_extract: float = 0.0
    flow_transfer: float = 0.0

    @property
    def total_airflow(self) -> float:
        """Return the combined supply, extract, and transfer airflow."""
        return self.flow_supply + self.flow_extract + self.flow_transfer

    def __add__(self, other: PhxLoadVentilation) -> PhxLoadVentilation:
        """Combine two PhxLoadVentilation objects."""
        new_load = PhxLoadVentilation()
        new_load.flow_supply = self.flow_supply + other.flow_supply
        new_load.flow_extract = self.flow_extract + other.flow_extract
        new_load.flow_transfer = self.flow_transfer + other.flow_transfer
        return new_load
