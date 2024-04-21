# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Component (Face, Aperture) Classes"""

from __future__ import annotations

from typing import ClassVar, Collection, List, Optional, Set, Tuple, Union

from PHX.model import constructions, geometry
from PHX.model.enums.building import (
    ComponentColor,
    ComponentExposureExterior,
    ComponentFaceOpacity,
    ComponentFaceType,
    ThermalBridgeType,
)


class PhxComponentBase:
    """Base class with id_num counter for Opaque and Aperture Components"""

    _count: ClassVar[int] = 0

    def __init__(self):
        PhxComponentBase._count += 1
        self._id_num: int = PhxComponentBase._count

    @property
    def id_num(self) -> int:
        return self._id_num

    def __str__(self):
        return f"{self.__class__.__name__}(id_num={self.id_num})"


class PhxComponentOpaque(PhxComponentBase):
    """Opaque surface components (wall, roof, floor)."""

    def __init__(self):
        super().__init__()

        self.display_name: str = ""
        self.face_type: ComponentFaceType = ComponentFaceType.WALL
        self.face_opacity: ComponentFaceOpacity = ComponentFaceOpacity.OPAQUE
        self.color_interior: ComponentColor = ComponentColor.EXT_WALL_INNER
        self.color_exterior: ComponentColor = ComponentColor.EXT_WALL_INNER
        self.exposure_exterior: ComponentExposureExterior = ComponentExposureExterior.EXTERIOR
        self.exposure_interior: int = 1
        self.interior_attachment_id: int = -1

        self.assembly: constructions.PhxConstructionOpaque = constructions.PhxConstructionOpaque()
        self.assembly_type_id_num: int = -1

        self.apertures: List[PhxComponentAperture] = []
        self.polygons: List[geometry.PhxPolygon] = []

    def __eq__(self, other: PhxComponentOpaque) -> bool:
        if (
            self.display_name != other.display_name
            or self.face_type != other.face_type
            or self.face_opacity != other.face_opacity
            or self.color_interior != other.color_interior
            or self.color_exterior != other.color_exterior
            or self.exposure_exterior != other.exposure_exterior
            or self.exposure_interior != other.exposure_interior
            or self.interior_attachment_id != other.interior_attachment_id
            or self.assembly_type_id_num != other.assembly_type_id_num
        ):
            return False

        # -- check the apertures
        if len(self.apertures) != len(other.apertures):
            return False
        for this_ap in self.apertures:
            if not any((this_ap == other_ap for other_ap in other.apertures)):
                return False

        # -- check the polygons
        if len(self.polygons) != len(other.polygons):
            return False
        for this_poly in self.polygons:
            if not any((this_poly == other_poly for other_poly in other.polygons)):
                return False

        return True

    @property
    def u_value(self) -> float:
        return self.assembly.u_value

    @property
    def polygon_ids(self) -> Set[int]:
        """Return a Set of all the Polygon-id numbers found in the Component's Polygon group."""
        return {polygon.id_num for polygon in self.polygons}

    @property
    def unique_key(self) -> str:
        """Returns a unique text key,. Useful for sorting / grouping / merging components."""
        return (
            f"{self.face_type.value}-{self.face_opacity.value}-{self.exposure_interior}-{self.interior_attachment_id}-"
            f"{self.exposure_exterior.value}-{self.assembly_type_id_num}"
        )

    @property
    def is_shade(self) -> bool:
        if self.face_opacity != ComponentFaceOpacity.OPAQUE:
            return False
        if self.exposure_interior != -1:
            return False
        return True

    @property
    def is_above_grade_wall(self) -> bool:
        if self.face_type != ComponentFaceType.WALL:
            return False
        if self.exposure_exterior != ComponentExposureExterior.EXTERIOR:
            return False
        return True

    @property
    def is_below_grade_wall(self) -> bool:
        if self.face_type != ComponentFaceType.WALL:
            return False
        if self.exposure_exterior != ComponentExposureExterior.GROUND:
            return False
        return True

    @property
    def is_above_grade_floor(self) -> bool:
        if self.face_type != ComponentFaceType.FLOOR:
            return False
        if self.exposure_exterior != ComponentExposureExterior.EXTERIOR:
            return False
        return True

    @property
    def is_below_grade_floor(self) -> bool:
        if self.face_type != ComponentFaceType.FLOOR:
            return False
        if self.exposure_exterior != ComponentExposureExterior.GROUND:
            return False
        return True

    @property
    def is_roof(self) -> bool:
        if self.face_type != ComponentFaceType.ROOF_CEILING:
            return False
        return True

    def add_polygons(self, _input: Union[Collection[geometry.PhxPolygon], geometry.PhxPolygon]) -> None:
        """Adds a new Polygon or Polygons to the Component's collection.

        Arguments:
        ----------
            * _input (Union[Collection[geometry.PhxPolygon], geometry.PhxPolygon]): The polygon or
                polygons to add to the component's collection.

        Returns:
        --------
            * None
        """
        if not isinstance(_input, Collection):
            _input = (_input,)

        for polygon in _input:
            self.polygons.append(polygon)

    @property
    def aperture_ids(self) -> Set[int]:
        """Return a Set of all the Aperture-id numbers found in the Component's Aperture group."""
        return {aperture.id_num for aperture in self.apertures}

    @property
    def aperture_elements(self) -> List[PhxApertureElement]:
        """Return a list of all the Aperture Elements found in the Component's Aperture group."""
        return [element for aperture in self.apertures for element in aperture.elements]

    def __add__(self, other: PhxComponentOpaque) -> PhxComponentOpaque:
        """Merge with another Component into a single new Component.

        Arguments:
        ----------
            * other (PhxComponentOpaque): The other PhxComponentOpaque to merge with.

        Returns:
        --------
            * (PhxComponentOpaque): A new Component with attributes merged.
        """
        new_compo = self.__class__()
        for attr_name, attr_val in vars(self).items():
            if attr_name.startswith("_"):
                continue
            setattr(new_compo, attr_name, attr_val)

        new_compo.display_name = f"{self.face_type.name} [{self.assembly.display_name}]"
        new_compo.polygons = self.polygons + other.polygons
        for phx_aperture in new_compo.apertures:
            phx_aperture.host = new_compo
        for phx_aperture in other.apertures:
            new_compo.add_aperture(phx_aperture)

        return new_compo

    def add_aperture(self, _aperture: PhxComponentAperture) -> None:
        """Add a new child PhxComponentAperture to the Component.

        Arguments:
        ----------
            * _aperture: (PhxComponentAperture): The new PhxComponentAperture to
                add as a child.
        Returns:
        --------
            * None
        """
        if _aperture.id_num not in self.aperture_ids:
            _aperture.host = self
            self.apertures.append(_aperture)

    def get_host_polygon_by_child_id_num(self, _id_num: int) -> geometry.PhxPolygon:
        """Return a single Polygon from the collection if it has the specified ID as a 'child'.

        If the specified ID number is not found, an Exception is raised.

        Arguments:
        ----------
            * _id_num: (int) The Polygon id-number to search the Component's collection for.
        Returns:
        -------
            * (PhxPolygon): The PhxPolygon with the specified id-number.
        """
        for polygon in self.polygons:
            if _id_num in polygon.child_polygon_ids:
                return polygon
        raise Exception(f"Error: Cannot find a host polygon for the child id_num: {_id_num}")

    def get_aperture_polygon_by_id_num(self, _id_num: int) -> geometry.PhxPolygon:
        """Return a single Polygon from the collection if it has the specified ID as a 'child'.

        If the specified ID number is not found, an Exception is raised.

        Arguments:
        ----------
            * _id_num: (int) The Polygon id-number to search the Component's collection for.
        Returns:
        -------
            * (PhxPolygon): The PhxPolygon with the specified id-number.
        """
        for aperture in self.apertures:
            for polygon in aperture.polygons:
                if polygon.id_num == _id_num:
                    return polygon
        raise Exception(f"Error: Cannot find an aperture polygon for the id_num: {_id_num}")

    def get_aperture_element_by_polygon_id_num(self, _id_num: int) -> PhxApertureElement:
        """Return a single Aperture Element from the collection if it has the specified ID.

        If the specified ID number is not found, an Exception is raised.

        Arguments:
        ----------
            * _id_num: (int) The Polygon id-number to search the Component's collection for.
        Returns:
        -------
            * (PhxApertureElement): The PhxApertureElement with the specified id-number.
        """
        for aperture in self.apertures:
            for element in aperture.elements:
                if not element.polygon:
                    continue

                if element.polygon.id_num == _id_num:
                    return element
        raise Exception(f"Error: Cannot find an aperture element for the id_num: {_id_num}")

    def set_assembly_type(self, _phx_construction: constructions.PhxConstructionOpaque):
        """Set the Assembly Type for the Component.

        Arguments:
        ----------
            * _phx_construction (constructions.PhxConstructionOpaque): The Construction to
                set as the Assembly Type.
        Returns:
        --------
            * None
        """
        self.assembly = _phx_construction
        self.assembly_type_id_num = _phx_construction.id_num

    def get_total_gross_component_area(self) -> float:
        """Return the total Gross wall area of the Component (ignoring any nested apertures)."""
        return sum([polygon.area for polygon in self.polygons])

    def get_total_aperture_area(self) -> float:
        """Return the total Gross aperture area of the Component."""
        return sum([aperture.get_total_aperture_area() for aperture in self.apertures])

    def get_total_net_component_area(self) -> float:
        """Return the total net area of the Component (gross - apertures)."""
        return self.get_total_gross_component_area() - self.get_total_aperture_area()


