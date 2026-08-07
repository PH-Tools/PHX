"""Characterize the three known load/schedule defects before behavior changes."""

from xml.etree import ElementTree

import pytest

from PHX.from_HBJSON import create_project, create_schedules
from PHX.to_METr_JSON import metr_builder
from PHX.to_WUFI_XML import xml_builder
from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import NON_RES_FIXTURE, load_hb_model


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


def test_DEFECT_2_schedule_with_no_ph_periods_is_degenerate():
    """A stock HB occupancy schedule currently becomes 0/24/365 with factor 0."""
    hb_room = _load_non_res_model().rooms[0]
    schedule = create_schedules.build_occupancy_schedule_from_hb_room(hb_room)

    assert schedule is not None
    assert (schedule.start_hour, schedule.end_hour) == (0, 24)
    assert schedule.annual_utilization_days == pytest.approx(365.0, abs=0.001)
    assert schedule.relative_utilization_factor == 0.0


def test_DEFECT_3_full_load_lighting_hours_is_currently_8760():
    """Lighting full-load hours currently report the window rather than EFLH."""
    hb_room = _load_non_res_model().rooms[0]
    schedule = create_schedules.build_lighting_schedule_from_hb_room(hb_room)

    assert schedule is not None
    assert schedule.full_load_lighting_hours == 8760


def test_wufi_reference_pins_current_defect_fields():
    """The WUFI reference exposes all three fields that later phases must flip."""
    root = ElementTree.fromstring(xml_builder.generate_WUFI_XML_from_object(_build_non_res_project()))

    assert [float(node.text) for node in root.iter("NumberOccupants")] == pytest.approx([5.65] * 4)
    assert [float(node.text) for node in root.iter("RelativeAbsenteeism")] == [0.0]
    assert [float(node.text) for node in root.iter("LightingFullLoadHours")] == [8760.0] * 4


def test_metr_reference_pins_current_defect_fields():
    """The METr reference exposes all three fields that later phases must flip."""
    metr = metr_builder.generate_metr_json_dict(_build_non_res_project())
    loads = [variant["building"]["lZone"][0]["loadsZ"] for variant in metr["lVariant"]]

    assert [pattern["relAbs"] for pattern in metr["lUtilNResPH"]] == [0.0]
    assert [person["nOcc"] for zone in loads for person in zone["lPersZ"]] == pytest.approx([5.65] * 4)
    assert [lighting["lFLoadH"] for zone in loads for lighting in zone["lLight"]] == [8760] * 4
