# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Water Piping Distribution Objects."""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import math

from ladybug_geometry.geometry3d.polyline import LineSegment3D


@dataclass
class PhxPipeSegment:
    """An individual Pipe Segment."""

    identifier: str
    display_name: str
    geometry: LineSegment3D
    diameter_m: float
    insulation_thickness_m: float
    insulation_conductivity: float # W/mk
    insulation_reflective: bool
    insulation_quality: Any
    daily_period: float

    pipe_wall_thickness_m: float = 0.00225

    @property
    def diameter_mm(self):
        return self.diameter_m * 1000

    @property
    def diameter_inner_m(self) -> float:
        return self.diameter_m
    
    @property
    def diameter_outer_m(self) -> float:
        """Return the outside diameter including the pipe wall thickness."""
        return self.diameter_inner_m + self.pipe_wall_thickness_m
    
    @property
    def diameter_with_insulation_m(self) -> float:
        return self.diameter_outer_m + (2 * self.insulation_thickness_m)

    @property
    def length_m(self) -> float:
        return self.geometry.length

    @property
    def pipe_heat_loss_coefficient(self) -> float:
        """Return the pipe's heat-loss-coefficient (W/mk) considering the diameter and insulation."""
        return self._solve_for_pipe_heat_loss_coeff()

    @property
    def _starting_alpha(self) -> float:
        """Return W/m2k based on insulation reflectivity."""
        if self.insulation_reflective:
            return 5.0
        else:
            return 8.0
        
    def _calc_pipe_heat_loss_coeff(self, _alpha) -> float:
        """Calculate the pipe heat-loss coefficient (W/mk) with a known Alpha (W/m2k) value."""
        _a = self.diameter_outer_m/self.diameter_inner_m
        _b = self.diameter_with_insulation_m/self.diameter_outer_m
        _c = (1 / 2 / 55 * math.log(_a) + 1 / 2 / self.insulation_conductivity * math.log(_b) + 1 / self.diameter_with_insulation_m / _alpha)
        return math.pi / _c

    def _calc_pipe_surface_temp(self, dT, _k) -> float:
        """Return a surface temp (k) for the pipe with a known heat-loss-coefficient (W/mk) value."""
        _a = self.diameter_outer_m/self.diameter_inner_m
        _b = self.diameter_with_insulation_m/self.diameter_outer_m
        _c = (1 / 2 / 55 * math.log(_a) + 1 / 2 / self.insulation_conductivity * math.log(_b))
        return dT - 1 / math.pi * _c * _k * dT

    def _solve_for_pipe_heat_loss_coeff(self, 
                                        _alpha: Optional[float]=None, 
                                        _k1: float=100.0, 
                                        _k2: float=1.0,
                                        _surface_temp: Optional[float]=None) -> float:
        """Return a heat-loss coefficient (W/mk) considering the diameter and insulation.
        
        Approximates the recursive algorithm found in the PHPP "DHW" worksheet.
        """
        TOLERANCE = 0.001
        DELTA_T = 30 # K

        while _k1 - _k2 > TOLERANCE:
            # -- hang onto the old k to test against tolerance later
            _k1 = _k2 

            # -- If W/m2k alpha is not provided (ie: at the start) use the starting-alpha constant
            if not _alpha:
                _alpha = self._starting_alpha
            
            # -- Calc the new K (W/mk), and new surface temp of the pipe
            _k2 = self._calc_pipe_heat_loss_coeff(_alpha)
            _surface_temp = self._calc_pipe_surface_temp(DELTA_T, _k2)

            # -- calc new alpha W/m2k value
            if self.insulation_reflective:
                _n = 0.1
            else:
                _n = 0.85
            _alpha = _n * 4.8 + 1.62 * _surface_temp**0.333

            # -- Run the solver until the k result is < the tolerance
            self._solve_for_pipe_heat_loss_coeff(_alpha, _k1, _k2, _surface_temp)
        
        return _k2


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
    def length_m(self) -> float:
        """Return the total length of all the Pipe Segments."""
        return sum(_.length_m for _ in self.segments) or 1.0

    @property
    def weighted_pipe_heat_loss_coefficient(self):
        """Return a length-weighted total heat loss coefficient (W/mk)"""
        weighted_total = 0.0
        for segment in self.segments:
            weighted_total += segment.pipe_heat_loss_coefficient * segment.length_m
        return weighted_total / self.length_m

    @property
    def weighted_diameter_mm(self):
        """Return a length-weighted total diameter (mm)"""
        weighted_total = 0.0
        for segment in self.segments:
            weighted_total += segment.diameter_mm * segment.length_m
        return weighted_total / self.length_m

    def add_segment(self, _s: PhxPipeSegment) -> None:
        self._segments[_s.identifier] = _s
