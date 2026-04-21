# -*- Python Version: 3.10 -*-

"""PHX Window Shade devices for solar gain reduction and overheating control."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class PhxWindowShade:
    """A window shading device used for solar gain reduction and overheating control.

    Each shade carries a reduction factor (0.0 = fully shaded, 1.0 = no shading)
    and supplementary radiative/thermal properties used by the WUFI shading calculation.

    Attributes:
        display_name (str): User-facing name for the shading device. Default: "__unnamed_shade__".
        operation_mode (int): Shade operation mode (1 = reduce overheating). Default: 1.
        reduction_factor (float): Solar reduction factor applied when shade is active (0.0-1.0). Default: 1.0.
        external_emissivity (float): Long-wave emissivity of the exterior shade surface. Default: 0.8.
        absorptivity (float): Short-wave absorptivity of the shade surface. Default: 0.0.
        thermal_resistance_supplement (float): Additional thermal resistance from the shade [m2K/W]. Default: 0.0.
        thermal_resistance_cavity (float): Thermal resistance of the cavity behind the shade [m2K/W]. Default: 0.0.
        radiation_limit (float): Solar radiation threshold for shade activation [W/m2]. Default: 1000.0.
        exclude_weekends (bool): If True, shade is inactive on weekends. Default: False.
    """

    _count: ClassVar[int] = 0

    _identifier: uuid.UUID | str = field(init=False, default_factory=uuid.uuid4)
    id_num: int = field(init=False, default=0)
    display_name: str = "__unnamed_shade__"
    operation_mode: int = 1  # 1=Reduce overheating
    reduction_factor: float = 1.0

    # -- Extra junk
    external_emissivity: float = 0.8
    absorptivity: float = 0.0
    thermal_resistance_supplement: float = 0.0
    thermal_resistance_cavity: float = 0.0
    radiation_limit: float = 1_000.0
    exclude_weekends: bool = False

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def identifier(self) -> str:
        """The unique string identifier for this shading device."""
        return str(self._identifier)

    @identifier.setter
    def identifier(self, _in: str):
        if not _in:
            return
        self._identifier = str(_in)

    def __hash__(self) -> int:
        return hash(self.identifier)
