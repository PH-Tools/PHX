# -*- Python Version: 3.10 -*-

"""PHX Lighting Load."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PhxLoadLighting:
    """Lighting load defining the installed lighting power density for a PHX zone or space.

    Attributes:
        installed_w_per_m2 (float): Installed lighting power density in watts
            per square meter of treated floor area. Default: 0.0.
    """

    installed_w_per_m2: float = 0.0

    @property
    def unique_key(self):
        """Return a unique key string based on the installed lighting power density."""
        return f"{self.__class__.__name__}_{self.installed_w_per_m2:.4f}_"
