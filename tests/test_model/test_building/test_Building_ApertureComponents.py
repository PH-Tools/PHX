from PHX.model import building, components


def test_building_with_no_apertures(reset_class_counters) -> None:
    b1 = building.PhxBuilding()
    wall_compo = components.PhxComponentOpaque()
    b1.add_component(wall_compo)

    assert len(b1.aperture_components) == 0


def test_building_with_single_aperture_in_single_component(reset_class_counters) -> None:
    """This is the simplest scenario: a single Aperture 'in' a single opaque component"""

    b1 = building.PhxBuilding()
    c1 = components.PhxComponentOpaque()
    c2 = components.PhxComponentOpaque()
    c3 = components.PhxComponentOpaque()
    b1.add_components([c1, c2, c3])
    ap = components.PhxComponentAperture(_host=c1)
    ap_el = components.PhxApertureElement(_host=ap)
    ap.add_element(ap_el)
    c1.add_aperture(ap)

    assert len(b1.aperture_components) == 1


def test_building_with_single_aperture_in_multiple_components(
    reset_class_counters,
) -> None:
    """A single Aperture might be have Elements 'in' multiple opaque components."""

    b1 = building.PhxBuilding()
    c1 = components.PhxComponentOpaque()
    c2 = components.PhxComponentOpaque()
    c3 = components.PhxComponentOpaque()
    b1.add_components([c1, c2, c3])
    ap = components.PhxComponentAperture(_host=c1)
    ap_el = components.PhxApertureElement(_host=ap)
    ap.add_element(ap_el)
    c1.add_aperture(ap)
    c2.add_aperture(ap)

    # Even when the Aperture had elements on multiple components
    # there is still only 'one' of the aperture
    assert len(b1.aperture_components) == 1
