# -*- Python Version: 3.10 -*-

"""Tests that attached zones (PhAdditionalZone) do not receive exhaust ventilators (PHX#172)."""

import xml.etree.ElementTree as ET

import pytest
from honeybee.model import Model
from honeybee.room import Room
from honeybee_energy_ph.boundarycondition import PhAdditionalZone
from honeybee_ph.space import Space, SpaceFloor, SpaceFloorSegment, SpaceVolume
from honeybee_phhvac.ventilation import ExhaustVentDryer, ExhaustVentKitchenHood
from ladybug_geometry.geometry3d import Face3D, Point3D

from PHX.from_HBJSON import create_variant
from PHX.from_HBJSON.create_project import convert_hb_model_to_PhxProject
from PHX.model.building import PhxZone
from PHX.model.enums.building import ZoneType
from PHX.model.hvac.ventilation import PhxExhaustVentilatorRangeHood
from PHX.model.project import PhxVariant
from PHX.to_METr_JSON.metr_builder import generate_metr_json_dict
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object


def _room_with_exhaust_vents(devices=None) -> Room:
    house = Room.from_box("House", 4, 4, 3, origin=Point3D(0, 0, 0))
    house.display_name = "House"
    seg = SpaceFloorSegment()
    seg.geometry = Face3D([Point3D(0, 0, 0), Point3D(4, 0, 0), Point3D(4, 4, 0), Point3D(0, 4, 0)])
    flr = SpaceFloor()
    flr.add_floor_segment(seg)
    vol = SpaceVolume()
    vol.floor = flr
    vol.avg_ceiling_height = 3.0
    space = Space(house)
    space.add_new_volumes(vol)
    house.properties.ph.add_new_space(space)
    for device in devices if devices is not None else (ExhaustVentKitchenHood(), ExhaustVentDryer()):
        house.properties.ph_hvac.add_exhaust_vent_device(device)
    return house


def _model_with_attached_zone() -> Model:
    house = _room_with_exhaust_vents()
    house.faces[1].boundary_condition = PhAdditionalZone(
        identifier="atz_garage",
        zone_name="Garage",
        temperature_reduction_factor=0.95,
    )
    return Model("house_with_garage", rooms=[house])


def test_exhaust_vent_not_copied_onto_attached_zones():
    project = convert_hb_model_to_PhxProject(_model_with_attached_zone())
    variant = project.variants[0]

    simulated = [z for z in variant.building.zones if z.zone_type == ZoneType.SIMULATED]
    attached = [z for z in variant.building.zones if z.zone_type == ZoneType.ATTACHED]

    assert len(simulated) == 1
    assert len(attached) == 1
    assert sorted(type(d).__name__ for d in simulated[0].exhaust_ventilator_collection.devices) == [
        "PhxExhaustVentilatorDryer",
        "PhxExhaustVentilatorRangeHood",
    ]
    assert list(attached[0].exhaust_ventilator_collection.devices) == []


def test_attached_zone_has_no_exhaust_vents_in_wufi_xml_and_metr_json():
    project = convert_hb_model_to_PhxProject(_model_with_attached_zone())

    xml_text = generate_WUFI_XML_from_object(project)
    root = ET.fromstring(xml_text)
    xml_zones = {
        z.findtext("Name"): len(z.findall("./ExhaustVents/ExhaustVent")) for z in root.findall(".//Building/Zones/Zone")
    }
    assert xml_zones == {"Unnamed_Bldg_Segment": 2, "Garage": 0}

    metr_data = generate_metr_json_dict(project)
    metr_zones = {z["n"]: len(z["lExhVent"]) for z in metr_data["lVariant"][0]["building"]["lZone"]}
    assert metr_zones == {"Unnamed_Bldg_Segment": 2, "Garage": 0}


@pytest.mark.parametrize("merge_devices, expected_count", [(False, 2), (True, 1)])
def test_multiple_simulated_zones_receive_and_merge_exhaust_vents_while_attached_zone_is_untouched(
    merge_devices: bool, expected_count: int
):
    hood_1 = ExhaustVentKitchenHood()
    hood_1.display_name = "Hood_1"
    hood_2 = ExhaustVentKitchenHood()
    hood_2.display_name = "Hood_2"
    rm = _room_with_exhaust_vents([hood_1, hood_2])

    sim_1, sim_2 = PhxZone(display_name="Sim_1"), PhxZone(display_name="Sim_2")
    attached = PhxZone(display_name="Garage", zone_type=ZoneType.ATTACHED)
    variant = PhxVariant()
    variant.building.add_zones([sim_1, sim_2, attached])

    create_variant.add_exhaust_vent_devices_from_hb_rooms(variant, rm, _merge_devices=merge_devices)

    assert len(sim_1.exhaust_ventilator_collection.devices) == expected_count
    assert len(sim_2.exhaust_ventilator_collection.devices) == expected_count
    assert list(attached.exhaust_ventilator_collection.devices) == []


def test_merge_loop_skips_attached_zones():
    rm = _room_with_exhaust_vents()
    sim = PhxZone(display_name="Sim")
    attached = PhxZone(display_name="Garage", zone_type=ZoneType.ATTACHED)
    attached.exhaust_ventilator_collection.add_new_ventilator("hood_a", PhxExhaustVentilatorRangeHood())
    attached.exhaust_ventilator_collection.add_new_ventilator("hood_b", PhxExhaustVentilatorRangeHood())

    variant = PhxVariant()
    variant.building.add_zones([sim, attached])

    create_variant.add_exhaust_vent_devices_from_hb_rooms(variant, rm, _merge_devices=True)

    assert len(attached.exhaust_ventilator_collection.devices) == 2
