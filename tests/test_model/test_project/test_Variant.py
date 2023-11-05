from PHX.model import project, building


def test_blank_variant(reset_class_counters):
    assert project.PhxVariant._count == 0
    var = project.PhxVariant()

    assert str(var)
    assert not var.graphics3D
    assert not var.building
    assert not var.default_mech_collection.devices
    assert not var.default_mech_collection.ventilation_devices
    assert not var.default_mech_collection.space_heating_devices
    assert not var.default_mech_collection.heat_pump_devices
    assert not var.default_mech_collection.dhw_heating_devices
    assert not var.default_mech_collection.dhw_tank_devices
    assert not var.default_mech_collection.dhw_distribution_piping_segments
    assert not var.default_mech_collection.dhw_distribution_piping_segments_by_diam
    assert not var.default_mech_collection.dhw_recirc_piping
    assert not var.default_mech_collection.dhw_recirc_piping_segments_by_diam
    assert not var.default_mech_collection.supportive_devices
    assert var.id_num == 1
    assert project.PhxVariant._count == 1


def test_variant_with_zone(reset_class_counters):
    var = project.PhxVariant()
    assert not var.zones

    z = building.PhxZone()
    var.building.add_zones(z)

    assert z in var.zones
