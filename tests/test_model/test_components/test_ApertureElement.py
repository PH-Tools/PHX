from PHX.model import components, constructions, geometry


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


def _aperture_with_type_psi(psi: float) -> components.PhxComponentAperture:
    win_type = constructions.PhxConstructionWindow()
    win_type.set_all_frames_psi_install(psi)
    c = components.PhxComponentOpaque()
    ap = components.PhxComponentAperture(_host=c)
    ap.window_type = win_type
    return ap


def test_aperture_element_resolved_psi_install_falls_back_to_window_type() -> None:
    ap = _aperture_with_type_psi(0.04)
    ap_el = components.PhxApertureElement(_host=ap)

    assert ap_el.install_psi is None
    assert ap_el.resolved_psi_install.values == (0.04, 0.04, 0.04, 0.04)


def test_aperture_element_resolved_psi_install_uses_own_values_when_set() -> None:
    ap = _aperture_with_type_psi(0.04)
    ap_el = components.PhxApertureElement(_host=ap)
    ap_el.install_psi = components.PhxApertureElementPsiInstall(top=0.1, right=0.04, bottom=0.0, left=0.04)

    assert ap_el.resolved_psi_install.values == (0.1, 0.04, 0.0, 0.04)
    # -- the window-type is untouched
    assert ap.window_type.frame_top.psi_install == 0.04


def test_psi_install_unique_key_is_stable_and_content_keyed() -> None:
    a = components.PhxApertureElementPsiInstall(top=0.1, right=0.04, bottom=0.0, left=0.04)
    b = components.PhxApertureElementPsiInstall(top=0.1, right=0.04, bottom=0.0, left=0.04)
    c = components.PhxApertureElementPsiInstall(top=0.1, right=0.04, bottom=0.0, left=0.05)

    assert a.unique_key == b.unique_key
    assert a.unique_key != c.unique_key
    assert a.unique_key == "psi(0.1000,0.0400,0.0000,0.0400)"


def test_aperture_elements_with_different_psi_are_not_equivalent() -> None:
    ap = _aperture_with_type_psi(0.04)
    ap_el_1 = components.PhxApertureElement(_host=ap)
    ap_el_2 = components.PhxApertureElement(_host=ap)

    assert ap_el_1.is_equivalent(ap_el_2)

    ap_el_2.install_psi = components.PhxApertureElementPsiInstall(top=0.04, right=0.04, bottom=0.04, left=0.0)
    assert not ap_el_1.is_equivalent(ap_el_2)

    # -- equal values (even if one is explicit and one inherited) ARE equivalent
    ap_el_2.install_psi = components.PhxApertureElementPsiInstall(top=0.04, right=0.04, bottom=0.04, left=0.04)
    assert ap_el_1.is_equivalent(ap_el_2)
