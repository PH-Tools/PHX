# -*- Python Version: 3.10 -*-

"""Tests for PHX.from_HBJSON.cleanup.merge_process_loads device counting (PHX#153).

A device shared across merged HB-Rooms (same equipment identifier) becomes one device whose
quantity is the sum of the per-Room quantities. A stored 0, the legacy honeybee-ph default,
counts as one unit, so N Rooms give N devices for legacy and new files alike.
"""

import pytest
from honeybee.room import Room
from honeybee_energy.lib.schedules import schedule_by_identifier
from honeybee_energy.load.process import Process
from honeybee_energy_ph.load.ph_equipment import PhCustomAnnualMEL

from PHX.from_HBJSON.cleanup import merge_process_loads


def _rooms_sharing_one_device(_room_count: int, _quantity: int) -> list[Room]:
    """N HB-Rooms, each with its own Process load carrying the same equipment identifier."""
    rooms = []
    for i in range(_room_count):
        equipment = PhCustomAnnualMEL()
        equipment.identifier = "shared_mel"
        equipment.energy_demand = 400.0
        equipment.quantity = _quantity
        process = Process(f"process_{i}", 100, schedule_by_identifier("Always On"), fuel_type="Electricity")
        process.properties.ph.ph_equipment = equipment
        room = Room.from_box(f"rm_{i}", 5, 5, 3)
        room.properties.energy.add_process_load(process)
        rooms.append(room)
    return rooms


@pytest.mark.parametrize("quantity, expected", [(0, 3), (1, 3), (2, 6)])
def test_a_device_shared_across_three_rooms_sums_its_quantity(quantity, expected):
    merged = merge_process_loads(_rooms_sharing_one_device(3, quantity))

    assert len(merged) == 1
    assert merged[0].properties.ph.ph_equipment.quantity == expected


def test_merging_leaves_the_source_rooms_unchanged():
    rooms = _rooms_sharing_one_device(3, 0)
    merge_process_loads(rooms)

    assert [rm.properties.energy.process_loads[0].properties.ph.ph_equipment.quantity for rm in rooms] == [0, 0, 0]
