# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Occupancy (People) Load."""

from __future__ import annotations
from typing import ClassVar, Any
from dataclasses import dataclass, field


@dataclass
class PhxLoadOccupancy:
    """A PHX Load for the Occupancy (People)."""

    people_per_m2: float = 0.0  # ppl/m2

    @property
    def unique_key(self):
        return "{}_{:.6f}_".format(self.__class__.__name__, self.people_per_m2)
