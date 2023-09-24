from PHX.model import components, geometry, constructions


def test_default_aperture_element() -> None:
    c = components.PhxComponentOpaque()
    ap = components.PhxComponentAperture(_host=c)
    ap_el = components.PhxApertureElement(_host=ap)

    assert ap_el.host == ap


def test_aperture_element_with_rect_polygon() -> None:
    frame_type = constructions.PhxWindowFrameElement(width=0.1)
    win_type = constructions.PhxConstructionWindow()
    win_type.frame_top = frame_type
    win_type.frame_right = frame_type
    win_type.frame_bottom = frame_type
    win_type.frame_left = frame_type

    c = components.PhxComponentOpaque()
    ap = components.PhxComponentAperture(_host=c)
    ap.window_type = win_type
    ap_el = components.PhxApertureElement(_host=ap)

    ap_el.polygon = geometry.PhxPolygonRectangular(
        _display_name="no_name",
        _area=2.0,
        _center=geometry.PhxVertix(0.5, 1.0, 0.0),
        normal_vector=geometry.PhxVector(0.0, 0.0, 1.0),
        plane=geometry.PhxPlane(
            geometry.PhxVector(0, 0, 1),
            geometry.PhxVertix(1, 1, 0),
            geometry.PhxVector(1, 0, 0),
            geometry.PhxVector(0, 1, 0),
        ),
    )

    ap_el.polygon.vertix_lower_left = geometry.PhxVertix(0, 0, 0)
    ap_el.polygon.vertix_lower_right = geometry.PhxVertix(1, 0, 0)
    ap_el.polygon.vertix_upper_right = geometry.PhxVertix(1, 2, 0)
    ap_el.polygon.vertix_upper_left = geometry.PhxVertix(0, 2, 0)

    assert ap_el.polygon.area == 2.0
    assert ap_el.area == 2.0
    assert ap_el.height == 2.0
    assert ap_el.width == 1.0
    assert ap_el.frame_factor == 0.28
    assert ap_el.frame_area == 0.56
    assert ap_el.glazing_factor == 0.72
    assert ap_el.glazing_area == 1.44
