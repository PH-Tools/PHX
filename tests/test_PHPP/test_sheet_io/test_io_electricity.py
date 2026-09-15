# -*- Python Version: 3.10 -*-

"""Tests for PHPP 'Electricity' device writes.

A category the model authors replaces PHPP's template rows for that category;
a category it does not author keeps the template.
"""

from PHX.model import elec_equip
from PHX.PHPP.phpp_model.electricity_item import ElectricityItemXLWriter
from PHX.PHPP.sheet_io.io_electricity import Electricity
from PHX.xl.xl_app import XLConnection
from tests.test_PHPP.test_sheet_io.conftest import load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

STANDARD_DEVICE_QUANTITY_CELLS = {f"E{row}": 0 for row in range(45, 53)}


def _write(_shape_filename: str, *_devices: elec_equip.PhxElectricalDevice) -> tuple[dict, list[str]]:
    shape = load_shape(_shape_filename).ELECTRICITY
    fake_xl = FakeXLFramework(sheet_names=[shape.name])
    outputs: list[str] = []
    connection = XLConnection(xl_framework=fake_xl, output=outputs.append)
    Electricity(connection, shape).write_equipment([ElectricityItemXLWriter(device) for device in _devices])
    return fake_xl.written_state().get(shape.name, {}), outputs


def _annual_device(_cls: type, _name: str, _kwh: float) -> elec_equip.PhxElectricalDevice:
    device = _cls()
    device.display_name = _name
    device.energy_demand = _kwh
    device.quantity = 1
    return device


def test_unauthored_categories_keep_the_template():
    dishwasher = elec_equip.PhxDeviceDishwasher()

    written, _ = _write("EN_10_6.json", dishwasher)

    assert set(written) == {"E24", "E25", "F25", "N25"}


def test_authored_refrigeration_replaces_all_three_template_rows():
    written, _ = _write("EN_10_6.json", elec_equip.PhxDeviceRefrigerator())

    assert (written["E16"], written["E17"], written["E18"]) == (1, 0, 0)


def test_cooktop_and_dryer_write_their_quantity():
    written, _ = _write("EN_10_6.json", elec_equip.PhxDeviceCooktop(), elec_equip.PhxDeviceClothesDryer())

    assert (written["E21"], written["E33"]) == (1, 1)


def test_annual_devices_fill_one_row_per_category_and_replace_their_template_rows():
    lighting = _annual_device(elec_equip.PhxDeviceCustomLighting, "REF-LIGHTING", 400.0)
    mel = _annual_device(elec_equip.PhxDeviceCustomMEL, "REF-MEL", 1200.0)

    written, _ = _write("EN_10_6.json", lighting, mel)

    assert written == {
        "E38": 0,
        **STANDARD_DEVICE_QUANTITY_CELLS,
        "D64": "Lighting: REF-LIGHTING",
        "E64": 1,
        "F64": 1.0,
        "N64": 400.0,
        "D65": "Misc. electric loads: REF-MEL",
        "E65": 1,
        "F65": 1.0,
        "N65": 1200.0,
    }


def test_shape_without_annual_rows_skips_annual_devices_and_keeps_their_templates():
    lighting = _annual_device(elec_equip.PhxDeviceCustomLighting, "REF-LIGHTING", 400.0)
    mel = _annual_device(elec_equip.PhxDeviceCustomMEL, "REF-MEL", 1200.0)

    written, outputs = _write("EN_10_6IP.json", lighting, mel)

    assert written == {}
    assert any("were not written" in line for line in outputs)
