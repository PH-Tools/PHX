# -*- Python Version: 3.10 -*-

"""Tests for PHX.from_HBJSON.create_elec_equip dryer type (PHX#160)."""

from honeybee_energy_ph.load.ph_equipment import PhClothesDryer, PhEquipmentBuilder

from PHX.from_HBJSON.create_elec_equip import build_phx_elec_device
from PHX.to_METr_JSON.metr_schemas import _PhxElectricalDevice
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_hbjson_heat_pump_dryer_reaches_metr_as_7_and_wufi_as_4(reset_class_counters):
    hbph_dryer = PhClothesDryer()
    hbph_dryer.dryer_type = 7
    hbph_dryer = PhEquipmentBuilder.from_dict(hbph_dryer.to_dict())  # -- as read from HBJSON

    device = build_phx_elec_device(hbph_dryer)

    assert _PhxElectricalDevice(device)["tDryer"] == 7
    wufi_xml = xml_string_to_list(generate_WUFI_XML_from_object(device, "", "_PhxElectricalDevice"))
    assert "<Dryer_Choice>4</Dryer_Choice>" in wufi_xml
