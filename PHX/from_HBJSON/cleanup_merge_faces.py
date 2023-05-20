# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

""""""

from copy import copy
from collections import defaultdict
from typing import List

from honeybee.face import Face
from honeybee.aperture import Aperture
from ladybug_geometry.geometry2d.pointvector import Vector2D
from ladybug_geometry.geometry2d.polygon import Polygon2D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.pointvector import Point3D

# -----------------------------------------------------------------------------
# Sorting


def _hb_face_type_unique_key(_hb_face: Face) -> str:
    """Return a unique key for the HB-Face's type."""

    face_type = str(_hb_face.type)
    face_bc = str(_hb_face.boundary_condition)
    const_name = _hb_face.properties.energy.construction.display_name
    normal = str(_hb_face.geometry.normal)

    return "{}_{}_{}_{}".format(face_type, face_bc, const_name, normal)


def sort_faces_by_type(_faces: List[Face]) -> List[List[Face]]:
    """Group HB-Faces by their type."""

    d = defaultdict(list)
    for face in _faces:
        key = _hb_face_type_unique_key(face)
        d[key].append(face.duplicate())
    return list(d.values())


def sort_faces_by_co_planar(
    _faces: List[Face], _tolerance: float, _angle_tolerance: float
) -> List[List[Face]]:
    """Group HB-Faces with their co-planar neighbors."""

    d = {}
    for f in _faces:
        if not d:
            d[id(f)] = [f]
        else:
            for k, v in d.items():
                if f.geometry.plane.is_coplanar_tolerance(
                    v[0].geometry.plane, _tolerance, _angle_tolerance
                ):
                    d[k].append(f)
                    break
            else:
                d[id(f)] = [f]

    return list(d.values())


def are_coincident_points(_pt1: Point3D, _pt2: Point3D, _tolerance: float) -> bool:
    """Return True if two Point3D objects are coincident within the tolerance."""
    return _pt1.distance_to_point(_pt2) < _tolerance


def are_touching(_face_2: Face, _face_1: Face, _tolerance: float):
    """Return True if the faces are 'touching' one another within the tolerance."""

    for v in _face_1.vertices:
        if _face_2.geometry.is_point_on_face(v, _tolerance):
            return True
        elif any([are_coincident_points(v, v2, _tolerance) for v2 in _face_2.vertices]):
            return True
    return False


def find_connected_components(
    _hb_faces: List[Face], _tolerance: float
) -> List[List[Face]]:
    """ChatGPT gave me this... not 100% sure what its doing. Seems to work though."""

    visited = set()
    components = []

    def dfs(node, component):
        # type: (Face, List[Face]) -> None
        visited.add(node)
        component.append(node)

        for _neighbor_face in _hb_faces:
            if _neighbor_face not in visited and are_touching(
                node, _neighbor_face, _tolerance
            ):
                dfs(_neighbor_face, component)

    for hb_face in _hb_faces:
        if hb_face not in visited:
            component = []
            dfs(hb_face, component)
            components.append(component)

    return components


def sort_faces(
    _hb_faces: List[Face], _tolerance: float, _angle_tolerance: float
) -> List[List[Face]]:
    """Sort HB-Faces into groups of similar, planar, connected faces."""

    face_groups_by_type = sort_faces_by_type(_hb_faces)

    face_groups_coplanar = []
    for face_group in face_groups_by_type:
        face_groups_coplanar.extend(
            sort_faces_by_co_planar(face_group, _tolerance, _angle_tolerance)
        )

    face_groups_connected = []
    for face_group in face_groups_coplanar:
        face_groups_connected.extend(find_connected_components(face_group, _tolerance))

    return face_groups_connected


# -----------------------------------------------------------------------------
# -- Merging Faces


def _get_polygon2d_in_reference_space(
    _polygon2d: Polygon2D, _poly2d_plane: Plane, _base_plane: Plane
) -> Polygon2D:
    """Return a Polygon2D in the reference space of the base polygon."""

    base_plane_origin = copy(_base_plane.xyz_to_xy(_base_plane.o))

    # -- Create a Vector2D from each face's origin to the base-geom's origin
    face_origin_in_base_plane_space = _base_plane.xyz_to_xy(_poly2d_plane.o)
    mv_x = face_origin_in_base_plane_space.x - base_plane_origin.x
    mv_y = face_origin_in_base_plane_space.y - base_plane_origin.y
    move_vec = Vector2D(mv_x, mv_y)  # type: ignore

    # ------------------------------------------------------------------------
    # -- Move the face's Polygon2D into the base polygon's space
    return _polygon2d.move(move_vec)


def _create_new_Face3D(_poly2D: Polygon2D, _base_plane: Plane, _ref_face: Face) -> Face:
    """Create a new Face from a Polygon2D and a reference HB-Face."""
    new_face = Face(
        identifier=_ref_face.identifier,
        geometry=Face3D(
            boundary=tuple(_base_plane.xy_to_xyz(v) for v in _poly2D.vertices),
            plane=_ref_face.geometry.plane,
        ),
        type=_ref_face.type,
        boundary_condition=_ref_face.boundary_condition,
    )
    new_face.display_name = _ref_face.display_name
    new_face._user_data = (
        None if _ref_face.user_data is None else _ref_face.user_data.copy()
    )
    new_face._properties._duplicate_extension_attr(_ref_face._properties)

    return new_face


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


def merge_hb_faces(_faces, _tolerance, _angle_tolerance):
    # type: (List[Face], float, float) -> List[Face]
    """Merge a group of HB-Faces into the fewest number of faces possible."""

    if not _faces:
        return []

    if len(_faces) == 1:
        return _faces

    # -------------------------------------------------------------------------
    # -- Before anything else, preserve all the Apertures for adding back in later
    apertures = []
    for f in _faces:
        apertures.extend([ap.duplicate() for ap in f.apertures])

    # -------------------------------------------------------------------------
    # -- This will be the reference face for everything else to match
    reference_face = _faces.pop(0).duplicate()  # type: Face # type: ignore
    reference_plane = copy(reference_face.geometry.plane)
    polygons_in_ref_space = [
        reference_face.geometry.polygon2d,
    ]

    # -------------------------------------------------------------------------
    # -- Get all the Polygon2Ds in the same reference space
    poly2ds = (f.geometry.polygon2d for f in _faces)
    planes = (f.geometry.plane for f in _faces)
    for poly2d_plane, poly2d in zip(planes, poly2ds):
        polygons_in_ref_space.append(
            _get_polygon2d_in_reference_space(poly2d, poly2d_plane, reference_plane)
        )

    # -------------------------------------------------------------------------
    # -- Try and merge all the new Polygon2Ds together.
    merged_polygons = Polygon2D.boolean_union_all(polygons_in_ref_space, _tolerance)

    # -- If the merged results in more than one new surface, something is wrong
    # -- and the results will be really weird. So just give up in that case.
    # -- TODO: Someday... figure out the problem and fix this....
    if len(merged_polygons) > 1:
        _faces.append(reference_face)  # put the pop'd face back in
        return _faces

    # -- Create new faces for each of the merged Polygon2Ds
    faces = []
    for p in merged_polygons:
        faces.append(_create_new_Face3D(p, reference_plane, reference_face))

    # -------------------------------------------------------------------------
    # -- Add the apertures back in
    faces_with_apertures_ = []
    for fce in faces:
        _check_and_add_sub_face(fce, apertures, _tolerance, _angle_tolerance)
        faces_with_apertures_.append(fce)

    return faces_with_apertures_
