# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Ventilation Ducting Distribution Objects."""


from __future__ import annotations
from typing import Dict, List, Optional, ClassVar
from dataclasses import dataclass, field

from ladybug_geometry.geometry3d.polyline import LineSegment3D

from PHX.model.enums.hvac import PhxVentDuctType

@dataclass
class PhxDuctSegment:
    """An individual Duct Segment Segment."""

    identifier: str
    display_name: str
    geometry: LineSegment3D
    diameter: float
    height: Optional[float]
    width: Optional[float]
    insulation_thickness: float
    insulation_conductivity: float
    insulation_reflective: bool

    @property
    def length(self) -> float:
        return self.geometry.length
    
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
    def length(self) -> float:
        return sum(_.length for _ in self.segments)

    @property
    def diameter(self) -> float:
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * seg.diameter
        return weighted_total / self.length

    @property
    def height(self) -> float: 
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * (seg.height or 0.0)
        return weighted_total / self.length 
    
    @property
    def width(self) -> float:
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * (seg.width or 0.0)
        return weighted_total / self.length 

    @property
    def insulation_thickness(self) -> float:
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * seg.insulation_thickness
        return weighted_total / self.length
    
    @property
    def insulation_conductivity(self) -> float:
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * seg.insulation_conductivity
        return weighted_total / self.length
    
    @property
    def duct_shape(self) -> int:
        if self.height and self.width:
            return 2 # Rectangular Duct
        else:
            return 1 # Round Duct

    @property
    def is_reflective(self) -> bool:
        return any({seg.insulation_reflective for seg in self.segments})

    @property
    def assigned_vent_unit_ids(self) -> List[int]:
        return [self.vent_unit_id]

    def add_segment(self, _s: PhxDuctSegment) -> None:
        self._segments[_s.identifier] = _s
