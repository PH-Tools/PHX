# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Water Piping Distribution Objects."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional, Union
from uuid import uuid4

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.polyline import LineSegment3D
from ph_units.converter import convert

from PHX.model.enums.hvac import (
    PhxHotWaterPipingCalcMethod,
    PhxHotWaterPipingInchDiameterType,
    PhxHotWaterPipingMaterial,
    PhxHotWaterSelectionUnitsOrFloors,
)


@dataclass
class PhxRecirculationParameters:
    calc_method: PhxHotWaterPipingCalcMethod = field(default=PhxHotWaterPipingCalcMethod.HOT_WATER_PIPING_FLOOR_METHOD)
    pipe_material: PhxHotWaterPipingMaterial = field(default=PhxHotWaterPipingMaterial.COPPER_L)
    demand_recirc: bool = True
    num_bathrooms: int = 1
    hot_water_fixtures: int = 1
    all_pipes_insulated: bool = True
    units_or_floors: PhxHotWaterSelectionUnitsOrFloors = field(
        default=PhxHotWaterSelectionUnitsOrFloors.USER_DETERMINED
    )
    pipe_diameter: float = 25.4  # MM - For simplified method only
    air_temp: float = 20.0  # Deg C
    water_temp: float = 60.0  # Deg C
    daily_recirc_hours: float = 0.0


@dataclass
class PhxPipeSegment:
    """An individual Pipe Segment."""

    identifier: str
    display_name: str
    geometry: LineSegment3D
    pipe_material: PhxHotWaterPipingMaterial
    diameter_m: float
    insulation_thickness_m: float
    insulation_conductivity: float  # W/mk
    insulation_reflective: bool
    insulation_quality: Any
    daily_period: float
    water_temp_c: float = 60.0
    pipe_wall_thickness_m: float = 0.00225

    @property
    def diameter_mm(self) -> float:
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

    def _calc_pipe_heat_loss_coeff(self, _alpha: float, _conductivity: Optional[float] = None) -> float:
        """Calculate the pipe heat-loss coefficient (W/mk) with a known Alpha (W/m2k) value."""

        # -- Allow for 'reverse' solver....
        conductivity = _conductivity or self.insulation_conductivity

        _a = self.diameter_outer_m / self.diameter_inner_m
        _b = self.diameter_with_insulation_m / self.diameter_outer_m
        _c = (
            1 / 2 / 55 * math.log(_a)
            + 1 / 2 / conductivity * math.log(_b)
            + 1 / self.diameter_with_insulation_m / _alpha
        )
        return math.pi / _c

    def _calc_pipe_surface_temp(self, dT, _k, _conductivity: Optional[float] = None) -> float:
        """Return a surface temp (k) for the pipe with a known heat-loss-coefficient (W/mk) value."""

        # -- Allow for 'reverse' solver....
        conductivity = _conductivity or self.insulation_conductivity

        _a = self.diameter_outer_m / self.diameter_inner_m
        _b = self.diameter_with_insulation_m / self.diameter_outer_m
        _c = 1 / 2 / 55 * math.log(_a) + 1 / 2 / conductivity * math.log(_b)
        return dT - 1 / math.pi * _c * _k * dT

    def _solve_for_pipe_heat_loss_coeff(
        self,
        _alpha: Optional[float] = None,
        _k1: float = 100.0,
        _k2: float = 1.0,
        _surface_temp: Optional[float] = None,
    ) -> float:
        """Return a heat-loss coefficient (W/mk) considering the diameter and insulation.

        Approximates the recursive algorithm found in the PHPP "DHW" worksheet.
        """
        TOLERANCE = 0.001
        DELTA_T = 30  # K
        if self.insulation_reflective:
            N = 0.1
        else:
            N = 0.85

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
            _alpha = N * 4.8 + 1.62 * _surface_temp**0.333

            # -- Run the solver until the k result is < the tolerance
            self._solve_for_pipe_heat_loss_coeff(_alpha, _k1, _k2, _surface_temp)

        return _k2

    def reverse_solve_for_insulation_conductivity(
        self,
        target_result: float,
        starting_conductivity: float,
    ) -> float:
        """Return an insulation conductivity (W/mk) when given a known heat-loss-coeff (W/MK).

        Be sure to set the known (or assumed) pipe-diameter and insulation-thickness of the Segment before trying to solve.
        """
        TOLERANCE_A = 0.001
        TOLERANCE_B = 0.01
        DELTA_T = 30  # K

        if self.insulation_reflective:
            N = 0.1
        else:
            N = 0.85

        conductivity = starting_conductivity

        while True:
            alpha = 5.0  # Assuming a known starting value for _alpha
            k1 = 2.0  # Assuming a high initial value for _k1
            k2 = 0.01  # Assuming a low initial value for _k2
            surface_temp = None  # Placeholder for surface temp

            # -- Use the values and calc the heat-loss-coefficient...
            while k1 - k2 > TOLERANCE_A:
                k1 = k2
                k2 = self._calc_pipe_heat_loss_coeff(alpha, conductivity)
                surface_temp = self._calc_pipe_surface_temp(DELTA_T, k2, conductivity)
                alpha = N * 4.8 + 1.62 * surface_temp**0.333

            if abs(k2 - target_result) < TOLERANCE_B:
                return conductivity

            # Adjust conductivity for the next iteration
            STEP = 0.001  # You can adjust the step size as needed
            conductivity -= STEP

    @classmethod
    def from_length(
        cls,
        display_name: str,
        length_m: float,
        pipe_material: PhxHotWaterPipingMaterial,
        pipe_diameter_m: float,
    ) -> "PhxPipeSegment":
        """Create a Pipe Segment from a length value (m)."""
        _l: int = length_m  # type: ignore # untyped LBT

        return cls(
            identifier=str(uuid4()),
            display_name=display_name,
            geometry=LineSegment3D(Point3D(0, 0, 0), Vector3D(_l, 0, 0)),
            pipe_material=pipe_material,
            diameter_m=pipe_diameter_m,
            insulation_thickness_m=0.0,
            insulation_conductivity=0.0,
            insulation_reflective=False,
            insulation_quality=None,
            daily_period=24,
        )


