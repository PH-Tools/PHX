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

