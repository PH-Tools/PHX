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
