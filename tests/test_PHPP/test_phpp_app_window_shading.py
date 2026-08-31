# -*- Python Version: 3.10 -*-

"""Tests for PHPPConnection window-shading row construction and name matching."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from PHX.model import components, geometry
from PHX.PHPP.phpp_app import PHPPConnection, get_ap_element_from_dict


def _rect_polygon(_display_name: str = "") -> geometry.PhxPolygonRectangular:
    return geometry.PhxPolygonRectangular(
        _display_name=_display_name,
        _area=1.0,
        _center=geometry.PhxVertix(0.5, 0.5, 0.0),
        normal_vector=geometry.PhxVector(0.0, 0.0, 1.0),
        plane=geometry.PhxPlane(
            geometry.PhxVector(0, 0, 1),
            geometry.PhxVertix(0, 0, 0),
            geometry.PhxVector(1, 0, 0),
            geometry.PhxVector(0, 1, 0),
        ),
    )


def _aperture_element(
    _element_name: str = "",
    _polygon_name: str = "",
) -> components.PhxApertureElement:
    host_component = components.PhxComponentOpaque()
    aperture = components.PhxComponentAperture(_host=host_component)
    element = components.PhxApertureElement(_host=aperture)
    element.display_name = _element_name
    element.polygon = _rect_polygon(_polygon_name)
    aperture.add_elements((element,))
    host_component.add_aperture(aperture)
    return element


def _project_with(*elements: components.PhxApertureElement) -> SimpleNamespace:
    opaque_components = [element.host.host for element in elements]
    return SimpleNamespace(variants=[SimpleNamespace(building=SimpleNamespace(opaque_components=opaque_components))])


def _connection(window_names: list[str]) -> PHPPConnection:
    connection = object.__new__(PHPPConnection)
    connection.shape = SimpleNamespace(SHADING=object())
    connection.windows = SimpleNamespace(get_all_window_names=Mock(return_value=window_names))
    connection.shading = SimpleNamespace(write_shading=Mock())
    return connection


# -----------------------------------------------------------------------------
# -- get_ap_element_from_dict


def test_lookup_string_name() -> None:
    element = _aperture_element("W-101")
    assert get_ap_element_from_dict("W-101", {"W-101": element}) is element


def test_lookup_numeric_name_read_back_as_float() -> None:
    # Excel converts a numeric-cell name '106' to 106.0 on read-back
    element = _aperture_element("106")
    assert get_ap_element_from_dict("106.0", {"106": element}) is element


def test_lookup_float_name_read_back_as_int() -> None:
    element = _aperture_element("106.0")
    assert get_ap_element_from_dict("106", {"106.0": element}) is element


def test_lookup_missing_numeric_name_raises_key_error() -> None:
    with pytest.raises(KeyError, match="'100'.*not found in the PHX-Model"):
        get_ap_element_from_dict("100", {"W-101": _aperture_element("W-101")})


def test_lookup_missing_non_numeric_name_raises_key_error_not_value_error() -> None:
    with pytest.raises(KeyError, match="'W-999'.*not found in the PHX-Model"):
        get_ap_element_from_dict("W-999", {"W-101": _aperture_element("W-101")})


# -----------------------------------------------------------------------------
# -- PHPPConnection.write_project_window_shading


def test_write_shading_matches_unnamed_apertures_by_polygon_id_fallback() -> None:
    # An aperture with no display-name: the Windows sheet gets the polygon's
    # display-name (which falls back to the polygon id-number, e.g. '100'), so
    # the shading write-back must key on that same name.
    element = _aperture_element(_element_name="", _polygon_name="")
    element.winter_shading_factor = 0.5
    element.summer_shading_factor = 0.25

    assert element.polygon is not None
    sheet_name = element.polygon.display_name
    assert sheet_name == str(element.polygon.id_num)

    connection = _connection(window_names=[sheet_name])
    connection.write_project_window_shading(_project_with(element))

    (rows,) = connection.shading.write_shading.call_args.args
    assert len(rows) == 1
    assert rows[0].winter_shading_factor == 0.5
    assert rows[0].summer_shading_factor == 0.25


def test_write_shading_matches_named_numeric_apertures() -> None:
    element = _aperture_element(_element_name="100", _polygon_name="100")
    connection = _connection(window_names=["100"])
    connection.write_project_window_shading(_project_with(element))

    (rows,) = connection.shading.write_shading.call_args.args
    assert len(rows) == 1


def test_write_shading_skips_elements_without_polygons() -> None:
    # Elements with no polygon are never written to the Windows sheet, so they
    # must be excluded from the shading name-lookup as well.
    element = _aperture_element(_element_name="100", _polygon_name="100")
    no_polygon_element = _aperture_element(_element_name="200")
    no_polygon_element.polygon = None

    connection = _connection(window_names=["100"])
    connection.write_project_window_shading(_project_with(element, no_polygon_element))

    (rows,) = connection.shading.write_shading.call_args.args
    assert len(rows) == 1
