# -*- Python Version: 3.10 -*-

"""PHX Lighting Load."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PhxLoadLighting:
    """A PHX Load for the Lighting."""

    installed_w_per_m2: float = 0.0

    @property
    def unique_key(self):
        return f"{self.__class__.__name__}_{self.installed_w_per_m2:.4f}_"
