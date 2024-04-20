# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Geometry Classes"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import ClassVar, Collection, List, Optional, Union


class PolygonEdgeError(Exception):
    def __init__(self, _polygon: PhxPolygonRectangular, _segment_name: str):
        self.msg = (
            f"Error: Cannot create PhxPolygonRectangle {_polygon}"
            f"segment {_segment_name}. Missing 1 or more vertices?"
        )
        super().__init__(self.msg)


@dataclass
class PhxVertix2D:
    """A 2D vertix."""

    _count: ClassVar[int] = 0

    id_num: int = field(init=False, default=0)
    x: float
    y: float

    def __eq__(self, other: PhxVertix2D) -> bool:
        TOLERANCE = 0.0001
        return abs(self.x - other.x) < TOLERANCE and abs(self.y - other.y) < TOLERANCE and self.id_num == other.id_num

    def is_equivalent(self, other: PhxVertix) -> bool:
        TOLERANCE = 0.001
        return abs(self.x - other.x) < TOLERANCE and abs(self.y - other.y) < TOLERANCE

    def __post_init__(self):
        PhxVertix._count += 1
        self.id_num = PhxVertix._count

    @property
    def unique_key(self) -> str:
        """Return a unique key (str) for the Vertex. Used for dicts, welding, etc"""
        return f"{self.x :0.10f}_{self.y :0.10f}"

    def __hash__(self) -> int:
        return hash(self.unique_key)


@dataclass
class PhxVertix:
    _count: ClassVar[int] = 0

    id_num: int = field(init=False, default=0)
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __eq__(self, other: PhxVertix) -> bool:
        TOLERANCE = 0.0001
        return (
            abs(self.x - other.x) < TOLERANCE
            and abs(self.y - other.y) < TOLERANCE
            and abs(self.z - other.z) < TOLERANCE
            and self.id_num == other.id_num
        )

    def is_equivalent(self, other: PhxVertix) -> bool:
        TOLERANCE = 0.001
        return (
            abs(self.x - other.x) < TOLERANCE
            and abs(self.y - other.y) < TOLERANCE
            and abs(self.z - other.z) < TOLERANCE
        )

    def __post_init__(self):
        PhxVertix._count += 1
        self.id_num = PhxVertix._count

    @property
    def unique_key(self) -> str:
        """Return a unique key (str) for the Vertex. Used for dicts, welding, etc"""
        return f"{self.x :0.10f}_{self.y :0.10f}_{self.z :0.10f}"

    def __hash__(self) -> int:
        return hash(self.unique_key)

    def distance_to(self, other: PhxVertix) -> float:
        """Return the distance between this vertex and another."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2)


@dataclass
class PhxVector:
    x: float
    y: float
    z: float

    @classmethod
    def from_2_points(cls, _start_pt: PhxVertix, _end_pt: PhxVertix) -> PhxVector:
        """Return a new PhxVector based on a start and end point."""
        return cls(_end_pt.x - _start_pt.x, _end_pt.y - _start_pt.y, _end_pt.z - _start_pt.z)

    def scale(self, _factor: float) -> None:
        self.x = self.x * _factor
        self.y = self.y * _factor
        self.z = self.z * _factor

    def dot(self, other: PhxVector) -> float:
        """Get the dot product of this vector with another."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def rotate_around(self, _axis: PhxVector, _angle_deg: float) -> PhxVector:
        """Rotate this vector around an axis by an angle in radians."""
        _cos = math.cos(math.radians(_angle_deg))
        _sin = math.sin(math.radians(_angle_deg))
        _x = (
            (_cos + _axis.x**2 * (1 - _cos)) * self.x
            + (_axis.x * _axis.y * (1 - _cos) - _axis.z * _sin) * self.y
            + (_axis.x * _axis.z * (1 - _cos) + _axis.y * _sin) * self.z
        )
        _y = (
            (_axis.y * _axis.x * (1 - _cos) + _axis.z * _sin) * self.x
            + (_cos + _axis.y**2 * (1 - _cos)) * self.y
            + (_axis.y * _axis.z * (1 - _cos) - _axis.x * _sin) * self.z
        )
        _z = (
            (_axis.z * _axis.x * (1 - _cos) - _axis.y * _sin) * self.x
            + (_axis.z * _axis.y * (1 - _cos) + _axis.x * _sin) * self.y
            + (_cos + _axis.z**2 * (1 - _cos)) * self.z
        )
        return PhxVector(_x, _y, _z)

    def unitize(self) -> None:
        """Convert this vector to a unit vector."""
        magnitude = math.sqrt(self.x**2 + self.y**2 + self.z**2)
        if magnitude > 0:
            self.x /= magnitude
            self.y /= magnitude
            self.z /= magnitude

    def __eq__(self, other: PhxVector) -> bool:
        TOLERANCE = 0.001
        return (
            abs(self.x - other.x) < TOLERANCE
            and abs(self.y - other.y) < TOLERANCE
            and abs(self.z - other.z) < TOLERANCE
        )


