# -*- Python Version: 3.10 -*-

"""PHX Occupancy (People) Load."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PhxLoadOccupancy:
    """A PHX Load for the Occupancy (People)."""

    people_per_m2: float = 0.0  # ppl/m2

    @property
    def unique_key(self) -> str:
        return f"{self.__class__.__name__}_{self.people_per_m2:.6f}_"
