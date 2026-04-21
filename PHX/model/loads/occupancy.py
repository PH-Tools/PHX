# -*- Python Version: 3.10 -*-

"""PHX Occupancy (People) Load."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PhxLoadOccupancy:
    """Occupancy load defining the people density for a PHX zone or space.

    Attributes:
        people_per_m2 (float): Occupancy density in people per square meter
            of treated floor area. Default: 0.0.
    """

    people_per_m2: float = 0.0  # ppl/m2

    @property
    def unique_key(self) -> str:
        """Return a unique key string based on the occupancy density value."""
        return f"{self.__class__.__name__}_{self.people_per_m2:.6f}_"