@dataclass
class PhxPlane:
    normal_vector: PhxVector
    origin: PhxVertix
    x: PhxVector
    y: PhxVector

    @property
    def normal(self) -> PhxVector:
        return self.normal_vector

    def __eq__(self, other: PhxPlane) -> bool:
        return (
            self.normal_vector == other.normal_vector
            and self.origin == other.origin
            and self.x == other.x
            and self.y == other.y
        )

    def xyz_to_xy(self, point: PhxVertix) -> PhxVertix2D:
        """Get a Point2D in the coordinate system of this plane from a Point3D.

        Copied from Ladybug-Geometry
        https://github.com/ladybug-tools/ladybug-geometry/blob/master/ladybug_geometry/geometry3d/plane.py
        """
        _diff = PhxVector(point.x - self.origin.x, point.y - self.origin.y, point.z - self.origin.z)
        return PhxVertix2D(self.x.dot(_diff), self.y.dot(_diff))

    def xy_to_xyz(self, point):
        """Get a Point3D from a Point2D in the coordinate system of this plane.

        Cpied from Ladybug-Geometry
        https://github.com/ladybug-tools/ladybug-geometry/blob/master/ladybug_geometry/geometry3d/plane.py
        """
        _u = (self.x.x * point.x, self.x.y * point.x, self.x.z * point.x)
        _v = (self.y.x * point.y, self.y.y * point.y, self.y.z * point.y)
        return PhxVertix(
            self.origin.x + _u[0] + _v[0],
            self.origin.y + _u[1] + _v[1],
            self.origin.z + _u[2] + _v[2],
        )


@dataclass
class PhxLineSegment:
    vertix_1: PhxVertix
    vertix_2: PhxVertix

    @property
    def length(self) -> float:
        return abs(
            math.sqrt(
                (
                    (self.vertix_2.x - self.vertix_1.x) ** 2
                    + (self.vertix_2.y - self.vertix_1.y) ** 2
                    + (self.vertix_2.z - self.vertix_1.z) ** 2
                )
            )
        )

    def __eq__(self, other: PhxLineSegment) -> bool:
        if self.vertix_1 == other.vertix_1 and self.vertix_2 == other.vertix_2:
            return True
        if self.vertix_1 == other.vertix_2 and self.vertix_2 == other.vertix_1:
            return True
        return False


