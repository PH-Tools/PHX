import pytest

from PHX.model.enums.hvac import PhxExhaustVentType
from PHX.model.hvac import ventilation


def test_add_default_PhxVentilatorParams(reset_class_counters):
    p1 = ventilation.PhxDeviceVentilatorParams()
    p2 = ventilation.PhxDeviceVentilatorParams()

    p3 = p1 + p2

    assert p3.sensible_heat_recovery == p1.sensible_heat_recovery
    assert p3.latent_heat_recovery == p1.latent_heat_recovery
    assert p3.quantity == 2
    assert p3.electric_efficiency == p1.electric_efficiency
    assert p3.frost_protection_reqd == p1.frost_protection_reqd
    assert p3.temperature_below_defrost_used == p1.temperature_below_defrost_used


def test_add_mixed_PhxVentilatorParams(reset_class_counters):
    p1 = ventilation.PhxDeviceVentilatorParams(
        _sensible_heat_recovery=10,
        _latent_heat_recovery=10,
        _quantity=2,
        _electric_efficiency=4,
        _frost_protection_reqd=True,
        _temperature_below_defrost_used=-5.0,
    )
    p2 = ventilation.PhxDeviceVentilatorParams(
        _sensible_heat_recovery=20,
        _latent_heat_recovery=20,
        _quantity=3,
        _electric_efficiency=2,
        _frost_protection_reqd=False,
        _temperature_below_defrost_used=5.0,
    )
    p3 = p1 + p2
    assert p1 != p2 != p3
    assert p3.sensible_heat_recovery == 15
    assert p3.latent_heat_recovery == 15
    assert p3.quantity == 5
    assert p3.electric_efficiency == 3
    assert p3.frost_protection_reqd
    assert p3.temperature_below_defrost_used == 0.0


def test_default_PhxVentilator(reset_class_counters):
    p1 = ventilation.PhxDeviceVentilator()
    p2 = ventilation.PhxDeviceVentilator()

    assert p1.id_num == 1
    assert p2.id_num == 2


def test__PhxVentilator_params(reset_class_counters):
    d1 = ventilation.PhxDeviceVentilator()
    d1.params.quantity = 1
    d2 = ventilation.PhxDeviceVentilator()
    d2.params.quantity = 12

    assert d1.params != d2.params
    assert d1.params.quantity != d2.params.quantity


def test_add_default_PhxVentilator(reset_class_counters):
    p1 = ventilation.PhxDeviceVentilator()
    p2 = ventilation.PhxDeviceVentilator()

    p3 = p1 + p2

    assert p1 != p2 != p3


def test_add_mixed_PhxVentilator(reset_class_counters):
    d1 = ventilation.PhxDeviceVentilator()
    d1.params = ventilation.PhxDeviceVentilatorParams(
        _sensible_heat_recovery=10,
        _latent_heat_recovery=10,
        _quantity=2,
        _electric_efficiency=4,
        _frost_protection_reqd=True,
        _temperature_below_defrost_used=-5.0,
    )
    d2 = ventilation.PhxDeviceVentilator()
    d2.params = ventilation.PhxDeviceVentilatorParams(
        _sensible_heat_recovery=20,
        _latent_heat_recovery=20,
        _quantity=3,
        _electric_efficiency=2,
        _frost_protection_reqd=False,
        _temperature_below_defrost_used=5.0,
    )

    d3 = d1 + d2

    assert d1 != d2 != d3
    assert d3.params.sensible_heat_recovery == 15
    assert d3.params.latent_heat_recovery == 15
    assert d3.params.quantity == 5
    assert d3.params.electric_efficiency == 3
    assert d3.params.frost_protection_reqd
    assert d3.params.temperature_below_defrost_used == 0.0


# -----------------------------------------------------------------------------
# Exhaust


def test_range_hood(reset_class_counters):
    o1 = ventilation.PhxExhaustVentilatorRangeHood()
    assert o1.params.exhaust_type == PhxExhaustVentType.KITCHEN_HOOD
    assert str(o1)


def test_add_error(reset_class_counters):
    o1 = ventilation.PhxExhaustVentilatorRangeHood()
    o2 = ventilation.PhxExhaustVentilatorDryer()

    with pytest.raises(Exception):
        o1 + o2


def test_add_range_hoods(reset_class_counters):
    o1 = ventilation.PhxExhaustVentilatorRangeHood()
    o1.params.exhaust_flow_rate_m3h = 300

    o2 = ventilation.PhxExhaustVentilatorRangeHood()
    o2.params.exhaust_flow_rate_m3h = 450

    o3 = o1 + o2
    assert o3.params.exhaust_flow_rate_m3h == 750


def test_dryer(reset_class_counters):
    o1 = ventilation.PhxExhaustVentilatorDryer()
    assert o1.params.exhaust_type == PhxExhaustVentType.DRYER
    assert str(o1)


def test_add_dryers(reset_class_counters):
    o1 = ventilation.PhxExhaustVentilatorDryer()
    o1.params.exhaust_flow_rate_m3h = 300

    o2 = ventilation.PhxExhaustVentilatorDryer()
    o2.params.exhaust_flow_rate_m3h = 450

    o3 = o1 + o2
    assert o3.params.exhaust_flow_rate_m3h == 750


def test_user_determined(reset_class_counters):
    o1 = ventilation.PhxExhaustVentilatorUserDefined()
    assert o1.params.exhaust_type == PhxExhaustVentType.USER_DEFINED
    assert str(o1)


def test_add_user_determined(reset_class_counters):
    o1 = ventilation.PhxExhaustVentilatorUserDefined()
    o1.params.exhaust_flow_rate_m3h = 450
    o1.params.annual_runtime_minutes = 50

    o2 = ventilation.PhxExhaustVentilatorUserDefined()
    o2.params.exhaust_flow_rate_m3h = 200
    o2.params.annual_runtime_minutes = 40

    o3 = o1 + o2
    assert o3.params.exhaust_flow_rate_m3h == 650
    assert o3.params.annual_runtime_minutes == pytest.approx(46.92307)
