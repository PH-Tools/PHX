from PHX.model.hvac import _base


def test_PhxUsageProfile_add(reset_class_counters):
    use_1 = _base.PhxUsageProfile(0, 0, 0, 1.0, 1.0, 0)
    use_2 = _base.PhxUsageProfile(0, 0, 1.0, 1.0, 0, 0)

    use_3 = use_1 + use_2
    assert use_3 != use_2 != use_1
    assert not use_3.space_heating
    assert not use_3.dhw_heating
    assert use_3.cooling
    assert use_3.ventilation
    assert use_3.humidification
    assert not use_3.dehumidification


def test_add_default_PhxMechEquipmentParams(reset_class_counters):
    p1 = _base.PhxMechanicalDeviceParams()
    p2 = _base.PhxMechanicalDeviceParams()

    p3 = p1 + p2
    assert p3.aux_energy is None
    assert p3.aux_energy_dhw is None
    assert p3.solar_fraction is None
    assert p3.in_conditioned_space


def test_r_add_default_PhxMechEquipmentParams(reset_class_counters):
    p1 = _base.PhxMechanicalDeviceParams()
    p2 = _base.PhxMechanicalDeviceParams()

    p3 = p1.__radd__(p2)
    assert p3.aux_energy is None
    assert p3.aux_energy_dhw is None
    assert p3.solar_fraction is None
    assert p3.in_conditioned_space

    p4 = p2.__radd__(p1)
    assert p4.aux_energy is None
    assert p4.aux_energy_dhw is None
    assert p4.solar_fraction is None
    assert p4.in_conditioned_space


def test_sum_default_PhxMechEquipmentParams(reset_class_counters):
    p1 = _base.PhxMechanicalDeviceParams()
    p2 = _base.PhxMechanicalDeviceParams()

    p3: _base.PhxMechanicalDeviceParams = sum([p1, p2])
    assert p3.aux_energy is None
    assert p3.aux_energy_dhw is None
    assert p3.solar_fraction is None
    assert p3.in_conditioned_space


def test_add_mixed_PhxMechEquipmentParams(reset_class_counters):
    p1 = _base.PhxMechanicalDeviceParams(
        aux_energy=12,
        aux_energy_dhw=0.4,
        solar_fraction=None,
        in_conditioned_space=False,
    )
    p2 = _base.PhxMechanicalDeviceParams(
        aux_energy=None,
        aux_energy_dhw=0.4,
        solar_fraction=13,
        in_conditioned_space=True,
    )

    p3 = p1 + p2
    assert p3.aux_energy == 12
    assert p3.aux_energy_dhw == 0.8
    assert p3.solar_fraction == 13
    assert p3.in_conditioned_space


def test_PhxMechanicalEquipment(reset_class_counters):
    mech_equip_1 = _base.PhxMechanicalDevice()
    mech_equip_2 = _base.PhxMechanicalDevice()

    assert mech_equip_1 != mech_equip_2
    assert mech_equip_1.id_num == 1
    assert mech_equip_2.id_num == 2


def test_add_default_PhxMechanicalEquipment(reset_class_counters):
    mech_equip_1 = _base.PhxMechanicalDevice()
    mech_equip_2 = _base.PhxMechanicalDevice()

    mech_equip_3 = mech_equip_1 + mech_equip_2
    assert mech_equip_3 != mech_equip_1 != mech_equip_2

    mech_equip_4 = sum([mech_equip_1, mech_equip_2])
    assert mech_equip_4 != mech_equip_1 != mech_equip_2


def test_r_add_default_PhxMechanicalEquipment(reset_class_counters):
    mech_equip_1 = _base.PhxMechanicalDevice()
    mech_equip_2 = _base.PhxMechanicalDevice()

    mech_equip_3 = mech_equip_1.__radd__(mech_equip_2)
    assert mech_equip_3 != mech_equip_1 != mech_equip_2


def test_add_mixed_PhxMechanicalEquipment(reset_class_counters):
    mech_equip_1 = _base.PhxMechanicalDevice(
        _quantity=1,
        unit=0.5,
        percent_coverage=0.25,
        usage_profile=_base.PhxUsageProfile(False, False, False, True, False, False),
    )
    mech_equip_2 = _base.PhxMechanicalDevice(
        _quantity=9,
        unit=0.25,
        percent_coverage=0.75,
        usage_profile=_base.PhxUsageProfile(True, False, False, False, False, True),
    )

    mech_equip_3 = mech_equip_1 + mech_equip_2
    assert mech_equip_3 != mech_equip_1 != mech_equip_2
    assert mech_equip_3.quantity == 10
    assert mech_equip_3.unit == 0.75
    assert mech_equip_3.percent_coverage == 1.0
    assert mech_equip_3.usage_profile.space_heating
    assert not mech_equip_3.usage_profile.dhw_heating
    assert not mech_equip_3.usage_profile.cooling
    assert mech_equip_3.usage_profile.ventilation
    assert not mech_equip_3.usage_profile.humidification
    assert mech_equip_3.usage_profile.dehumidification

    mech_equip_4: _base.PhxMechanicalDevice = sum([mech_equip_1, mech_equip_2])
    assert mech_equip_4 != mech_equip_1 != mech_equip_2
    assert mech_equip_4.quantity == 10
    assert mech_equip_4.unit == 0.75
    assert mech_equip_4.percent_coverage == 1.0
    assert mech_equip_4.usage_profile.space_heating
    assert not mech_equip_4.usage_profile.dhw_heating
    assert not mech_equip_4.usage_profile.cooling
    assert mech_equip_4.usage_profile.ventilation
    assert not mech_equip_4.usage_profile.humidification
    assert mech_equip_4.usage_profile.dehumidification
