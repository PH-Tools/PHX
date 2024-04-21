# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Window Shades."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import ClassVar, Union


@dataclass
class PhxWindowShade:
    _count: ClassVar[int] = 0

    _identifier: Union[uuid.UUID, str] = field(init=False, default_factory=uuid.uuid4)
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
        return str(self._identifier)

    @identifier.setter
    def identifier(self, _in: str):
        if not _in:
            return
        self._identifier = str(_in)

    def __hash__(self) -> int:
        return hash(self.identifier)
