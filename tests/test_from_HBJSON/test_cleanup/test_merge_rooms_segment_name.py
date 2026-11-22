# -*- Python Version: 3.10 -*-

"""Tests that Building Segment names with spaces or punctuation survive merge_rooms (PHX#175)."""

import xml.etree.ElementTree as ET

import pytest
from honeybee.model import Model
from honeybee.room import Room
from honeybee.typing import valid_string
from honeybee_ph.bldg_segment import BldgSegment
from ladybug_geometry.geometry3d import Point3D

from PHX.from_HBJSON.cleanup import merge_rooms
from PHX.from_HBJSON.create_project import convert_hb_model_to_PhxProject
from PHX.to_METr_JSON.metr_builder import generate_metr_json_dict
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object


def _segment_rooms(segment_name: str, origin_y: float = 0.0, segment_id: str | None = None) -> list[Room]:
    segment = BldgSegment()
    segment.display_name = segment_name
    if segment_id is not None:
        segment.identifier = segment_id
    rooms = []
    for i, name in enumerate(["Living", "Bedroom"]):
        rm = Room.from_box(f"{name}_{int(origin_y)}_{i}", 4, 4, 3, origin=Point3D(4 * i, origin_y, 0))
        rm.properties.ph.ph_bldg_segment = segment
        rooms.append(rm)
    return rooms


@pytest.mark.parametrize("segment_name", ["Main_House", "Main House", "Building A (Phase 2), #1!"])
def test_merge_rooms_accepts_segment_name_with_spaces_and_punctuation(segment_name: str):
    rooms = _segment_rooms(segment_name)

    merged = merge_rooms(rooms, 0.01, 1.0, False)

    assert valid_string(merged.identifier) == merged.identifier
    assert merged.display_name == segment_name


@pytest.mark.parametrize("segment_name", ["Main House", "Building A (Phase 2), #1!"])
def test_convert_preserves_segment_name_in_variant_zone_wufi_and_metr(segment_name: str):
    model = Model("segment_name_model", rooms=_segment_rooms(segment_name))

    project = convert_hb_model_to_PhxProject(model)

    assert len(project.variants) == 1
    assert project.variants[0].name == segment_name
    assert project.variants[0].building.zones[0].display_name == segment_name

    xml_root = ET.fromstring(generate_WUFI_XML_from_object(project))
    assert xml_root.findtext(".//Variants/Variant/Name") == segment_name
    assert xml_root.findtext(".//Building/Zones/Zone/Name") == segment_name

    metr = generate_metr_json_dict(project)
    assert metr["lVariant"][0]["n"] == segment_name
    assert metr["lVariant"][0]["building"]["lZone"][0]["n"] == segment_name


def test_two_segments_colliding_after_cleaning_produce_distinct_rooms_and_variants():
    rooms_space = _segment_rooms("Main House", origin_y=0.0)
    rooms_underscore = _segment_rooms("Main_House", origin_y=10.0)

    merged_space = merge_rooms(rooms_space, 0.01, 1.0, False)
    merged_underscore = merge_rooms(rooms_underscore, 0.01, 1.0, False)
    assert merged_space.identifier != merged_underscore.identifier

    model = Model("two_segments", rooms=rooms_space + rooms_underscore)
    project = convert_hb_model_to_PhxProject(model)

    assert [v.name for v in project.variants] == ["Main House", "Main_House"]
    assert [v.building.zones[0].display_name for v in project.variants] == ["Main House", "Main_House"]


def test_merge_rooms_handles_segment_identifier_with_spaces():
    rooms = _segment_rooms("Main House", segment_id="seg with space & punctuation!")

    merged = merge_rooms(rooms, 0.01, 1.0, False)

    assert valid_string(merged.identifier) == merged.identifier
    assert merged.display_name == "Main House"