@dataclass
class PhxPolygon:
    """A Polygon surface defined by 3 or more vertices."""

    _count: ClassVar[int] = 0

    _display_name: str
    _area: Optional[float]
    _center: Optional[PhxVertix]
    normal_vector: PhxVector
    plane: PhxPlane

    _vertices: List[PhxVertix] = field(init=False, default_factory=list)
    child_polygon_ids: List[int] = field(init=False, default_factory=list)

    id_num: int = field(init=False, default=0)

    def __eq__(self, other: PhxPolygon) -> bool:
        # -- Check the PolyIds
        if not len(self.child_polygon_ids) == len(other.child_polygon_ids):
            return False
        for _ in self.child_polygon_ids:
            if not _ in other.child_polygon_ids:
                return False

        # # -- Check the actual vertices
        if not len(self.vertices) == len(other.vertices):
            return False
        # -- For each Vertix, make sure this is an equivalent vertix in the other
        for v in self.vertices:
            if not any((_.is_equivalent(v) for _ in other.vertices)):
                return False

        return True

    @property
    def area(self) -> float:
        if not self._area:
            self._area = self.calculate_area()
        return self._area

    @area.setter
    def area(self, _in: Optional[float]):
        if _in:
            self._area = _in

    @property
    def center(self) -> PhxVertix:
        if not self._center:
            self._center = self.calculate_center()
        return self._center

    @center.setter
    def center(self, _in: Optional[PhxVertix]):
        if _in:
            self._center = _in

    def __post_init__(self):
        PhxPolygon._count += 1
        self.id_num = PhxPolygon._count

    @property
    def display_name(self) -> str:
        if not self._display_name:
            return str(self.id_num)
        else:
            return self._display_name

    @display_name.setter
    def display_name(self, _in: str):
        self._display_name = str(_in)

    @property
    def vertices(self) -> List[PhxVertix]:
        return self._vertices

    @property
    def vertices_id_numbers(self) -> List[int]:
        return [v.id_num for v in self.vertices]

    @property
    def angle_from_horizontal(self) -> float:
        """Return the surface normal's angle (degrees) off horizontal.

        ie: pointing 'up'=0, vertical surface=90, pointing 'down'=180

        https://www.omnicalculator.com/math/angle-between-two-vectors

        Returns:
        -------
            * (float): Degrees. The surface normal angle off horizontal.
        """

        # Get the input Vector's X and Y parts
        a = self.normal_vector
        b = PhxVector(0, 0, 1.0)

        try:
            angle = math.acos(
                (a.x * b.x + a.y * b.y + a.z * b.z)
                / (math.sqrt(a.x**2 + a.y**2 + a.z**2) * math.sqrt(b.x**2 + b.y**2 + b.z**2))
            )
        except ZeroDivisionError:
            angle = 0.0

        return math.degrees(angle)

    @property
    def is_horizontal(self, tolerance: float = 0.0001) -> bool:
        a = self.angle_from_horizontal
        if abs(a) < tolerance:
            return True
        elif abs(180 - abs(a)) < tolerance:
            return True
        return False

    @property
    def is_vertical(self, tolerance: float = 0.0001) -> bool:
        a = self.angle_from_horizontal
        if abs(90 - abs(a)) < tolerance:
            return True
        return False

    @property
    def cardinal_orientation_angle(self, _reference_vector: Optional[PhxVector] = None) -> float:
        """Calculate polygon normal's horizontal angle off a reference. By default, the
        reference vector will be (x=0,y=1,z=0) assuming north is y-direction.

        http://frasergreenroyd.com/obtaining-the-angle-between-two-vectors-for-360-degrees/
        Results 0=north, 90=east, 180=south, 270=west

        Arguments:
        ----------
            * _reference_vector: (PhxVector) The reference vector representing
                'North'. By default, will use (x=0, y=1, z=0) as the north vector.

        Returns:
        --------
            (float) Degrees. The clockwise angle off reference of the surface normal.
        """
        if self.is_horizontal:
            return 0.0

        if not _reference_vector:
            _reference_vector = PhxVector(0, 1.0, 0)

        a_x = self.normal_vector.x
        a_y = self.normal_vector.y

        b_x = _reference_vector.x
        b_y = _reference_vector.y

        angle = math.atan2(b_y, b_x) - math.atan2(a_y, a_x)
        angle = math.degrees(angle)

        if angle < 0:
            angle = angle + 360

        return angle

    def add_vertix(self, _phx_vertix: PhxVertix) -> None:
        self.vertices.append(_phx_vertix)

    def add_child_poly_id(self, _child_ids: Union[Collection[int], int]) -> None:
        if not isinstance(_child_ids, Collection):
            _child_ids = (_child_ids,)

        for child_id in _child_ids:
            self.child_polygon_ids.append(child_id)

    def set_vertex(self, _phx_vertix: PhxVertix, index: int):
        """Set a vertex at a specific index."""
        self.vertices[index] = _phx_vertix

    def calculate_area(self) -> float:
        """Calculate the area of the polygon."""
        x_coords = [self.plane.xyz_to_xy(v).x for v in self.vertices]
        y_coords = [self.plane.xyz_to_xy(v).y for v in self.vertices]
        x_coords.append(x_coords[0])
        y_coords.append(y_coords[0])
        return (
            abs(sum([x_coords[i] * y_coords[i + 1] - x_coords[i + 1] * y_coords[i] for i in range(len(x_coords) - 1)]))
            / 2
        )

    def calculate_center(self) -> PhxVertix:
        """Find the center of the polygon."""
        num_vertices = len(self.vertices)
        center = PhxVertix(0, 0, 0)  # Initialize the center point at (0, 0, 0)

        # Sum up the coordinates of all vertices
        for vertex in self.vertices:
            center.x += vertex.x
            center.y += vertex.y
            center.z += vertex.z

        # Divide the sum by the number of vertices to get the average position
        center.x /= num_vertices
        center.y /= num_vertices
        center.z /= num_vertices

        return center

    def scale(self, _scale_factor: float = 1.0) -> None:
        """Scale the polygon by the given factor."""
        for vertex in self.vertices:
            vertex.x -= self.center.x
            vertex.y -= self.center.y
            vertex.z -= self.center.z

            vertex.x *= _scale_factor
            vertex.y *= _scale_factor
            vertex.z *= _scale_factor

            vertex.x += self.center.x
            vertex.y += self.center.y
            vertex.z += self.center.z

    def perimeter_length(self) -> float:
        """Calculate the total perimeter length of the polygon."""
        perimeter = 0.0
        for i in range(len(self.vertices)):
            perimeter += self.vertices[i].distance_to(self.vertices[i - 1])
        return perimeter


