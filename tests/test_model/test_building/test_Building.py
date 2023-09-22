from PHX.model import building, components, spaces


def test_default_Building(reset_class_counters):
    b1 = building.PhxBuilding()
    b2 = building.PhxBuilding()

    assert id(b1) != id(b2)
    assert not b1
    assert not b2
    assert not b1.opaque_components
    assert not b2.opaque_components
    assert not b1.zones
    assert not b2.zones


def test_add_single_component(reset_class_counters):
    b = building.PhxBuilding()
    c1 = components.PhxComponentOpaque()
    b.add_components(c1)

    assert b
    assert b._components
    assert len(b._components) == 1
    assert c1 in b._components


def test_add_multiple_components(reset_class_counters):
    b = building.PhxBuilding()
    c1 = components.PhxComponentOpaque()
    c2 = components.PhxComponentOpaque()
    b.add_components([c1, c2])

    assert b
    assert b._components
    assert len(b._components) == 2
    assert c1 in b._components
    assert c2 in b._components


def test_add_single_zone(reset_class_counters):
    b = building.PhxBuilding()
    z1 = building.PhxZone()
    b.add_zones(z1)

    assert b
    assert b.zones
    assert len(b.zones) == 1
    assert z1 in b.zones


def test_add_multiple_zones(reset_class_counters):
    b = building.PhxBuilding()
    z1 = building.PhxZone()
    z2 = building.PhxZone()
    b.add_zones([z1, z2])

    assert b
    assert b.zones
    assert len(b.zones) == 2
    assert z1 in b.zones
    assert z2 in b.zones


def test_group_compos_by_assembly_with_single_compo(reset_class_counters):
    b = building.PhxBuilding()
    c1 = components.PhxComponentOpaque()
    b.add_components(c1)
    b.merge_opaque_components_by_assembly()

    assert b
    assert b._components
    assert len(b._components) == 1
    assert c1 in b._components


def test_zones_with_ventilation(reset_class_counters) -> None:
    z = building.PhxZone()

    sp1 = spaces.PhxSpace()
    sp1.ventilation.load.flow_extract = 0
    sp1.ventilation.load.flow_supply = 0
    sp1.ventilation.load.flow_transfer = 0
    z.spaces.append(sp1)

    sp2 = spaces.PhxSpace()
    sp2.ventilation.load.flow_extract = 1
    sp2.ventilation.load.flow_supply = 1
    sp2.ventilation.load.flow_transfer = 1
    z.spaces.append(sp2)

    sp3 = spaces.PhxSpace()
    sp3.ventilation.load.flow_extract = 1
    sp3.ventilation.load.flow_supply = 1
    sp3.ventilation.load.flow_transfer = 1
    z.spaces.append(sp3)

    assert len(z.spaces_with_ventilation) == 2
    assert sp1 not in z.spaces_with_ventilation
    assert sp2 in z.spaces_with_ventilation
    assert sp3 in z.spaces_with_ventilation