class PhxApertureShadingDimensions(PhxComponentBase):
    """PHPP old-style shading dimensions data.

    ### Horizon Objects:
    - d_hori = Distance away from glass
    - h_hori = Height of the shading from glass bottom edge

    ### Shading to the sides (reveal):
    - d_reveal = Reveal distance 'over' from glass
    - o_reveal = Reveal depth from glass

    ### Overhand Shading:
    - d_over = Overhang height 'up' from glass top edge
    - o_over = Overhang depth from glass
    """

    def __init__(self) -> None:
        super().__init__()

        # -- Horizon Objects
        self.d_hori: Optional[float] = None  # Vertical distance to the shading top
        self.h_hori: Optional[float] = None  # Horizontal distance to the shading

        # -- Shading to the sides (reveal)
        self.d_reveal: Optional[float] = None  # Reveal distance 'over' from glass
        self.o_reveal: Optional[float] = None  # Reveal depth from glass

        # -- Overhand Shading
        self.d_over: Optional[float] = None  # Overhang height 'up' from glass
        self.o_over: Optional[float] = None  # Overhang Depth from glass


class PhxApertureElement(PhxComponentBase):
    """A single sash / element of an Aperture Component."""

    def __init__(self, _host: PhxComponentAperture):
        super().__init__()

        self.host: PhxComponentAperture = _host
        self.display_name: str = ""
        self.polygon: Union[geometry.PhxPolygonRectangular, geometry.PhxPolygon, None] = None
        self.winter_shading_factor: float = 0.75
        self.summer_shading_factor: float = 0.75
        self.shading_dimensions = PhxApertureShadingDimensions()

    @property
    def area(self) -> float:
        """Return the area of the element's polygon."""
        if self.polygon is None:
            return 0.0
        return self.polygon.area

    @property
    def width(self) -> float:
        if not self.polygon:
            return 0.0

        try:
            return self.polygon.width  # type: ignore
        except AttributeError:
            return self.polygon.perimeter_length() / 4

    @property
    def height(self) -> float:
        if not self.polygon:
            return 0.0

        try:
            return self.polygon.height  # type: ignore
        except AttributeError:
            return self.polygon.perimeter_length() / 4

    @property
    def frame_area(self) -> float:
        """Return the area of the frame in the Aperture Element."""
        if not self.polygon:
            return 1.0

        # -- Get the frame widths
        window_type = self.host.window_type
        frame_w_top = window_type.frame_top.width
        frame_w_bottom = window_type.frame_bottom.width
        frame_w_left = window_type.frame_left.width
        frame_w_right = window_type.frame_right.width

        # -- Get the frame lengths (remove the top/bottom frame width from the sides)
        frame_l_top = self.width
        frame_l_bottom = self.width
        frame_l_left = self.height - self.height / self.height * (frame_w_top + frame_w_bottom)
        frame_l_right = self.height - self.height / self.height * (frame_w_top + frame_w_bottom)
        # -- Calc. the frame area
        frame_area = (
            +(frame_l_top * frame_w_top)
            + (frame_l_bottom * frame_w_bottom)
            + (frame_l_left * frame_w_left)
            + (frame_l_right * frame_w_right)
        )

        return frame_area

    @property
    def frame_factor(self) -> float:
        """Return the % of the Aperture Element which is frame (as opposed to glazing)."""
        try:
            return self.frame_area / self.area
        except ZeroDivisionError:
            return 0.0

    @property
    def glazing_area(self) -> float:
        """Return the area of the glazing in the Aperture Element."""
        return self.area * self.glazing_factor

    @property
    def glazing_factor(self) -> float:
        """Return the % of the Aperture Element which is glazing (as opposed to frame)."""
        return 1 - self.frame_factor

    def is_equivalent(self, other: PhxApertureElement) -> bool:
        """Return True if the two elements are equivalent."""
        TOLERANCE = 0.001
        if (
            abs(self.winter_shading_factor - other.winter_shading_factor) > TOLERANCE
            or abs(self.summer_shading_factor - other.summer_shading_factor) > TOLERANCE
        ):
            return False

        if self.polygon != other.polygon:
            return False

        return True

    def scale(self, _scale_factor: float) -> None:
        """Scale the element's polygon by the specified factor."""
        if self.polygon:
            self.polygon.scale(_scale_factor)


