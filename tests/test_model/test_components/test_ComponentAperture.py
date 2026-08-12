from PHX.model import components, constructions


def test_default_component_aperture(reset_class_counters) -> None:
    c1 = components.PhxComponentOpaque()
    ap1 = components.PhxComponentAperture(_host=c1)
    ap2 = components.PhxComponentAperture(_host=c1)
    c1.add_aperture(ap1)
    c1.add_aperture(ap2)

    assert c1.id_num == 1
    assert ap1.id_num == 2
    assert ap2.id_num == 3
    assert id(ap1) != id(ap2)

    assert len(ap1.polygon_ids) == 0
    assert len(ap2.polygon_ids) == 0


def test_reset_aperture_construction(reset_class_counters):
    """Since a single Aperture can be in multiple opaque-components,
    resetting the Construction on any one should re-set it for all.
    """

    c1 = components.PhxComponentOpaque()
    c2 = components.PhxComponentOpaque()
    ap1 = components.PhxComponentAperture(_host=c1)
    c1.add_aperture(ap1)
    c2.add_aperture(ap1)

    new_const = constructions.PhxConstructionWindow()
    ap1.window_type = new_const

    for ap in c1.apertures:
        assert ap.window_type == new_const

    for ap in c2.apertures:
        assert ap.window_type == new_const


def test_apertures_with_different_element_psi_do_not_share_unique_key(reset_class_counters):
    """Two apertures, same window-type, different resolved psi -> different unique_key (no merge)."""
    win_type = constructions.PhxConstructionWindow()
    win_type.set_all_frames_psi_install(0.04)

    c = components.PhxComponentOpaque()
    ap1 = components.PhxComponentAperture(_host=c)
    ap1.window_type = win_type
    el1 = components.PhxApertureElement(_host=ap1)
    ap1.add_element(el1)

    ap2 = components.PhxComponentAperture(_host=c)
    ap2.window_type = win_type
    el2 = components.PhxApertureElement(_host=ap2)
    ap2.add_element(el2)

    assert ap1.unique_key == ap2.unique_key

    el2.install_psi = components.PhxApertureElementPsiInstall(top=0.04, right=0.04, bottom=0.04, left=0.0)
    assert ap1.unique_key != ap2.unique_key

    # -- explicit values equal to the type's values keep the same key (no-op invariant)
    el2.install_psi = components.PhxApertureElementPsiInstall(top=0.04, right=0.04, bottom=0.04, left=0.04)
    assert ap1.unique_key == ap2.unique_key
