# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Water Piping Distribution Objects."""

from __future__ import annotations
from re import L
from typing import Dict, List, Any
from dataclasses import dataclass, field

from ladybug_geometry.geometry3d.polyline import LineSegment3D


@dataclass
class PhxPipeSegment:
    """An individual Pipe Segment."""

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
class PhxPipeElement:
    """A Pipe Element / Run made of one or more PhxPipeSegments."""

    identifier: str
    display_name: str
    _segments: Dict = field(default_factory=dict)

    @property
    def segments(self) -> List[PhxPipeSegment]:
        return list(self._segments.values())

    @property
    def length(self) -> float:
        return sum(_.length for _ in self.segments)

    def add_segment(self, _s: PhxPipeSegment) -> None:
        self._segments[_s.identifier] = _s
