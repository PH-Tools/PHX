# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Lighting Load."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass
class PhxLoadLighting:
    """A PHX Load for the Lighting."""

    installed_w_per_m2: float = 0.0

    @property
    def unique_key(self):
        return "{}_{:.4f}_".format(self.__class__.__name__, self.installed_w_per_m2)
