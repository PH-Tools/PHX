# -*- Python Version: 3.10 -*-

"""Tests for PHX.from_HBJSON.cleanup.merge_lighting and PH interior lighting merge (PHX#171)."""

import logging

import pytest
from honeybee.model import Model
from honeybee.room import Room
from honeybee_energy.lib.schedules import schedule_by_identifier
from honeybee_energy.load.lighting import Lighting
from honeybee_energy_ph.load.ph_equipment import PhPhiusLightingInterior
from honeybee_ph.bldg_segment import BldgSegment
from ladybug_geometry.geometry3d import Point3D

from PHX.from_HBJSON.cleanup import merge_lighting, merge_rooms
from PHX.from_HBJSON.create_project import convert_hb_model_to_PhxProject


def _room(name: str, origin_x: float) -> Room:
    rm = Room.from_box(name.replace(" ", "_"), 4, 4, 3, origin=Point3D(origin_x, 0, 0))
    rm.display_name = name
    return rm


def _lighting(name: str, w_per_m2: float = 1.0, ph_equip: PhPhiusLightingInterior | None = None) -> Lighting:
    ltg = Lighting(name, w_per_m2, schedule_by_identifier("Always On"))
    if ph_equip is not None:
        ltg.properties.ph.ph_equipment = ph_equip
    return ltg


@pytest.mark.parametrize("apartment_first", [False, True])
def test_ph_lighting_device_survives_regardless_of_room_order(apartment_first: bool):
    segment = BldgSegment()
    segment.display_name = "Test_Segment"

    corridor = _room("Corridor", 0)
    corridor.properties.ph.ph_bldg_segment = segment
    corridor.properties.energy.lighting = _lighting("Corridor_lighting", 1.0)

    apartment = _room("Apt 1", 4)
    apartment.properties.ph.ph_bldg_segment = segment
    apartment.properties.energy.lighting = _lighting("Apt1_lighting", 1.0, PhPhiusLightingInterior())

    rooms = [apartment, corridor] if apartment_first else [corridor, apartment]

    merged = merge_rooms(rooms, 0.01, 1.0, False)
    assert isinstance(merged.properties.energy.lighting.properties.ph.ph_equipment, PhPhiusLightingInterior)

    project = convert_hb_model_to_PhxProject(Model("segment", rooms=rooms))
    assert len(project.variants) == 1
    zone = project.variants[0].building.zones[0]
    assert [type(d).__name__ for d in zone.elec_equipment_collection.devices] == ["PhxDeviceLightingInterior"]


def test_ph_lighting_device_survives_when_first_room_has_no_lighting():
    unlit = _room("Storage", 0)
    unlit.properties.energy.lighting = None

    apartment = _room("Apt 1", 4)
    apartment.properties.energy.lighting = _lighting("Apt1_lighting", 2.0, PhPhiusLightingInterior())

    merged = merge_rooms([unlit, apartment], 0.01, 1.0, False)
    assert merged.properties.energy.lighting is not None
    assert isinstance(merged.properties.energy.lighting.properties.ph.ph_equipment, PhPhiusLightingInterior)


def test_multiple_rooms_with_matching_ph_lighting_keep_one_without_warning(caplog: pytest.LogCaptureFixture):
    apt1 = _room("Apt 1", 0)
    apt1.properties.energy.lighting = _lighting("Apt1_lighting", 1.0, PhPhiusLightingInterior())

    apt2 = _room("Apt 2", 4)
    apt2.properties.energy.lighting = _lighting("Apt2_lighting", 1.0, PhPhiusLightingInterior())

    with caplog.at_level(logging.WARNING):
        merged_ltg = merge_lighting([apt1, apt2])

    assert merged_ltg is not None
    assert isinstance(merged_ltg.properties.ph.ph_equipment, PhPhiusLightingInterior)
    assert not any("conflicting PH lighting" in rec.message for rec in caplog.records)


def test_conflicting_ph_lighting_values_keeps_first_and_warns(caplog: pytest.LogCaptureFixture):
    equip_1 = PhPhiusLightingInterior()
    equip_1.frac_high_efficiency = 0.9
    apt1 = _room("Apt 1", 0)
    apt1.properties.energy.lighting = _lighting("Apt1_lighting", 1.0, equip_1)

    equip_2 = PhPhiusLightingInterior()
    equip_2.frac_high_efficiency = 0.5
    apt2 = _room("Apt 2", 4)
    apt2.properties.energy.lighting = _lighting("Apt2_lighting", 1.0, equip_2)

    with caplog.at_level(logging.WARNING):
        merged_ltg = merge_lighting([apt1, apt2])

    assert merged_ltg is not None
    assert merged_ltg.properties.ph.ph_equipment.frac_high_efficiency == pytest.approx(0.9)
    assert any("Apt 1" in rec.message and "Apt 2" in rec.message for rec in caplog.records)


def test_merge_lighting_does_not_mutate_source_rooms():
    corridor = _room("Corridor", 0)
    corridor.properties.energy.lighting = _lighting("Corridor_lighting", 1.0)

    apartment = _room("Apt 1", 4)
    apartment.properties.energy.lighting = _lighting("Apt1_lighting", 3.0, PhPhiusLightingInterior())

    merged_ltg = merge_lighting([corridor, apartment])

    assert merged_ltg is not None
    assert merged_ltg.watts_per_area == pytest.approx(2.0)
    assert corridor.properties.energy.lighting.properties.ph.ph_equipment is None
    assert corridor.properties.energy.lighting.watts_per_area == pytest.approx(1.0)
    assert apartment.properties.energy.lighting.watts_per_area == pytest.approx(3.0)


def test_merge_lighting_returns_none_when_no_rooms_have_lighting():
    rm1 = _room("Room 1", 0)
    rm1.properties.energy.lighting = None
    rm2 = _room("Room 2", 4)
    rm2.properties.energy.lighting = None

    assert merge_lighting([rm1, rm2]) is None
