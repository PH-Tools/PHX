from PHX.model.schedules import ventilation
from PHX.model import utilization_patterns


def test_empty_util_collection(reset_class_counters):
    coll = utilization_patterns.UtilizationPatternCollection_Ventilation()

    assert not coll
    assert not coll.patterns


def test_add_no_schedule_to_collection(reset_class_counters):
    coll = utilization_patterns.UtilizationPatternCollection_Ventilation()
    coll.add_new_util_pattern(None)
    assert not coll
    assert not coll.patterns


def test_add_single_schedule_to_collection(reset_class_counters):
    coll = utilization_patterns.UtilizationPatternCollection_Ventilation()
    vent_sched_1 = ventilation.PhxScheduleVentilation(
        operating_periods=ventilation.Vent_UtilPeriods(
            high=ventilation.Vent_OperatingPeriod(24, 0.0),
            standard=ventilation.Vent_OperatingPeriod(0, 0.0),
            basic=ventilation.Vent_OperatingPeriod(0, 0.0),
            minimum=ventilation.Vent_OperatingPeriod(0, 0.0),
        )
    )
    coll.add_new_util_pattern(vent_sched_1)

    assert len(coll) == 1
    assert vent_sched_1.identifier in coll.patterns.keys()
    assert coll.key_is_in_collection(vent_sched_1.identifier)

    for pat in coll:
        assert isinstance(pat, ventilation.PhxScheduleVentilation)


def test_add_multiple_schedules_to_collection(reset_class_counters):
    coll = utilization_patterns.UtilizationPatternCollection_Ventilation()
    pat_1 = ventilation.PhxScheduleVentilation(
        operating_periods=ventilation.Vent_UtilPeriods(
            high=ventilation.Vent_OperatingPeriod(24, 0.0),
            standard=ventilation.Vent_OperatingPeriod(0, 0.0),
            basic=ventilation.Vent_OperatingPeriod(0, 0.0),
            minimum=ventilation.Vent_OperatingPeriod(0, 0.0),
        )
    )
    pat_2 = ventilation.PhxScheduleVentilation(
        operating_periods=ventilation.Vent_UtilPeriods(
            high=ventilation.Vent_OperatingPeriod(24, 0.0),
            standard=ventilation.Vent_OperatingPeriod(0, 0.0),
            basic=ventilation.Vent_OperatingPeriod(0, 0.0),
            minimum=ventilation.Vent_OperatingPeriod(0, 0.0),
        )
    )
    coll.add_new_util_pattern(pat_1)
    coll.add_new_util_pattern(pat_2)

    assert len(coll) == 2
    assert pat_1.identifier in coll.patterns.keys()
    assert pat_2.identifier in coll.patterns.keys()
    assert coll.key_is_in_collection(pat_1.identifier)
    assert coll.key_is_in_collection(pat_2.identifier)

    for pat in coll:
        assert isinstance(pat, ventilation.PhxScheduleVentilation)
