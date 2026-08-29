"""The room-count invariant behind the Phius multi-family MEL / lighting export.

PHX creates one PhxZone per Honeybee-Room and adds every room's devices to *every*
zone, keyed by the device identifier, as an upsert. The Phius-MF builders in
`honeybee_grasshopper_ph` rely on that: `build_mel` sets
`energy_demand = total / number_of_rooms` and hands one device to all N rooms. The N
per-room devices collapse to one device per zone, and the N zones then sum back to
the building total.

Nothing asserted that until now, and the arithmetic is held up entirely by the shared
device identifier -- see honeybee-ph decision 0008.
"""

import pytest
from honeybee.room import Room
from honeybee_energy.lib.schedules import schedule_by_identifier
from honeybee_energy.load.process import Process
from honeybee_energy_ph.load import ph_equipment
from honeybee_ph_standards.programtypes.default_elec_equip import ph_default_equip

from PHX.from_HBJSON import create_variant
from PHX.model.building import PhxZone
from PHX.model.project import PhxVariant

TOTAL_DEMAND = 12_000.0  # kWh/yr for the whole building


def _mf_equipment(_cls_name, _total_demand, _room_count):
    """Mirror the Phius-MF builders: one device, demand divided by the room count."""
    equipment_class = getattr(ph_equipment, _cls_name)
    equipment = equipment_class(_defaults=ph_default_equip[_cls_name]["PHIUS"])
    equipment.display_name = "Phius-MF-{}".format(_cls_name)
    equipment.energy_demand = _total_demand / _room_count
    equipment.quantity = 1
    return equipment


def _rooms_with_one_shared_device(_room_count, _equipment):
    """N Honeybee-Rooms that all carry the same Process Load, as the MF component builds them."""
    process = Process(
        identifier="HBPH_Process_MF",
        watts=100,
        schedule=schedule_by_identifier("Always On"),
        fuel_type="Electricity",
        end_use_category="HBPH_Process",
    )
    process.properties.ph.ph_equipment = _equipment

    rooms = []
    for i in range(_room_count):
        room = Room.from_box("Room_{}".format(i), 5, 5, 3)
        room.properties.energy.add_process_load(process)
        rooms.append(room)
    return rooms


def _variant_with_zones(_room_count):
    variant = PhxVariant()
    variant.building.add_zones([PhxZone() for _ in range(_room_count)])
    return variant


def _exported_total(_variant):
    """Sum the device demand across every zone, as WUFI/METr would total it."""
    return sum(
        device.get_energy_demand() * device.get_quantity()
        for zone in _variant.building.zones
        for device in zone.elec_equipment_collection.devices
    )


@pytest.mark.parametrize("room_count", [1, 2, 10])
@pytest.mark.parametrize("equipment_type", ["PhCustomAnnualMEL", "PhCustomAnnualLighting", "PhCustomAnnualElectric"])
def test_the_exported_demand_equals_the_building_total(room_count, equipment_type):
    """N rooms x (total / N) must export as `total`, not as `N x total`."""
    equipment = _mf_equipment(equipment_type, TOTAL_DEMAND, room_count)
    rooms = _rooms_with_one_shared_device(room_count, equipment)
    variant = _variant_with_zones(room_count)

    for room in rooms:
        create_variant.add_elec_equip_from_hb_room(variant, room)

    assert _exported_total(variant) == pytest.approx(TOTAL_DEMAND)


@pytest.mark.parametrize("room_count", [1, 2, 10])
def test_each_zone_holds_exactly_one_device(room_count):
    """The upsert onto one key is what makes the total come out right."""
    equipment = _mf_equipment("PhCustomAnnualMEL", TOTAL_DEMAND, room_count)
    rooms = _rooms_with_one_shared_device(room_count, equipment)
    variant = _variant_with_zones(room_count)

    for room in rooms:
        create_variant.add_elec_equip_from_hb_room(variant, room)

    assert [len(zone.elec_equipment_collection.devices) for zone in variant.building.zones] == [1] * room_count


@pytest.mark.parametrize("room_count", [2, 10])
def test_a_re_keyed_device_would_multiply_the_total_by_the_room_count(room_count):
    """Guard the reason `PhEquipment.duplicate()` keeps the identifier.

    If every room's device arrived with its own identifier, each zone would hold N
    devices instead of 1 and the export would come out N times too high. This test
    fails the day someone 'fixes' duplicate() to re-key.
    """
    variant = _variant_with_zones(room_count)
    for i in range(room_count):
        equipment = _mf_equipment("PhCustomAnnualMEL", TOTAL_DEMAND, room_count)
        equipment.identifier = "re-keyed-{}".format(i)  # -- what a conventional duplicate() would do
        room = _rooms_with_one_shared_device(1, equipment)[0]
        create_variant.add_elec_equip_from_hb_room(variant, room)

    assert _exported_total(variant) == pytest.approx(TOTAL_DEMAND * room_count)
