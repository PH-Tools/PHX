from PHX.model import project, building


def test_blank_variant(reset_class_counters):
    assert project.PhxVariant._count == 0
    var = project.PhxVariant()

    assert str(var)
    assert not var.graphics3D
    assert not var.building
    assert not var.mech_systems.devices
    assert not var.mech_systems.ventilation_devices
    assert not var.mech_systems.space_heating_devices
    assert not var.mech_systems.cooling_devices
    assert not var.mech_systems.dhw_heating_devices
    assert not var.mech_systems.dhw_tank_devices
    assert not var.mech_systems.dhw_distribution_piping_segments
    assert not var.mech_systems.dhw_distribution_piping_segments_by_diam
    assert not var.mech_systems.dhw_recirc_piping
    assert not var.mech_systems.dhw_recirc_piping_segments_by_diam
    assert not var.mech_systems.supportive_devices
    assert var.id_num == 1
    assert project.PhxVariant._count == 1


def test_variant_with_zone(reset_class_counters):
    var = project.PhxVariant()
    assert not var.zones

    z = building.PhxZone()
    var.building.add_zones(z)

    assert z in var.zones