@dataclass
class PhxPipeElement:
    """A Pipe Element / Run made of one or more PhxPipeSegments."""

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    identifier: str = field(default_factory=lambda: str(uuid4()))
    display_name: str = "_unnamed_pipe_element_"
    _segments: Dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        PhxPipeElement._count += 1
        self.id_num = PhxPipeElement._count

    @property
    def segments(self) -> List[PhxPipeSegment]:
        return list(self._segments.values())

    @property
    def length_m(self) -> float:
        """Return the total length of all the Pipe Segments."""
        return sum(_.length_m for _ in self.segments)

    @property
    def weighted_pipe_heat_loss_coefficient(self) -> float:
        """Return a length-weighted total heat loss coefficient (W/mk)"""
        weighted_total = 0.0
        for segment in self.segments:
            weighted_total += segment.pipe_heat_loss_coefficient * segment.length_m
        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def weighted_diameter_mm(self) -> float:
        """Return a length-weighted total diameter (mm)"""
        weighted_total = 0.0
        for segment in self.segments:
            weighted_total += segment.diameter_mm * segment.length_m
        try:
            return weighted_total / self.length_m
        except ZeroDivisionError:
            return 0.0

    @property
    def material(self) -> PhxHotWaterPipingMaterial:
        if not self.segments:
            return PhxHotWaterPipingMaterial.COPPER_K

        materials = list({s.pipe_material for s in self.segments})
        if len(materials) != 1:
            raise ValueError(
                "Error: Pipe Element '{}' has multiple materials: '{}'."
                "Please rebuild the pipe with a single material. {}".format(self.display_name, materials, self.segments)
            )
        else:
            return materials[0]

    @property
    def demand_recirculation(self) -> bool:
        return False

    def add_segment(self, _s: PhxPipeSegment) -> None:
        self._segments[_s.identifier] = _s


@dataclass
class PhxPipeBranch:
    """A Pipe Branch made of one or more Fixture-pipes (PhxPipeElement)."""

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    identifier: str = field(default_factory=lambda: str(uuid4()))
    display_name: str = "_unnamed_pipe_branch_"
    pipe_element: PhxPipeElement = field(default_factory=PhxPipeElement)
    fixtures: List[PhxPipeElement] = field(default_factory=list)

    def __post_init__(self) -> None:
        PhxPipeBranch._count += 1
        self.id_num = PhxPipeBranch._count

    def add_fixture(self, _f: PhxPipeElement) -> None:
        self.fixtures.append(_f)


@dataclass
class PhxPipeTrunk:
    """A Pipe Trunk made of one or more Pipe Branches (PhxPipeBranch)."""

    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    identifier: str = field(default_factory=lambda: str(uuid4()))
    display_name: str = "_unnamed_pipe_trunk_"
    multiplier: int = 1
    pipe_element: PhxPipeElement = field(default_factory=PhxPipeElement)
    branches: List[PhxPipeBranch] = field(default_factory=list)

    def __post_init__(self) -> None:
        PhxPipeTrunk._count += 1
        self.id_num = PhxPipeTrunk._count

    def add_branch(self, _b: PhxPipeBranch) -> None:
        self.branches.append(_b)


# -- Type Alias
AnyPhxPiping = Union[PhxPipeElement, PhxPipeBranch, PhxPipeTrunk]
