"""Characterize the occupancy and schedule fields changed by the phased fixes."""

from xml.etree import ElementTree

import pytest

from PHX.from_HBJSON import create_project, create_schedules
from PHX.to_METr_JSON import metr_builder
from PHX.to_WUFI_XML import xml_builder
from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import (
    GENERIC_OFFICE_OCCUPANCY_MEAN,
    NON_RES_FIXTURE,
    load_hb_model,
)


def _load_non_res_model():
    return load_hb_model(NON_RES_FIXTURE)


def _build_non_res_project():
    return create_project.convert_hb_model_to_PhxProject(
        _load_non_res_model(), _group_components=True, _merge_faces=False
    )


def test_space_peak_occupancy_comes_from_the_non_res_people_load():
    """The non-res People load reaches every PHX Space."""
    project = _build_non_res_project()
    spaces = [space for variant in project.variants for zone in variant.building.zones for space in zone.spaces]

    assert len(spaces) == 4
    assert [space.peak_occupancy for space in spaces] == pytest.approx([5.65] * 4)


def test_schedule_without_ph_periods_uses_annual_mean():
    """A stock HB occupancy schedule becomes 0/24/365 with its annual mean."""
    hb_room = _load_non_res_model().rooms[0]
    schedule = create_schedules.build_occupancy_schedule_from_hb_room(hb_room)

    assert schedule is not None
    assert (schedule.start_hour, schedule.end_hour) == (0, 24)
    assert schedule.annual_utilization_days == pytest.approx(365.0, abs=0.001)
    assert schedule.relative_utilization_factor == pytest.approx(GENERIC_OFFICE_OCCUPANCY_MEAN)


def test_full_load_lighting_hours_reports_eflh():
    """Lighting full-load hours apply the HB schedule's annual utilization factor."""
    hb_room = _load_non_res_model().rooms[0]
    schedule = create_schedules.build_lighting_schedule_from_hb_room(hb_room)

    assert schedule is not None
    assert schedule.full_load_lighting_hours == pytest.approx(2555.39130768)


def test_wufi_reference_pins_current_phase_fields():
    """The WUFI reference pins the corrected occupancy load, factor, and EFLH."""
    root = ElementTree.fromstring(xml_builder.generate_WUFI_XML_from_object(_build_non_res_project()))

    assert [float(node.text) for node in root.iter("NumberOccupants")] == pytest.approx([5.65] * 4)
    assert [float(node.text) for node in root.iter("RelativeAbsenteeism")] == pytest.approx(
        [GENERIC_OFFICE_OCCUPANCY_MEAN]
    )
    assert [float(node.text) for node in root.iter("LightingFullLoadHours")] == pytest.approx([2555.4] * 4)


def test_metr_reference_pins_current_phase_fields():
    """The METr reference pins the corrected occupancy load, factor, and EFLH."""
    metr = metr_builder.generate_metr_json_dict(_build_non_res_project())
    loads = [variant["building"]["lZone"][0]["loadsZ"] for variant in metr["lVariant"]]

    assert [pattern["relAbs"] for pattern in metr["lUtilNResPH"]] == pytest.approx([GENERIC_OFFICE_OCCUPANCY_MEAN])
    assert [person["nOcc"] for zone in loads for person in zone["lPersZ"]] == pytest.approx([5.65] * 4)
    assert [lighting["lFLoadH"] for zone in loads for lighting in zone["lLight"]] == pytest.approx([2555.4] * 4)
