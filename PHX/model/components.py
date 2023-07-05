# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Component (Face, Aperture) Classes"""

from __future__ import annotations
from typing import ClassVar, Collection, List, Set, Union, Optional, Tuple

from PHX.model import geometry, constructions
from PHX.model.enums.building import (
    ComponentExposureExterior,
    ComponentFaceType,
    ComponentFaceOpacity,
    ComponentColor,
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
        self.exposure_exterior: ComponentExposureExterior = (
            ComponentExposureExterior.EXTERIOR
        )
        self.exposure_interior: int = 1
        self.interior_attachment_id: int = -1

        self.assembly: constructions.PhxConstructionOpaque = (
            constructions.PhxConstructionOpaque()
        )
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
    def is_roof(self) -> bool:
        if self.face_type != ComponentFaceType.ROOF_CEILING:
            return False
        return True

    def add_polygons(
        self, _input: Union[Collection[geometry.PhxPolygon], geometry.PhxPolygon]
    ) -> None:
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
        raise Exception(
            f"Error: Cannot find a host polygon for the child id_num: {_id_num}"
        )

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
    """PHPP old-style shading dimensions data."""

    def __init__(self):
        super().__init__()

        self.d_hori: Optional[float] = None
        self.h_hori: Optional[float] = None
        self.d_reveal: Optional[float] = None
        self.o_reveal: Optional[float] = None
        self.d_over: Optional[float] = None
        self.o_over: Optional[float] = None


class PhxApertureElement(PhxComponentBase):
    """A single sash / element of an Aperture Component."""

    def __init__(self, _host: PhxComponentAperture):
        super().__init__()

        self.host: PhxComponentAperture = _host
        self.display_name: str = ""
        self.polygon: Optional[
            Union[geometry.PhxPolygonRectangular, geometry.PhxPolygon]
        ] = None
        self.winter_shading_factor: float = 0.75
        self.summer_shading_factor: float = 0.75
        self.shading_dimensions: PhxApertureShadingDimensions = (
            PhxApertureShadingDimensions()
        )

    @property
    def area(self) -> float:
        """Return the area of the element's polygon."""
        if self.polygon is None:
            return 0.0
        return self.polygon.area

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

    def __init__(self, _host: PhxComponentOpaque):
        super().__init__()

        self.host = _host

        self.display_name: str = ""
        self.face_type: ComponentFaceType = ComponentFaceType.WINDOW
        self.face_opacity: ComponentFaceOpacity = ComponentFaceOpacity.TRANSPARENT
        self.color_interior: ComponentColor = ComponentColor.WINDOW
        self.color_exterior: ComponentColor = ComponentColor.WINDOW
        self.exposure_interior: int = 1
        self.exposure_exterior: ComponentExposureExterior = (
            ComponentExposureExterior.EXTERIOR
        )
        self.interior_attachment_id: int = -1

        self.window_type: constructions.PhxConstructionWindow = (
            constructions.PhxConstructionWindow()
        )

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
    def polygon_ids_sorted(self) -> Tuple[int]:
        """Return a Tuple of all the Polygon-id numbers found in the Component's Polygon group, sorted."""
        return tuple(sorted(self.polygon_ids))

    @property
    def unique_key(self) -> str:
        """Returns a unique text key,. Useful for sorting / grouping / merging components."""
        return (
            f"{self.face_type.value}-{self.face_opacity.value}-{self.exposure_interior}-{self.interior_attachment_id}-"
            f"{self.exposure_exterior.value}-{self.window_type_id_num}-{self.shade_type_id_num}-{self.variant_type_name}-{self.default_monthly_shading_correction_factor}"
        )

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
        new_compo.default_monthly_shading_correction_factor = (
            self.default_monthly_shading_correction_factor
        )

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
            or abs(
                self.default_monthly_shading_correction_factor
                - other.default_monthly_shading_correction_factor
            )
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
        self._group_number: Optional[ThermalBridgeType] = ThermalBridgeType.AMBIENT
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
    def group_number(self) -> Optional[ThermalBridgeType]:
        return self._group_number

    @group_number.setter
    def group_number(self, value: Optional[ThermalBridgeType]) -> None:
        if value is not None:
            self._group_number = value

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
