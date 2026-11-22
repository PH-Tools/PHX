# -*- Python Version: 3.10 -*-

"""Tests that attached zones (PhAdditionalZone) do not receive PH appliance devices (PHX#171)."""

import xml.etree.ElementTree as ET

from honeybee.model import Model
from honeybee.room import Room
from honeybee_energy.lib.schedules import schedule_by_identifier
from honeybee_energy.load.lighting import Lighting
from honeybee_energy.load.process import Process
from honeybee_energy_ph.boundarycondition import PhAdditionalZone
from honeybee_energy_ph.load.ph_equipment import PhDishwasher, PhPhiusLightingInterior
from ladybug_geometry.geometry3d import Point3D

from PHX.from_HBJSON import create_variant
from PHX.from_HBJSON.create_project import convert_hb_model_to_PhxProject
from PHX.model.building import PhxZone
from PHX.model.enums.building import ZoneType
from PHX.model.project import PhxVariant
from PHX.to_METr_JSON.metr_builder import generate_metr_json_dict
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object


def _model_with_attached_zone() -> Model:
    always_on = schedule_by_identifier("Always On")

    house = Room.from_box("House", 4, 4, 3, origin=Point3D(0, 0, 0))
    house.display_name = "House"

    dishwasher = Process("House_dishwasher", 0.0, always_on, "Electricity")
    dishwasher.properties.ph.ph_equipment = PhDishwasher()
    house.properties.energy.add_process_load(dishwasher)

    lighting = Lighting("House_lighting", 1.0, always_on)
    lighting.properties.ph.ph_equipment = PhPhiusLightingInterior()
    house.properties.energy.lighting = lighting

    house.faces[1].boundary_condition = PhAdditionalZone(
        identifier="atz_garage",
        zone_name="Garage",
        temperature_reduction_factor=0.95,
    )
    return Model("house_with_garage", rooms=[house])


def test_elec_equip_not_copied_onto_attached_zones():
    project = convert_hb_model_to_PhxProject(_model_with_attached_zone())
    variant = project.variants[0]

    simulated = [z for z in variant.building.zones if z.zone_type == ZoneType.SIMULATED]
    attached = [z for z in variant.building.zones if z.zone_type == ZoneType.ATTACHED]

    assert len(simulated) == 1
    assert len(attached) == 1
    assert sorted(type(d).__name__ for d in simulated[0].elec_equipment_collection.devices) == [
        "PhxDeviceDishwasher",
        "PhxDeviceLightingInterior",
    ]
    assert list(attached[0].elec_equipment_collection.devices) == []


def test_attached_zone_has_no_devices_in_wufi_xml_and_metr_json():
    project = convert_hb_model_to_PhxProject(_model_with_attached_zone())

    xml_text = generate_WUFI_XML_from_object(project)
    root = ET.fromstring(xml_text)
    xml_zones = {
        z.findtext("Name"): len(z.findall("./HomeDevice/Device")) for z in root.findall(".//Building/Zones/Zone")
    }
    assert xml_zones == {"Unnamed_Bldg_Segment": 2, "Garage": 0}

    metr_data = generate_metr_json_dict(project)
    metr_zones = {z["n"]: len(z["loadsZ"]["lHomeDev"]) for z in metr_data["lVariant"][0]["building"]["lZone"]}
    assert metr_zones == {"Unnamed_Bldg_Segment": 2, "Garage": 0}


def test_multiple_simulated_zones_receive_devices_while_attached_zone_stays_empty():
    always_on = schedule_by_identifier("Always On")
    rm = Room.from_box("Unit", 4, 4, 3)
    dishwasher = Process("Unit_dishwasher", 0.0, always_on, "Electricity")
    dishwasher.properties.ph.ph_equipment = PhDishwasher()
    rm.properties.energy.add_process_load(dishwasher)

    sim_1, sim_2 = PhxZone(display_name="Sim_1"), PhxZone(display_name="Sim_2")
    attached = PhxZone(display_name="Garage", zone_type=ZoneType.ATTACHED)
    variant = PhxVariant()
    variant.building.add_zones([sim_1, sim_2, attached])

    create_variant.add_elec_equip_from_hb_room(variant, rm)

    assert len(sim_1.elec_equipment_collection.devices) == 1
    assert len(sim_2.elec_equipment_collection.devices) == 1
    assert list(attached.elec_equipment_collection.devices) == []
