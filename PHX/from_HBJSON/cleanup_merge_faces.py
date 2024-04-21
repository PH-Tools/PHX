# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions to allow the merging of HB-Faces which are used to simplify HB-Models."""

import logging
from typing import List, Sequence, Tuple, TypeVar

try:
    from honeybee.aperture import Aperture
    from honeybee.face import Face
    from honeybee.shade import Shade
except ImportError as e:
    raise ImportError("\nFailed to import honeybee:\n\t{}".format(e))

try:
    from ladybug_geometry.geometry2d.polygon import Polygon2D
    from ladybug_geometry.geometry3d.face import Face3D
    from ladybug_geometry.geometry3d.plane import Plane
except ImportError as e:
    raise ImportError("\nFailed to import ladybug_geometry:\n\t{}".format(e))

try:
    from honeybee_ph_utils import polygon2d_tools
except ImportError as e:
    raise ImportError("\nFailed to import honeybee_ph_utils:\n\t{}".format(e))


logger = logging.getLogger()

TFaceOrShade = TypeVar("TFaceOrShade", Face, Shade)


def _add_sub_face(_face: Face, _aperture: Aperture):
    """Add an HB-sub-face (either HB-Aperture or HB-Door) to a parent Face.

    NOTE: this method is copied from honeybee's Grasshopper component "HB Add Sub-face"
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
) -> None:
    """Check whether a HB-sub-face is valid for an HB-face and, if so, add it.

    NOTE: this method is copied from honeybee's Grasshopper component "HB Add Sub-face"
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
    new_face._user_data = None if _ref_face.user_data is None else _ref_face.user_data.copy()
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
    new_face._user_data = None if _ref_face.user_data is None else _ref_face.user_data.copy()
    new_face._properties._duplicate_extension_attr(_ref_face._properties)

    return new_face


def _create_new_Face3D(_poly2D: Polygon2D, _base_plane: Plane, _ref_face: TFaceOrShade) -> Face3D:
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


def face3Ds(_faces: Sequence[TFaceOrShade]) -> List[Face3D]:
    """Return a list of LBT-Face3Ds from a list of HB-Faces or HB-Shades."""
    return [f.geometry for f in _faces]


def merge_hb_faces(_faces: List[Face], _tolerance: float, _angle_tolerance_degrees: float) -> List[Face]:
    """Merge a group of HB-Faces into the fewest number of faces possible."""

    if not _faces:
        logger.debug("No faces in group. Skipping merge.")
        return []

    if len(_faces) == 1:
        logger.debug(f"Single face: {_faces[0].display_name} in group. Skipping merge.")
        return _faces

    # -------------------------------------------------------------------------
    # -- Before anything else, preserve any the Apertures for adding back in later
    apertures = []
    for f in _faces:
        apertures.extend([ap.duplicate() for ap in getattr(f, "apertures", [])])

    # -------------------------------------------------------------------------
    # -- Merge the HB-Faces' Polygons together
    merged_polygon2Ds = polygon2d_tools.merge_lbt_face_polygons(face3Ds(_faces), _tolerance)

    # -------------------------------------------------------------------------
    # -- Create new LBT-Face3D, and HB-Faces from the Polygon2Ds
    ref_face = _faces[0]
    ref_plane = ref_face.geometry.plane
    faces = []
    if len(merged_polygon2Ds) == 1:
        # -- Create new faces for the merged Polygon2Ds
        face3ds = (_create_new_Face3D(p, ref_plane, ref_face) for p in merged_polygon2Ds)
        faces = [_create_new_HB_Face(f3d, ref_face) for f3d in face3ds]
    elif len(merged_polygon2Ds) > 1:
        # -- It may mean that there are 'holes' in a surface? So try and find
        # -- the parent and any child surfaces.

        parent_polygon, child_polygons = find_parent_and_child_polygons(merged_polygon2Ds)

        # -- Check the results
        if len(parent_polygon) != 1:
            # -- Something went wrong, give up.
            _faces.append(ref_face)
            return _faces

        # -- If only 1 parent, lets make some Face3Ds and Faces
        parent_face_3d = [_create_new_Face3D(p, ref_plane, ref_face) for p in parent_polygon]
        child_face_3ds = [_create_new_Face3D(p, ref_plane, ref_face) for p in child_polygons]
        face_3ds = [Face3D.from_punched_geometry(parent_face_3d[0], child_face_3ds)]
        faces = [_create_new_HB_Face(f3d, ref_face) for f3d in face_3ds]

    # -------------------------------------------------------------------------
    # -- Add the apertures back in
    faces_with_apertures_: List[Face] = []
    for _face in faces:
        _check_and_add_sub_face(_face, apertures, _tolerance, _angle_tolerance_degrees)
        faces_with_apertures_.append(_face)

    return faces_with_apertures_


def merge_hb_shades(_faces: List[Shade], _tolerance: float, _angle_tolerance_degrees: float) -> List[Shade]:
    """Merge a group of HB-Shades into the fewest number of shades possible."""
    if not _faces:
        return []

    if len(_faces) == 1:
        return list(_faces)

    # -------------------------------------------------------------------------
    # -- Merge the HB-Face's Polygons together
    merged_polygon2Ds = polygon2d_tools.merge_lbt_face_polygons(face3Ds(_faces), _tolerance)

    # -------------------------------------------------------------------------
    # -- Create new LBT-Face3D, and HB-Faces from the Polygon2Ds
    ref_face = _faces[0]
    ref_plane = ref_face.geometry.plane
    hb_shades_ = []
    if len(merged_polygon2Ds) == 1:
        # -- Create new faces for the merged Polygon2Ds
        face3ds = (_create_new_Face3D(p, ref_plane, ref_face) for p in merged_polygon2Ds)
        hb_shades_ = [_create_new_HB_Shade(f3d, ref_face) for f3d in face3ds]
    elif len(merged_polygon2Ds) > 1:
        # -- It may mean that there are 'holes' in a surface? So try and find
        # -- the parent and any child surfaces.

        parent_polygon, child_polygons = find_parent_and_child_polygons(merged_polygon2Ds)

        # -- Check the results
        if len(parent_polygon) != 1:
            # -- Something went wrong, give up.
            _faces.append(ref_face)
            return _faces

        # -- If only 1 parent, lets make some Face3Ds and Faces
        parent_face_3d = [_create_new_Face3D(p, ref_plane, ref_face) for p in parent_polygon]
        child_face_3ds = [_create_new_Face3D(p, ref_plane, ref_face) for p in child_polygons]
        face_3ds = Face3D.from_punched_geometry(parent_face_3d[0], child_face_3ds)
        hb_shades_ = [_create_new_HB_Shade(f3d, ref_face) for f3d in face_3ds]

    return hb_shades_