@dataclass
class PhxPolygonRectangular(PhxPolygon):
    """A Polygon with additional geometric attributes for rectangular surfaces."""

    vertix_upper_left: Optional[PhxVertix] = field(init=False, default=None)
    vertix_lower_left: Optional[PhxVertix] = field(init=False, default=None)
    vertix_lower_right: Optional[PhxVertix] = field(init=False, default=None)
    vertix_upper_right: Optional[PhxVertix] = field(init=False, default=None)

    VERTEX_ORDER = [
        "vertix_upper_left",
        "vertix_lower_left",
        "vertix_lower_right",
        "vertix_upper_right",
    ]

    def __post_init__(self):
        super().__post_init__()

    @property
    def edge_top(self) -> PhxLineSegment:
        """Returns the PhxLineSegment representing the 'Top' side of the Polygon (viewed from outside)."""
        if not self.vertix_upper_right or not self.vertix_upper_left:
            raise PolygonEdgeError(self, "top")
        return PhxLineSegment(self.vertix_upper_right, self.vertix_upper_left)

    @property
    def edge_left(self) -> PhxLineSegment:
        """Returns the PhxLineSegment representing the 'Left' side of the Polygon (viewed from outside)."""
        if not self.vertix_upper_left or not self.vertix_lower_left:
            raise PolygonEdgeError(self, "left")
        return PhxLineSegment(self.vertix_upper_left, self.vertix_lower_left)

    @property
    def edge_bottom(self) -> PhxLineSegment:
        """Returns the PhxLineSegment representing the 'Bottom' side of the Polygon (viewed from outside)."""
        if not self.vertix_lower_left or not self.vertix_lower_right:
            raise PolygonEdgeError(self, "bottom")
        return PhxLineSegment(self.vertix_lower_left, self.vertix_lower_right)

    @property
    def edge_right(self) -> PhxLineSegment:
        """Returns the PhxLineSegment representing the 'Right' side of the Polygon (viewed from outside)."""
        if not self.vertix_lower_right or not self.vertix_upper_right:
            raise PolygonEdgeError(self, "right")
        return PhxLineSegment(self.vertix_lower_right, self.vertix_upper_right)

    @property
    def width(self) -> float:
        return self.edge_top.length

    @property
    def height(self) -> float:
        return self.edge_left.length

    def add_vertix(self, _phx_vertix: PhxVertix) -> None:
        print(
            f'Method "add_vertix()" is not allowed for {self.__class__.__name__} objects.'
            f"Please assign the vertix corners directly (vertix_upper_left-left, vertix_lower_left-right, etc..)"
        )

    @property
    def vertices(self) -> List[PhxVertix]:
        """Return a List of the PhxPolygonRectangle Vertices (counter-clockwise from upper-left)."""
        corner_vertices = [getattr(self, v) for v in self.VERTEX_ORDER]
        # filter out any 'None' vertices
        return [v for v in corner_vertices if v]

    def set_vertex(self, _phx_vertix: PhxVertix, index: int):
        """Set a vertex at a specific index."""
        vert_name = self.VERTEX_ORDER[index]
        setattr(self, vert_name, _phx_vertix)

    @property
    def area(self) -> float:
        """Returns the area of the rectangular surface."""
        return self.width * self.height

    def perimeter_length(self) -> float:
        """Calculate the total perimeter length of the polygon."""
        return (2 * self.width) + (2 * self.height)


@dataclass
class PhxGraphics3D:
    polygons: List[PhxPolygon] = field(default_factory=list)

    @property
    def vertices(self) -> List[PhxVertix]:
        """Returns a sorted list with all of the unique vertix objects of all the polygons in the collection."""
        return sorted(
            {vertix for polygon in self.polygons for vertix in polygon.vertices},
            key=lambda _: _.id_num,
        )

    def add_polygons(self, _polygons: Union[Collection[PhxPolygon], PhxPolygon]) -> None:
        """Adds a new Polygon object to the collection"""

        if not isinstance(_polygons, Collection):
            _polygons = [_polygons]

        for polygon in _polygons:
            self.polygons.append(polygon)

    def get_polygons_by_id(self, _ids: Collection[int]) -> List[PhxPolygon]:
        """Returns a sorted list of polygons in the collection matching the IDs supplied.

        Arguments:
        ----------
            * _ids: (Collection[int]): A collection of one or more id_nums to look for.

        Returns:
        --------
            * List[PhxPolygon]: A sorted (by display_name) list of all the
                polygons with matching id_nums.
        """

        if not isinstance(_ids, Collection):
            _ids = {_ids}

        return sorted([p for p in self.polygons if p.id_num in _ids], key=lambda _: _.display_name)

    def __bool__(self) -> bool:
        return bool(self.polygons)
