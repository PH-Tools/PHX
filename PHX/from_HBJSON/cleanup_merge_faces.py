# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions to allow the merging of HB-Faces which are used to simplify HB-Models."""

from copy import copy
from collections import defaultdict
import math
from typing import List, Sequence, Tuple, Union, TypeVar

from honeybee.face import Face
from honeybee.shade import Shade
from honeybee.aperture import Aperture
from ladybug_geometry.geometry2d.pointvector import Vector2D
from ladybug_geometry.geometry2d.polygon import Polygon2D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D


# -----------------------------------------------------------------------------
# -- Geometry Functions
def cross_product(
    a: Union[Sequence[float], Vector3D], b: Union[Sequence[float], Vector3D]
) -> Sequence[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def dot_product(
    a: Union[Sequence[float], Vector3D], b: Union[Sequence[float], Vector3D]
) -> float:
    return sum([a[i] * b[i] for i in range(len(a))])


def magnitude(a: Union[Sequence[float], Vector3D]) -> float:
    return sum([a[i] ** 2 for i in range(len(a))]) ** 0.5


def normalize(a: Union[Sequence[float], Vector3D]) -> List[float]:
    mag = magnitude(a)
    return [a[i] / mag for i in range(len(a))]


def angle_between_planes(plane1, plane2, _tolerance):
    # type: (Plane, Plane, float) -> float
    # Calculate the x-axes of the planes
    plane1_x_axis = cross_product(plane1.n, plane1.x)
    plane2_x_axis = cross_product(plane2.n, plane2.x)

    # Normalize the x-axes
    plane1_x_axis = normalize(plane1_x_axis)
    plane2_x_axis = normalize(plane2_x_axis)

    # Calculate the dot product between the x-axes
    dot_product_value = dot_product(plane1_x_axis, plane2_x_axis)

    # Calculate the angle between the x-axes
    # Handle parallel or coincident planes
    if (1.0 - dot_product_value) < _tolerance:
        return 0.0

    angle_rad = math.acos(dot_product_value)

    # Determine the counterclockwise angle
    orientation = cross_product(plane1_x_axis, plane2_x_axis)
    if dot_product(plane1.n, orientation) < 0:
        angle_rad = 2 * math.pi - angle_rad

    return angle_rad


# -----------------------------------------------------------------------------
# Sorting

TFaceOrShade = TypeVar("TFaceOrShade", Face, Shade)


def _hb_face_type_unique_key(_hb_face: TFaceOrShade) -> str:
    """Return a unique key for the HB-Face's type."""

    face_type = str(getattr(_hb_face, "type", "shade"))
    face_bc = str(getattr(_hb_face, "boundary_condition", "shade"))
    hb_prop_e = _hb_face.properties.energy  # type: ignore
    const_name = hb_prop_e.construction.display_name

    return "{}_{}_{}".format(face_type, face_bc, const_name)


def sort_hb_faces_by_type(_faces: List[TFaceOrShade]) -> List[List[TFaceOrShade]]:
    """Group HB-Faces by their type."""

    d = defaultdict(list)
    for face in _faces:
        key = _hb_face_type_unique_key(face)
        d[key].append(face.duplicate())
    return list(d.values())


def sort_faces_by_co_planar(
    _faces: List[TFaceOrShade], _tolerance: float, _angle_tolerance_radians: float
) -> List[List[TFaceOrShade]]:
    """Group HB-Faces with their co-planar neighbors.
    Args:
        _faces: (List[Face | Shade]) A list of HB-Faces to sort.
        _tolerance: (Model units) The tolerance value for co-planarity test, in model units.
        _angle_tolerance: (Radians) The tolerance for co-planarity, in radians.
    Returns:
        (List[List[Face | Shade]]) A list of lists of HB-Faces that are co-planar.
    """

    groups = {}
    for face in _faces:
        for group_plane, group_faces in groups.items():
            if face.geometry.plane.is_coplanar_tolerance(
                group_plane, _tolerance, _angle_tolerance_radians
            ):
                group_faces.append(face)
                break
        else:
            groups[face.geometry.plane] = [face]
    return list(groups.values())


def are_coincident_points(_pt1: Point3D, _pt2: Point3D, _tolerance: float) -> bool:
    """Return True if two Point3D objects are coincident within the tolerance."""
    return _pt1.distance_to_point(_pt2) < _tolerance


def are_touching(_face_2: TFaceOrShade, _face_1: TFaceOrShade, _tolerance: float):
    """Return True if the faces are 'touching' one another within the tolerance."""

    for v in _face_1.vertices:
        if _face_2.geometry.is_point_on_face(v, _tolerance):
            return True
        elif any([are_coincident_points(v, v2, _tolerance) for v2 in _face_2.vertices]):
            return True
    return False


def find_connected_components(
    _hb_faces: List[TFaceOrShade], _tolerance: float
) -> List[List[TFaceOrShade]]:
    """Finds connected components of touching faces in a list of Honeybee faces.

    Args:
        _hb_faces List[Face | Shade]: A list of Honeybee face or shades to search for connected components.
        _tolerance: A tolerance value for determining whether two faces are touching.

    Returns:
        A list of lists, where each inner list contains a connected component of touching faces.
    """

    """Initialize an empty set called visited to keep track of which faces have 
    been visited during the search, and an empty list called components to store 
    the connected component groups."""
    visited = set()
    components = []

    def depth_first_search(node, component):
        # type: (TFaceOrShade, List[TFaceOrShade]) -> None
        """Define a recursive function that takes a starting face node
        and a list component to store the connected component.
        The function adds the starting face to the visited set and the component list,
        and then recursively calls itself on all neighboring faces that are not
        in the visited set and are touching the starting face within
        a given tolerance _tolerance.
        """
        visited.add(node)
        component.append(node)

        for _neighbor_face in _hb_faces:
            if _neighbor_face not in visited and are_touching(
                node, _neighbor_face, _tolerance
            ):
                depth_first_search(_neighbor_face, component)

    """Loop over all the faces in the input list _hb_faces. If a face has not 
    been visited yet, create an empty list called 'component', call the 'depth_first_search'
    function with the face and the new component list, and append the 'component' list 
    to the master components list."""
    for hb_face in _hb_faces:
        if hb_face not in visited:
            component = []
            depth_first_search(hb_face, component)
            components.append(component)

    return components


def sort_hb_faces(
    _hb_faces: List[TFaceOrShade], _tolerance: float, _angle_tolerance_degrees: float
) -> List[List[TFaceOrShade]]:
    """Sort HB-Faces into groups of similar, planar, connected faces.

    Args:
        _hb_faces: (List[Face | Shade]) A list of HB-Faces to sort.
        _tolerance: (Model units) The tolerance value for co-planarity test, in model units.
        _angle_tolerance_degrees: (Degrees) The tolerance for co-planarity, in degrees.
    Returns:
        (List[List[Face | Shade]]) A list of lists of HB-Faces that are similar, planar, and connected.
    """

    face_groups_by_type = sort_hb_faces_by_type(_hb_faces)
    angle_tolerance_radians = math.radians(_angle_tolerance_degrees)

    face_groups_coplanar = []
    for face_group in face_groups_by_type:
        face_groups_coplanar.extend(
            sort_faces_by_co_planar(face_group, _tolerance, angle_tolerance_radians)
        )

    face_groups_connected = []
    for face_group in face_groups_coplanar:
        face_groups_connected.extend(find_connected_components(face_group, _tolerance))

    return face_groups_connected


# -----------------------------------------------------------------------------
# -- Merging Faces


def _get_polygon2d_in_reference_space(
    _polygon2d: Polygon2D, _poly2d_plane: Plane, _base_plane: Plane, _tolerance: float
) -> Polygon2D:
    """Return a Polygon2D in the reference space of the base polygon."""

    # -- Create a Vector2D from each face's origin to the base-geom's origin
    face_origin_in_base_plane_space = _base_plane.xyz_to_xy(_poly2d_plane.o)
    base_plane_origin = copy(_base_plane.xyz_to_xy(_base_plane.o))
    # ------------------------------------------------------------------------
    # -- Construct a Move vector from the face's origin to the base-plane's origin
    mv_x = face_origin_in_base_plane_space.x - base_plane_origin.x
    mv_y = face_origin_in_base_plane_space.y - base_plane_origin.y
    move_vec = Vector2D(mv_x, mv_y)  # type: ignore

    # ------------------------------------------------------------------------
    # -- Move the face's Polygon2D into the base polygon's space
    moved_polygon = _polygon2d.move(move_vec)

    # ------------------------------------------------------------------------
    # -- Rotate the Polygon to align with the base-plane
    angle = angle_between_planes(_base_plane, _poly2d_plane, _tolerance)
    rotated_polygon = moved_polygon.rotate(
        angle=angle, origin=face_origin_in_base_plane_space
    )
    return rotated_polygon


def _add_sub_face(_face: Face, _aperture: Aperture):
    """Add an HB-sub-face (either HB-Aperture or HB-Door) to a parent Face.

    NOTE: this method is copied from honeybee's Grasshopper component "HB Add Subface"
    """
    if isinstance(_aperture, Aperture):  # the sub-face is an Aperture
        _face.add_aperture(_aperture)
    else:  # the sub-face is a Door
        _face.add_door(_aperture)

    return _face


def _check_and_add_sub_face(
    _face: Face,
    _apertures: List[Aperture],
    _tolerance: float,
    _angle_tolerance: float,
):
    """Check whether a HB-sub-face is valid for an HB-face and, if so, add it.

    NOTE: this method is copied from honeybee's Grasshopper component "HB Add Subface"
    """
    for aperture in _apertures:
        if _face.geometry.is_sub_face(aperture.geometry, _tolerance, _angle_tolerance):
            _add_sub_face(_face, aperture)


def _create_new_HB_Face(_face3D: Face3D, _ref_face: Face) -> Face:
    """Create a new HB-Face using a Face3D and a reference HB-Face."""
    new_face = Face(
        identifier=_ref_face.identifier,
        geometry=_face3D,
        type=_ref_face.type,
        boundary_condition=_ref_face.boundary_condition,
    )
    new_face.display_name = _ref_face.display_name
    new_face._user_data = (
        None if _ref_face.user_data is None else _ref_face.user_data.copy()
    )
    new_face._properties._duplicate_extension_attr(_ref_face._properties)

    return new_face


def _create_new_HB_Shade(_face3D: Face3D, _ref_face: Shade) -> Shade:
    """Create a new HB-Shade using a Face3D and a reference HB-Shade."""
    new_face = Shade(
        identifier=_ref_face.identifier,
        geometry=_face3D,
        is_detached=True,
    )
    new_face.display_name = _ref_face.display_name
    new_face._user_data = (
        None if _ref_face.user_data is None else _ref_face.user_data.copy()
    )
    new_face._properties._duplicate_extension_attr(_ref_face._properties)

    return new_face


def _create_new_Face3D(
    _poly2D: Polygon2D, _base_plane: Plane, _ref_face: TFaceOrShade
) -> Face3D:
    """Return a new Face3D based on a Polygon2D and a reference HB-Face."""
    return Face3D(
        boundary=tuple(_base_plane.xy_to_xyz(v) for v in _poly2D.vertices),
        plane=_ref_face.geometry.plane,
    )


def find_parent_and_child_polygons(
    _polygons: List[Polygon2D],
) -> Tuple[List[Polygon2D], List[Polygon2D]]:
    """Return a Tuple of any parent (container) and child (contained) polygons from a list of polygons."""

    # Initialize empty lists for parent and child surfaces
    parent_polygon = []
    child_polygons = []

    # Compare each surface with all other surfaces
    for i, _polygon in enumerate(_polygons):
        is_inside_any = False

        for j, other_polygon in enumerate(_polygons):
            if i == j:
                continue

            if _polygon.is_polygon_inside(other_polygon):
                is_inside_any = True
                break

        # If the surface is inside any other surface, add it to child_surfaces
        # Otherwise, it is a parent surface
        if is_inside_any:
            parent_polygon.append(_polygon)
        else:
            child_polygons.append(_polygon)

    return parent_polygon, child_polygons


def merge_hb_face_polygons(
    _faces: List[TFaceOrShade], _tolerance: float, _angle_tolerance_degrees: float
) -> Tuple[List[Polygon2D], Plane, TFaceOrShade]:
    # -------------------------------------------------------------------------
    # -- This will be the reference face for everything else to match
    reference_face: TFaceOrShade = _faces.pop(0).duplicate()  # type: ignore
    reference_plane: Plane = copy(reference_face.geometry.plane)
    polygons_in_ref_space: List[Polygon2D] = []
    polygons_in_ref_space.append(reference_face.geometry.polygon2d)

    # -------------------------------------------------------------------------
    # -- Get all the Polygon2Ds in the same reference space
    poly2ds = [f.geometry.polygon2d for f in _faces]
    planes = (f.geometry.plane for f in _faces)

    if len(poly2ds) > 100:
        print(
            f"Merging together {len(poly2ds)} polygons for '{reference_face.display_name}'."
        )
        print("Consider reducing the complexity of the geometry.")

    for poly2d_plane, poly2d in zip(planes, poly2ds):
        polygons_in_ref_space.append(
            _get_polygon2d_in_reference_space(
                poly2d, poly2d_plane, reference_plane, _tolerance
            )
        )

    # -------------------------------------------------------------------------
    # -- Try and merge all the new Polygon2Ds together.
    merged_polygons = Polygon2D.boolean_union_all(polygons_in_ref_space, _tolerance)

    if len(poly2ds) > 100:
        print(f"merge_hb_face_polygons resulted in: {len(merged_polygons)} faces.")

    return (merged_polygons, reference_plane, reference_face)


def merge_hb_faces(
    _faces: List[Face], _tolerance: float, _angle_tolerance_degrees: float
):
    """Merge a group of HB-Faces into the fewest number of faces possible."""

    if not _faces:
        return []

    if len(_faces) == 1:
        return _faces

    # -------------------------------------------------------------------------
    # -- Before anything else, preserve any the Apertures for adding back in later
    apertures = []
    for f in _faces:
        apertures.extend([ap.duplicate() for ap in getattr(f, "apertures", [])])

    # -------------------------------------------------------------------------
    # -- Merge the Polygons togther
    merged_polygons, ref_plane, ref_face = merge_hb_face_polygons(
        _faces, _tolerance, _angle_tolerance_degrees
    )

    # -------------------------------------------------------------------------
    # -- Create new Face3D, and HB-Faces from the Polygon2Ds
    faces = []
    if len(merged_polygons) == 1:
        # -- Create new faces for the merged Polygon2Ds
        face3ds = (_create_new_Face3D(p, ref_plane, ref_face) for p in merged_polygons)
        faces = [_create_new_HB_Face(f3d, ref_face) for f3d in face3ds]
    elif len(merged_polygons) > 1:
        # -- It may mean that there are 'holes' in a surface? So try and find
        # -- the parent and any child surfaces.

        parent_polygon, child_polygons = find_parent_and_child_polygons(merged_polygons)

        # -- Check the results
        if len(parent_polygon) != 1:
            # -- Something went wrong, give up.
            _faces.append(ref_face)
            return _faces

        # -- If only 1 parent, lets make some Face3Ds and Faces
        parent_face_3d = [
            _create_new_Face3D(p, ref_plane, ref_face) for p in parent_polygon
        ]
        child_face_3ds = [
            _create_new_Face3D(p, ref_plane, ref_face) for p in child_polygons
        ]
        face_3ds = [Face3D.from_punched_geometry(parent_face_3d[0], child_face_3ds)]
        faces = [_create_new_HB_Face(f3d, ref_face) for f3d in face_3ds]

    # -------------------------------------------------------------------------
    # -- Add the apertures back in
    faces_with_apertures_ = []
    for _face in faces:
        _check_and_add_sub_face(_face, apertures, _tolerance, _angle_tolerance_degrees)
        faces_with_apertures_.append(_face)

    return faces_with_apertures_


def merge_hb_shades(
    _faces: List[Shade], _tolerance: float, _angle_tolerance_degrees: float
) -> List[Shade]:
    """Merge a group of HB-Shades into the fewest number of shades possible."""
    if not _faces:
        return []

    if len(_faces) == 1:
        return _faces

    # -------------------------------------------------------------------------
    # -- Merge the Polygons togther
    merged_polygons, ref_plane, ref_face = merge_hb_face_polygons(
        _faces, _tolerance, _angle_tolerance_degrees
    )

    # -------------------------------------------------------------------------
    # -- Create new Face3D, and HB-Faces from the Polygon2Ds
    hb_shades_ = []
    if len(merged_polygons) == 1:
        # -- Create new faces for the merged Polygon2Ds
        face3ds = (_create_new_Face3D(p, ref_plane, ref_face) for p in merged_polygons)
        hb_shades_ = [_create_new_HB_Shade(f3d, ref_face) for f3d in face3ds]
    elif len(merged_polygons) > 1:
        # -- It may mean that there are 'holes' in a surface? So try and find
        # -- the parent and any child surfaces.

        parent_polygon, child_polygons = find_parent_and_child_polygons(merged_polygons)

        # -- Check the results
        if len(parent_polygon) != 1:
            # -- Something went wrong, give up.
            _faces.append(ref_face)
            return _faces

        # -- If only 1 parent, lets make some Face3Ds and Faces
        parent_face_3d = [
            _create_new_Face3D(p, ref_plane, ref_face) for p in parent_polygon
        ]
        child_face_3ds = [
            _create_new_Face3D(p, ref_plane, ref_face) for p in child_polygons
        ]
        face_3ds = Face3D.from_punched_geometry(parent_face_3d[0], child_face_3ds)
        hb_shades_ = [_create_new_HB_Shade(f3d, ref_face) for f3d in face_3ds]

    return hb_shades_
