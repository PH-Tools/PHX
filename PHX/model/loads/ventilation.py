# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Ventilation Load."""

from __future__ import annotations
from typing import ClassVar, Any
from dataclasses import dataclass, field


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
