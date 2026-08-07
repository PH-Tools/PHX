import pytest

from PHX.model.schedules.lighting import PhxScheduleLighting


def test_eflh_applies_the_utilization_factor():
    schedule = PhxScheduleLighting(
        start_hour=0,
        end_hour=24,
        annual_utilization_days=365,
        relative_utilization_factor=0.2917,
    )

    assert schedule.full_load_lighting_hours == pytest.approx(2555.292)


def test_eflh_at_full_utilization_equals_the_window():
    schedule = PhxScheduleLighting(
        start_hour=7,
        end_hour=18,
        annual_utilization_days=250,
        relative_utilization_factor=1.0,
    )

    assert schedule.full_load_lighting_hours == 2750


def test_eflh_at_zero_utilization_is_zero():
    schedule = PhxScheduleLighting(
        start_hour=0,
        end_hour=24,
        annual_utilization_days=365,
        relative_utilization_factor=0.0,
    )

    assert schedule.full_load_lighting_hours == 0


def test_eflh_is_clamped_to_8760():
    schedule = PhxScheduleLighting(
        start_hour=0,
        end_hour=24,
        annual_utilization_days=365,
        relative_utilization_factor=2.0,
    )

    assert schedule.full_load_lighting_hours == 8760


def test_eflh_is_never_negative():
    schedule = PhxScheduleLighting(
        start_hour=0,
        end_hour=24,
        annual_utilization_days=365,
        relative_utilization_factor=-1.0,
    )

    assert schedule.full_load_lighting_hours == 0