class PhxComponentAperture(PhxComponentBase):
    """An Aperture (window, door) component with one or more 'element' (sash)."""

    def __init__(self, _host: PhxComponentOpaque) -> None:
        super().__init__()

        self.host = _host

        self.display_name: str = ""
        self.face_type: ComponentFaceType = ComponentFaceType.WINDOW
        self.face_opacity: ComponentFaceOpacity = ComponentFaceOpacity.TRANSPARENT
        self.color_interior: ComponentColor = ComponentColor.WINDOW
        self.color_exterior: ComponentColor = ComponentColor.WINDOW
        self.exposure_interior: int = 1
        self.exposure_exterior: ComponentExposureExterior = ComponentExposureExterior.EXTERIOR
        self.interior_attachment_id: int = -1

        self.window_type: constructions.PhxConstructionWindow = constructions.PhxConstructionWindow()

        self.variant_type_name: str = "_unnamed_type_"
        self._install_depth: float = 0.1016  # m
        self._default_monthly_shading_correction_factor: float = 0.5

        self.elements: List[PhxApertureElement] = []

    @property
    def install_depth(self) -> float:
        """Return the installation depth of the Aperture."""
        return self._install_depth

    @install_depth.setter
    def install_depth(self, _depth: Optional[float]) -> None:
        """Set the installation depth of the Aperture."""
        if _depth != None:
            self._install_depth = _depth

    @property
    def average_shading_d_reveal(self) -> Optional[float]:
        """The average shading 'reveal' distance of the Aperture's Elements from the glass."""
        if not all(e.shading_dimensions.d_reveal for e in self.elements):
            return None

        try:
            total_d_reveal = sum(e.shading_dimensions.d_reveal or 0.0 for e in self.elements)
            return total_d_reveal / len(self.elements)
        except ZeroDivisionError:
            return 0.0

    @property
    def default_monthly_shading_correction_factor(self) -> float:
        """Return the default monthly shading correction factor."""
        return self._default_monthly_shading_correction_factor

    @default_monthly_shading_correction_factor.setter
    def default_monthly_shading_correction_factor(self, _factor: Optional[float]) -> None:
        """Set the default monthly shading correction factor."""
        if _factor != None:
            self._default_monthly_shading_correction_factor = _factor

    @property
    def shade_type_id_num(self) -> int:
        """Return the ID-Number of the Component Construction's Shade-Type, or -1 if None."""
        return self.window_type._id_num_shade

    @property
    def window_type_id_num(self) -> int:
        return self.window_type.id_num

    @property
    def polygons(
        self,
    ) -> List[Union[geometry.PhxPolygonRectangular, geometry.PhxPolygon]]:
        return [e.polygon for e in self.elements if e.polygon]

    @property
    def polygon_ids(self) -> Set[int]:
        """Return a Set of all the Polygon-id numbers found in the Component's Polygon group."""
        return {polygon.id_num for polygon in self.polygons}

    @property
    def polygon_ids_sorted(self) -> Tuple[int, ...]:
        """Return a Tuple of all the Polygon-id numbers found in the Component's Polygon group, sorted."""
        return tuple(sorted(self.polygon_ids))

    @property
    def unique_key(self) -> str:
        """Returns a unique text key,. Useful for sorting / grouping / merging components."""
        attributes = {
            "face_type": self.face_type.value,
            "face_opacity": self.face_opacity.value,
            "exposure_interior": self.exposure_interior,
            "interior_attachment_id": self.interior_attachment_id,
            "exposure_exterior": self.exposure_exterior.value,
            "window_type_id_num": self.window_type_id_num,
            "shade_type_id_num": self.shade_type_id_num,
            "variant_type_name": self.variant_type_name,
            "default_monthly_shading_correction_factor": self.default_monthly_shading_correction_factor,
        }
        return "-".join(f"{v}" for k, v in attributes.items())

    def add_elements(self, _elements: Collection[PhxApertureElement]) -> None:
        """Add one or more new 'Elements' (Sashes) to the Aperture"""
        for element in _elements:
            self.elements.append(element)

    def add_element(self, _element: PhxApertureElement) -> None:
        """Add a new 'Element' (Sash) to the Aperture"""
        self.elements.append(_element)

    def set_window_type(self, _window_type: constructions.PhxConstructionWindow) -> None:
        """Set the Component's Window Type."""
        self.window_type = _window_type

    def __add__(self, other: PhxComponentAperture) -> PhxComponentAperture:
        """Merge with another Component into a single new Component.

        Arguments:
        ----------
            * other (PhxComponentAperture): The other PhxComponentAperture to merge with.

        Returns:
        --------
            * (PhxComponentAperture): A new Component with attributes merged.
        """
        new_compo = self.__class__(_host=self.host)

        # -- Copy the basic attribute values over
        for attr_name, attr_val in vars(self).items():
            if attr_name.startswith("_"):
                continue  # Ignore private attributes
            setattr(new_compo, attr_name, attr_val)

        # -- Get the Properties as well
        new_compo.install_depth = self.install_depth
        new_compo.default_monthly_shading_correction_factor = self.default_monthly_shading_correction_factor

        if self.window_type.display_name == other.window_type.display_name:
            new_compo.display_name = self.window_type.display_name
        else:
            new_compo.display_name = "Merged_Aperture_Component"

        new_compo.elements = self.elements + other.elements
        for element in new_compo.elements:
            element.host = new_compo

        return new_compo

    def __eq__(self, other: PhxComponentAperture) -> bool:
        if (
            self.display_name != other.display_name
            or self.face_type != other.face_type
            or self.face_opacity != other.face_opacity
            or self.color_interior != other.color_interior
            or self.color_exterior != other.color_exterior
            or self.exposure_exterior != other.exposure_exterior
            or self.exposure_interior != other.exposure_interior
            or self.interior_attachment_id != other.interior_attachment_id
            or self.window_type_id_num != other.window_type_id_num
            or self.variant_type_name != other.variant_type_name
            or abs(self.install_depth - other.install_depth) > 0.001
            or abs(self.default_monthly_shading_correction_factor - other.default_monthly_shading_correction_factor)
            > 0.001
        ):
            return False

        # -- check the elements
        if len(self.elements) != len(other.elements):
            return False
        for this_el in self.elements:
            if not any((this_el.is_equivalent(other_el) for other_el in other.elements)):
                return False

        # -- check the polygons
        if len(self.polygons) != len(other.polygons):
            return False
        for this_poly in self.polygons:
            if not any((this_poly == other_poly for other_poly in other.polygons)):
                return False

        return True

    def get_total_aperture_area(self) -> float:
        """Return the total Window Area of the Component."""
        return sum([polygon.area for polygon in self.polygons])

    def scale(self, _scale_factor: float = 1.0) -> None:
        """Scale the Component's size by the given factor."""
        for element in self.elements:
            element.scale(_scale_factor)


