# -*- Python Version: 3.10 -*-

"""PHX ventilation duct distribution objects.

Hierarchical ducting model: PhxDuctElement (a duct run) contains one or
more PhxDuctSegment objects, each with geometry, cross-section dimensions,
and insulation properties.
"""


from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from PHX.model.enums.hvac import PhxVentDuctType
from PHX.model.geometry import PhxLineSegment


@dataclass
class PhxDuctSegment:
    """An individual duct segment with geometry, cross-section, and insulation properties.

    Supports both round (diameter only) and rectangular (height + width) cross-sections.

    Attributes:
        identifier (str): Unique segment identifier.
        display_name (str): Human-readable label.
        geometry (PhxLineSegment): 3D line geometry defining the duct run.
        diameter_m (float): Duct diameter for round ducts (m).
        height_m (float | None): Duct height for rectangular ducts (m), or None for round.
        width_m (float | None): Duct width for rectangular ducts (m), or None for round.
        insulation_thickness_m (float): Insulation thickness (m).
        insulation_conductivity_wmk (float): Insulation thermal conductivity (W/mK).
        insulation_reflective (bool): True if insulation has a reflective facing.
    """

    identifier: str
    display_name: str
    geometry: PhxLineSegment
    diameter_m: float
    height_m: float | None
    width_m: float | None
    insulation_thickness_m: float
    insulation_conductivity_wmk: float
    insulation_reflective: bool

    @property
    def length(self) -> float:
        """Segment length derived from the line geometry (m)."""
        return self.geometry.length

    @property
    def diameter_mm(self) -> float:
        """Return the diameter in MM."""
        return self.diameter_m * 1000.0

    @property
    def height_mm(self) -> float | None:
        """Return the height in MM."""
        if self.height_m:
            return self.height_m * 1000.0
        else:
            return None

    @property
    def width_mm(self) -> float | None:
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
    """A duct run composed of one or more PhxDuctSegment objects.

    Aggregate properties (diameter, height, width, insulation) are
    length-weighted averages across all segments.

    Attributes:
        id_num (int): Auto-incrementing instance number.
        identifier (str): Unique duct element identifier.
        display_name (str): Human-readable label.
        duct_type (PhxVentDuctType): Supply or exhaust classification. Default: SUPPLY.
        vent_unit_id (int): ID of the ventilation unit this duct serves.
    """

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)

    identifier: str
    display_name: str
    duct_type: PhxVentDuctType = field(init=False, default=PhxVentDuctType.SUPPLY)
    vent_unit_id: int
    _segments: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def quantity(self) -> int:
        """Always 1 for a single duct element."""
        return 1

    @property
    def segments(self) -> list[PhxDuctSegment]:
        """All duct segments in this element."""
        return list(self._segments.values())

    @property
    def length_m(self) -> float:
        """Total duct length across all segments (m)."""
        return sum(_.length for _ in self.segments)

    @property
    def diameter_mm(self) -> float:
        """Length-weighted average diameter across all segments (mm)."""
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * seg.diameter_mm

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def height_mm(self) -> float:
        """Length-weighted average height for rectangular ducts (mm). 0.0 if round."""
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * (seg.height_mm or 0.0)

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def width_mm(self) -> float:
        """Length-weighted average width for rectangular ducts (mm). 0.0 if round."""
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * (seg.width_mm or 0.0)

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def insulation_thickness_mm(self) -> float:
        """Length-weighted average insulation thickness (mm)."""
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * seg.insulation_thickness_mm

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def insulation_conductivity_wmk(self) -> float:
        """Length-weighted average insulation conductivity (W/mK)."""
        weighted_total = 0.0
        for seg in self.segments:
            weighted_total += seg.length * seg.insulation_conductivity_wmk

        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def duct_shape(self) -> int:
        """Return 1 for round duct, 2 for rectangular duct."""
        if self.height_mm and self.width_mm:
            return 2  # Rectangular Duct
        else:
            return 1  # Round Duct

    @property
    def is_reflective(self) -> bool:
        """True if any segment has reflective insulation facing."""
        return any(seg.insulation_reflective for seg in self.segments)

    @property
    def assigned_vent_unit_ids(self) -> list[int]:
        """List of ventilation unit IDs this duct element is assigned to."""
        return [self.vent_unit_id]

    def add_segment(self, _s: PhxDuctSegment) -> None:
        """Add a duct segment to this element.

        Arguments:
        ----------
            * _s (PhxDuctSegment): The duct segment to add.
        """
        self._segments[_s.identifier] = _s
