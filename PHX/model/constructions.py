# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Construction, Materials Classes"""

from __future__ import annotations
from typing import ClassVar, Union, List, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class PhxMaterial:
    display_name: str = ""
    conductivity: float = 0.0
    density: float = 0.0
    porosity: float = 0.0
    heat_capacity: float = 0.0
    water_vapor_resistance: float = 0.0
    reference_water: float = 0.0
    percentage_of_assembly: float = 1.0


@dataclass
class PhxLayer:
    thickness_m: float = 0.0
    materials: List[PhxMaterial] = field(default_factory=list)

    @property
    def material(self) -> PhxMaterial:
        """Return the first PhxMaterial from the self.materials collection."""
        if not self.materials:
            # -- Return a default PhxMaterial if no materials are set.
            return PhxMaterial()
        else:
            # -- Otherwise return the first material in the collection.
            return self.materials[0]

    def add_material(self, _material: PhxMaterial) -> None:
        self.materials.append(_material)

    @property
    def thickness_mm(self):
        """Returns the thickness of the layer in MM"""
        return self.thickness_m * 1000

    @classmethod
    def from_total_u_value(cls, _total_u_value: float) -> PhxLayer:
        """Returns a new PhxLayer with a single material with the given U-Value.
        note that this will assign a default thickness of 1m to the layer.
        """
        obj = cls()
        obj.thickness_m = 1

        new_mat = PhxMaterial()
        new_mat.conductivity = obj.thickness_m * _total_u_value
        new_mat.display_name = "Material"
        obj.materials.append(new_mat)

        return obj


@dataclass
class PhxConstructionOpaque:
    _count: ClassVar[int] = 0

    _identifier: Union[uuid.UUID, str] = field(init=False, default_factory=uuid.uuid4)
    id_num: int = field(init=False, default=0)
    display_name: str = ""
    layer_order: int = 2  # Outside to Inside
    grid_kind: int = 2  # Medium
    layers: list[PhxLayer] = field(default_factory=list)

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

    @classmethod
    def from_total_u_value(
        cls, _total_u_value: float, _display_name: str = ""
    ) -> PhxConstructionOpaque:
        """Returns a new PhxConstructionOpaque with a single layer with the given U-Value."""
        obj = cls()
        obj.display_name = _display_name or f"U-Value: {_total_u_value}"
        obj.layers.append(PhxLayer.from_total_u_value(_total_u_value))
        return obj


# ------------------------------------------------------------
# Windows


@dataclass
class PhxWindowFrameElement:
    width: float = 0.1  # m
    u_value: float = 1.0  # W/m2k
    psi_glazing: float = 0.00  # W/mk
    psi_install: float = 0.00  # W/mk

    @classmethod
    def from_total_u_value(cls, _total_u_value: float) -> PhxWindowFrameElement:
        """Returns a new PhxWindowFrameElement with u-values set to a single value."""
        obj = cls()
        obj.width = 0.1  # m
        obj.u_value = _total_u_value
        obj.psi_glazing = 0.0
        obj.psi_install = 0.0
        return obj


@dataclass
class PhxConstructionWindow:
    _count: ClassVar[int] = 0
    id_num: int = field(init=False, default=0)
    _identifier: Union[uuid.UUID, str] = field(init=False, default_factory=uuid.uuid4)
    display_name: str = ""
    _glazing_type_display_name: str = ""
    _frame_type_display_name: str = ""

    use_detailed_uw: bool = True
    use_detailed_frame: bool = True

    u_value_window: float = 1.0
    u_value_glass: float = 1.0
    u_value_frame: float = 1.0

    frame_top: PhxWindowFrameElement = field(default_factory=PhxWindowFrameElement)
    frame_right: PhxWindowFrameElement = field(default_factory=PhxWindowFrameElement)
    frame_bottom: PhxWindowFrameElement = field(default_factory=PhxWindowFrameElement)
    frame_left: PhxWindowFrameElement = field(default_factory=PhxWindowFrameElement)
    frame_factor: float = 0.75

    glass_mean_emissivity: float = 0.1
    glass_g_value: float = 0.4

    id_num_shade: int = -1

    def __post_init__(self) -> None:
        self.__class__._count += 1
        self.id_num = self.__class__._count

    @property
    def glazing_type_display_name(self) -> str:
        return self._glazing_type_display_name or self.display_name

    @glazing_type_display_name.setter
    def glazing_type_display_name(self, _in: str) -> None:
        self._glazing_type_display_name = _in

    @property
    def frame_type_display_name(self) -> str:
        return self._frame_type_display_name or self.display_name

    @frame_type_display_name.setter
    def frame_type_display_name(self, _in: str) -> None:
        self._frame_type_display_name = _in

    @property
    def identifier(self) -> str:
        return str(self._identifier)

    @identifier.setter
    def identifier(self, _in: str):
        if not _in:
            return
        self._identifier = str(_in)

    @classmethod
    def from_total_u_value(
        cls, _total_u_value: float, _g_value: float = 0.4, _display_name: str = ""
    ) -> PhxConstructionWindow:
        """Returns a new PhxConstructionWindow with all u-values set to a single value."""
        obj = cls()
        obj.display_name = _display_name or f"U-Value: {_total_u_value}"
        obj.frame_type_display_name = _display_name or f"U-Value: {_total_u_value}"
        obj.glazing_type_display_name = _display_name or f"U-Value: {_total_u_value}"

        obj.u_value_window = _total_u_value
        obj.u_value_glass = _total_u_value
        obj.u_value_frame = _total_u_value

        obj.glass_g_value = _g_value

        obj.frame_top = PhxWindowFrameElement.from_total_u_value(_total_u_value)
        obj.frame_right = PhxWindowFrameElement.from_total_u_value(_total_u_value)
        obj.frame_bottom = PhxWindowFrameElement.from_total_u_value(_total_u_value)
        obj.frame_left = PhxWindowFrameElement.from_total_u_value(_total_u_value)

        return obj
