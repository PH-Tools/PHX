# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Ventilation Load."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass
class PhxLoadVentilation:
    """A PHX Load for the Ventilation."""

    flow_supply: float = 0.0
    flow_extract: float = 0.0
    flow_transfer: float = 0.0

    @property
    def total_airflow(self) -> float:
        """Returns the total airflow for the ventilation load."""
        return self.flow_supply + self.flow_extract + self.flow_transfer

    def __add__(self, other: PhxLoadVentilation) -> PhxLoadVentilation:
        """Combine two PhxLoadVentilation objects."""
        new_load = PhxLoadVentilation()
        new_load.flow_supply = self.flow_supply + other.flow_supply
        new_load.flow_extract = self.flow_extract + other.flow_extract
        new_load.flow_transfer = self.flow_transfer + other.flow_transfer
        return new_load