class PhxComponentThermalBridge(PhxComponentBase):
    """A single Thermal Bridge Element."""

    def __init__(self):
        super().__init__()

        self._identifier: Optional[str] = ""
        self._quantity: Optional[float] = 0.0
        self._group_type: Optional[ThermalBridgeType] = ThermalBridgeType.AMBIENT
        self._display_name: Optional[str] = ""
        self._psi_value: Optional[float] = 0.1
        self._fRsi_value: Optional[float] = 0.75
        self._length: Optional[float] = 0.0

    @property
    def identifier(self) -> Optional[str]:
        return self._identifier

    @identifier.setter
    def identifier(self, value: Optional[str]) -> None:
        if value is not None:
            self._identifier = value

    @property
    def quantity(self) -> Optional[float]:
        return self._quantity

    @quantity.setter
    def quantity(self, value: Optional[float]) -> None:
        if value is not None:
            self._quantity = value

    @property
    def group_type(self) -> Optional[ThermalBridgeType]:
        return self._group_type

    @group_type.setter
    def group_type(self, value: Optional[ThermalBridgeType]) -> None:
        if value is not None:
            self._group_type = value

    @property
    def group_number(self) -> int:
        if self.group_type:
            return self.group_type.value
        else:
            return 15

    @property
    def display_name(self) -> Optional[str]:
        return self._display_name

    @display_name.setter
    def display_name(self, value: Optional[str]) -> None:
        if value is not None:
            self._display_name = value

    @property
    def psi_value(self) -> Optional[float]:
        return self._psi_value

    @psi_value.setter
    def psi_value(self, value: Optional[float]) -> None:
        if value is not None:
            self._psi_value = value

    @property
    def fRsi_value(self) -> Optional[float]:
        return self._fRsi_value

    @fRsi_value.setter
    def fRsi_value(self, value: Optional[float]) -> None:
        if value is not None:
            self._fRsi_value = value

    @property
    def length(self) -> Optional[float]:
        return self._length

    @length.setter
    def length(self, value: Optional[float]) -> None:
        if value is not None:
            self._length = value

    @property
    def unique_key(self) -> str:
        """Returns a unique text key,. Useful for sorting / grouping / merging components."""
        return f"{self.group_number}-{self.psi_value :.4f}-{self.display_name}"

    def __add__(self, other: PhxComponentThermalBridge) -> PhxComponentThermalBridge:
        """Merge with another Component into a single new Component.

        Arguments:
        ----------
            * other (PhxComponentThermalBridge): The other PhxComponentThermalBridge to merge with.

        Returns:
        --------
            * (PhxComponentThermalBridge): A new Component with attributes merged.
        """
        new_compo = self.__class__()

        # -- Copy the basic attribute values over
        new_compo.identifier = self.identifier
        new_compo.display_name = self.display_name
        new_compo.group_type = self.group_type
        new_compo.fRsi_value = self.fRsi_value
        new_compo.quantity = 1

        # -- Calculate the new length
        _self_total_len = (self.length or 0) * (self.quantity or 0)
        _other_total_len = (other.length or 0) * (other.quantity or 0)
        new_compo.length = _self_total_len + _other_total_len

        # -- Calculate the new psi value
        _self_weighted_psi_value = _self_total_len * (self.psi_value or 0.0)
        _other_weighted_psi_value = _other_total_len * (other.psi_value or 0.0)
        _total_weighted_psi_value = _self_weighted_psi_value + _other_weighted_psi_value
        try:
            new_compo.psi_value = _total_weighted_psi_value / new_compo.length
        except ZeroDivisionError:
            new_compo.psi_value = 0.0

        return new_compo

    def __eq__(self, other: PhxComponentThermalBridge) -> bool:
        TOLERANCE = 0.001
        if (
            self.group_type != other.group_type
            or self.display_name != other.display_name
            or abs((self.psi_value or 0) - (other.psi_value or 0)) > TOLERANCE
            or abs((self.fRsi_value or 0) - (other.fRsi_value or 0)) > TOLERANCE
            or abs((self.length or 0) - (other.length or 0)) > TOLERANCE
        ):
            return False
        return True
