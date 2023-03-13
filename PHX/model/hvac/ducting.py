# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Ventilation Ducting Distribution Objects."""


from __future__ import annotations
from typing import Dict, List, Any
from dataclasses import dataclass, field

from ladybug_geometry.geometry3d.polyline import LineSegment3D

@dataclass
class PhxDuctSegment:
    """An individual Duct Segment Segment."""

    identifier: str
    display_name: str
    geometry: LineSegment3D
    diameter: float
    insulation_thickness: float
    insulation_conductivity: float
    insulation_reflective: bool
    insulation_quality: Any
    daily_period: float

    @property
    def length(self) -> float:
        return self.geometry.length
    
@dataclass
class PhxDuctElement:
    """A Duct Element / Run made of one or more PhxDuctSegments."""

    identifier: str
    display_name: str
    _segments: Dict = field(default_factory=dict)

    @property
    def segments(self) -> List[PhxDuctSegment]:
        return list(self._segments.values())

    @property
    def length(self) -> float:
        return sum(_.length for _ in self.segments)

    def add_segment(self, _s: PhxDuctSegment) -> None:
        self._segments[_s.identifier] = _s
