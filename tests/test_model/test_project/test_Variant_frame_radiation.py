"""Tests for the area-weighted window-frame radiation properties on PhxVariant.

These collapse the per-frame `solar_absorptance` / `thermal_emissivity` values to the
single project-wide PHPP "Radiation balance window frames" pair (Areas!AI40 / AJ40).
"""

from PHX.model import components, constructions, geometry, project


def _make_aperture(_width: float, _height: float, _frame_width: float = 0.1) -> components.PhxComponentAperture:
    """Return an aperture with a single rectangular sash of the given size."""
    win_type = constructions.PhxConstructionWindow()
    for frame in win_type.frames:
        frame.width = _frame_width

    host = components.PhxComponentOpaque()
    ap = components.PhxComponentAperture(_host=host)
    ap.window_type = win_type

    ap_el = components.PhxApertureElement(_host=ap)
    ap_el.polygon = geometry.PhxPolygonRectangular(
        _display_name="no_name",
        _area=_width * _height,
        _center=geometry.PhxVertix(_width / 2, _height / 2, 0.0),
        normal_vector=geometry.PhxVector(0.0, 0.0, 1.0),
        plane=geometry.PhxPlane(
            geometry.PhxVector(0, 0, 1),
            geometry.PhxVertix(0, 0, 0),
            geometry.PhxVector(1, 0, 0),
            geometry.PhxVector(0, 1, 0),
        ),
    )
    ap_el.polygon.vertix_lower_left = geometry.PhxVertix(0, 0, 0)
    ap_el.polygon.vertix_lower_right = geometry.PhxVertix(_width, 0, 0)
    ap_el.polygon.vertix_upper_right = geometry.PhxVertix(_width, _height, 0)
    ap_el.polygon.vertix_upper_left = geometry.PhxVertix(0, _height, 0)
    ap.add_element(ap_el)
    host.add_aperture(ap)
    return ap


def test_frame_element_default_radiation_properties() -> None:
    frame = constructions.PhxWindowFrameElement()
    assert frame.solar_absorptance == constructions.PHPP_DEFAULT_FRAME_SOLAR_ABSORPTANCE == 0.25
    assert frame.thermal_emissivity == constructions.PHPP_DEFAULT_FRAME_THERMAL_EMISSIVITY == 0.6


def test_empty_variant_returns_phpp_defaults(reset_class_counters) -> None:
    variant = project.PhxVariant()
    assert variant.window_frame_solar_absorptance == 0.25
    assert variant.window_frame_thermal_emissivity == 0.6


def test_uniform_frames_return_the_single_value(reset_class_counters) -> None:
    ap = _make_aperture(2.0, 3.0)
    for frame in ap.window_type.frames:
        frame.solar_absorptance = 0.45
        frame.thermal_emissivity = 0.72

    variant = project.PhxVariant()
    variant.building.add_component(ap.host)

    assert round(variant.window_frame_solar_absorptance, 6) == 0.45
    assert round(variant.window_frame_thermal_emissivity, 6) == 0.72


def test_area_weighted_average_across_sides(reset_class_counters) -> None:
    # 2m wide x 3m tall sash, 0.1m frames. Corner squares go to top/bottom:
    #   top/bottom area = 2.0 * 0.1 = 0.2 each
    #   left/right area = (3.0 - 0.2) * 0.1 = 0.28 each
    ap = _make_aperture(2.0, 3.0)
    ap.window_type.frame_top.solar_absorptance = 0.9
    ap.window_type.frame_bottom.solar_absorptance = 0.1
    ap.window_type.frame_left.solar_absorptance = 0.5
    ap.window_type.frame_right.solar_absorptance = 0.5

    variant = project.PhxVariant()
    variant.building.add_component(ap.host)

    # (0.2*0.9 + 0.2*0.1 + 0.28*0.5 + 0.28*0.5) / (0.2 + 0.2 + 0.28 + 0.28) = 0.48 / 0.96
    assert round(variant.window_frame_solar_absorptance, 6) == 0.5


def test_area_weighted_across_multiple_apertures(reset_class_counters) -> None:
    # A big dark window should dominate a small light one.
    big = _make_aperture(4.0, 4.0)
    for frame in big.window_type.frames:
        frame.solar_absorptance = 0.8
    small = _make_aperture(1.0, 1.0)
    for frame in small.window_type.frames:
        frame.solar_absorptance = 0.2

    variant = project.PhxVariant()
    variant.building.add_component(big.host)
    variant.building.add_component(small.host)

    result = variant.window_frame_solar_absorptance
    # Weighted toward the larger (dark) window, strictly between the two inputs.
    assert 0.2 < result < 0.8
    assert result > 0.5
