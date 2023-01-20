from PHX.model.schedules import ventilation


def test_vent_schedule_empty(reset_class_counters):
    obj_1 = ventilation.PhxScheduleVentilation()
    assert obj_1.id_num == 1
    obj_2 = ventilation.PhxScheduleVentilation()
    assert obj_2.id_num == 2
    assert obj_1 != obj_2


def test_vent_schedule_empty_force_24(reset_class_counters):
    obj = ventilation.PhxScheduleVentilation()
    obj.force_max_utilization_hours()
    assert obj.operating_periods.high.period_operating_hours == 24


def test_vent_schedule_custom(reset_class_counters):
    obj = ventilation.PhxScheduleVentilation(
        operating_periods=ventilation.Vent_UtilPeriods(
            high=ventilation.Vent_OperatingPeriod(10, 0.98),
            standard=ventilation.Vent_OperatingPeriod(10, 0.77),
            basic=ventilation.Vent_OperatingPeriod(2, 0.50),
            minimum=ventilation.Vent_OperatingPeriod(2, 0.24),
        )
    )
    obj.force_max_utilization_hours()
    assert obj
    assert obj.operating_periods.high.period_operating_hours == 10


def test_vent_schedule_over_24_force_24(reset_class_counters):
    obj = ventilation.PhxScheduleVentilation(
        operating_periods=ventilation.Vent_UtilPeriods(
            high=ventilation.Vent_OperatingPeriod(25, 0.98),  # <-- over 24
            standard=ventilation.Vent_OperatingPeriod(0, 0.0),
            basic=ventilation.Vent_OperatingPeriod(0, 0.0),
            minimum=ventilation.Vent_OperatingPeriod(0, 0.0),
        )
    )
    obj.force_max_utilization_hours()
    assert obj
    assert obj.operating_periods.high.period_operating_hours == 24


def test_vent_schedules_different_hash(reset_class_counters):
    obj_1 = ventilation.PhxScheduleVentilation()
    obj_2 = ventilation.PhxScheduleVentilation()

    assert hash(obj_1) != hash(obj_2)

    # -- try adding to a set
    s_1 = set()
    s_1.add(obj_1)
    s_1.add(obj_2)
    assert len(s_1) == 2
