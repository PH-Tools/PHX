# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Ventilation Ducting Distribution Objects."""


from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional

from ladybug_geometry.geometry3d.polyline import LineSegment3D

from PHX.model.enums.hvac import PhxVentDuctType


@dataclass
class PhxDuctSegment:
    """An individual Duct Segment Segment."""

    identifier: str
    display_name: str
    geometry: LineSegment3D
    diameter_m: float
    height_m: Optional[float]
    width_m: Optional[float]
    insulation_thickness_m: float
    insulation_conductivity_wmk: float
    insulation_reflective: bool

    @property
    def length(self) -> float:
        return self.geometry.length

    @property
    def diameter_mm(self) -> float:
        """Return the diameter in MM."""
        return self.diameter_m * 1000.0

    @property
    def height_mm(self) -> Optional[float]:
        """Return the height in MM."""
        if self.height_m:
            return self.height_m * 1000.0
        else:
            return None

    @property
    def width_mm(self) -> Optional[float]:
        """Return the width in MM."""
        if self.width_m:
            return self.width_m * 1000.0
        else:
            return None

    @property
    def insulation_thickness_mm(self) -> float:
        """Return the insulation-thickness in MM."""
        return self.insulation_thickness_m * 1000.0


@dataclass
class PhxDuctElement:
    """A Duct Element / Run made of one or more PhxDuctSegments."""

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)

    identifier: str
    display_name: str
    duct_type: PhxVentDuctType = field(init=False, default=PhxVentDuctType.SUPPLY)
    vent_unit_id: int
    _segments: Dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def quantity(self) -> int:
        return 1

    @property
    def segments(self) -> List[PhxDuctSegment]:
        return list(self._segments.values())

    @property
    def length_m(self) -> float:
        return sum(_.length for _ in self.segments)

    @property
    def diameter_mm(self) -> float:
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * seg.diameter_mm

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def height_mm(self) -> float:
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * (seg.height_mm or 0.0)

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def width_mm(self) -> float:
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * (seg.width_mm or 0.0)

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def insulation_thickness_mm(self) -> float:
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * seg.insulation_thickness_mm

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def insulation_conductivity_wmk(self) -> float:
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * seg.insulation_conductivity_wmk

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def duct_shape(self) -> int:
        if self.height_mm and self.width_mm:
            return 2  # Rectangular Duct
        else:
            return 1  # Round Duct

    @property
    def is_reflective(self) -> bool:
        return any({seg.insulation_reflective for seg in self.segments})

    @property
    def assigned_vent_unit_ids(self) -> List[int]:
        return [self.vent_unit_id]

    def add_segment(self, _s: PhxDuctSegment) -> None:
        self._segments[_s.identifier] = _s
