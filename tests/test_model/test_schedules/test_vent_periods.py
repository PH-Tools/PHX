import pytest

from PHX.model.schedules import ventilation


def test_default_vent_util_period(reset_class_counters):
    o = ventilation.Vent_UtilPeriods()
    assert o.high.period_operating_hours == 0
    assert o.high.period_operation_speed == 0
    assert o.standard.period_operating_hours == 0
    assert o.standard.period_operation_speed == 0
    assert o.basic.period_operating_hours == 0
    assert o.basic.period_operation_speed == 0
    assert o.minimum.period_operating_hours == 0
    assert o.minimum.period_operation_speed == 0


def test_custom_vent_util_periods(reset_class_counters):
    o = ventilation.Vent_UtilPeriods(
        high=ventilation.Vent_OperatingPeriod(10, 0.98),
        standard=ventilation.Vent_OperatingPeriod(10, 0.77),
        basic=ventilation.Vent_OperatingPeriod(2, 0.50),
        minimum=ventilation.Vent_OperatingPeriod(2, 0.24),
    )
    assert o


def test_add_vent_util_period_same(reset_class_counters) -> None:
    o1 = ventilation.Vent_UtilPeriods(
        high=ventilation.Vent_OperatingPeriod(10, 0.98),
        standard=ventilation.Vent_OperatingPeriod(10, 0.77),
        basic=ventilation.Vent_OperatingPeriod(2, 0.50),
        minimum=ventilation.Vent_OperatingPeriod(2, 0.24),
    )
    o2 = ventilation.Vent_UtilPeriods(
        high=ventilation.Vent_OperatingPeriod(10, 0.98),
        standard=ventilation.Vent_OperatingPeriod(10, 0.77),
        basic=ventilation.Vent_OperatingPeriod(2, 0.50),
        minimum=ventilation.Vent_OperatingPeriod(2, 0.24),
    )

    o3 = o1 + o2
    assert o3.high.period_operating_hours == 10
    assert o3.high.period_operation_speed == 0.98
    assert o3.standard.period_operating_hours == 10
    assert o3.standard.period_operation_speed == 0.77
    assert o3.basic.period_operating_hours == 2
    assert o3.basic.period_operation_speed == 0.50
    assert o3.minimum.period_operating_hours == 2
    assert o3.minimum.period_operation_speed == 0.24


def test_add_vent_util_period_different(reset_class_counters) -> None:
    o1 = ventilation.Vent_UtilPeriods(
        high=ventilation.Vent_OperatingPeriod(10, 1.0),
        standard=ventilation.Vent_OperatingPeriod(10, 0.80),
        basic=ventilation.Vent_OperatingPeriod(8, 0.50),
        minimum=ventilation.Vent_OperatingPeriod(8, 1.0),
    )
    o2 = ventilation.Vent_UtilPeriods(
        high=ventilation.Vent_OperatingPeriod(20, 0.5),
        standard=ventilation.Vent_OperatingPeriod(20, 0.40),
        basic=ventilation.Vent_OperatingPeriod(4, 0.0),
        minimum=ventilation.Vent_OperatingPeriod(4, 0.0),
    )

    o3 = o1 + o2
    assert o3.high.period_operating_hours == 15
    assert o3.high.period_operation_speed == pytest.approx(0.75)
    assert o3.standard.period_operating_hours == 15
    assert o3.standard.period_operation_speed == pytest.approx(0.60)
    assert o3.basic.period_operating_hours == 6
    assert o3.basic.period_operation_speed == pytest.approx(0.25)
    assert o3.minimum.period_operating_hours == 6
    assert o3.minimum.period_operation_speed == pytest.approx(0.5)
