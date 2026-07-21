# -*- Python Version: 3.10 -*-

"""Tests for PHX.from_HBJSON.cleanup dwelling-unit counting.

The dwelling count computed here becomes `PhxZone.res_number_dwellings` and
`ph_building_data.num_of_units`, which is written out as `NumberUnits` in the WUFI XML,
`num_of_units` in the PHPP Verification worksheet, and `nUnits` in the METr JSON. It is
also used to scale Phius MF appliance and lighting loads, so an off-by-N here is a silent
energy error rather than a cosmetic one.

Counting is by UNIQUE `PhDwellings` object, so a dwelling spanning several HB-Rooms is
counted once. See honeybee-ph decision 0002 (dwelling identity lives on PhDwellings,
never on `Room.zone`).
"""

import pytest
from honeybee.room import Room
from honeybee_energy.load.people import People
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy_ph.properties.load.people import PhDwellings

from PHX.from_HBJSON.cleanup import merge_occupancies


def _room(_name: str, _dwelling: PhDwellings | None = None, _with_people: bool = True) -> Room:
    """Build a HB-Room, optionally with a People load carrying a PhDwellings object."""
    room = Room.from_box(_name, 5, 5, 3)
    if _with_people:
        people = People(f"{_name}_People", 0.01, ScheduleRuleset.from_constant_value("occ", 1.0))
        if _dwelling is not None:
            people.properties.ph.dwellings = _dwelling
        room.properties.energy.people = people
    return room


def _merged_dwelling_count(_hb_rooms: list[Room]) -> int:
    return merge_occupancies(_hb_rooms).properties.ph.dwellings.num_dwellings


class TestMergeOccupanciesDwellingCount:
    """The dwelling-unit count that reaches WUFI / PHPP / METr."""

    def test_single_family_home_is_one_dwelling(self):
        """N Rooms sharing ONE PhDwellings object -> 1 unit, not N."""
        dwelling = PhDwellings(_num_dwellings=1)
        rooms = [_room(f"rm_{i}", dwelling) for i in range(6)]

        assert _merged_dwelling_count(rooms) == 1

    def test_multifamily_distinct_dwellings(self):
        """Each Room with its OWN PhDwellings -> counted separately."""
        rooms = [_room(f"rm_{i}", PhDwellings(_num_dwellings=1)) for i in range(4)]

        assert _merged_dwelling_count(rooms) == 4

    def test_single_room_holding_many_dwellings(self):
        """A Room modeled as a 'block' of dwellings uses num_dwellings > 1."""
        rooms = [_room("rm_1", PhDwellings(_num_dwellings=4))]

        assert _merged_dwelling_count(rooms) == 4

    def test_mixed_shared_and_distinct(self):
        shared = PhDwellings(_num_dwellings=2)
        rooms = [
            _room("rm_1", shared),
            _room("rm_2", shared),
            _room("rm_3", PhDwellings(_num_dwellings=3)),
        ]

        assert _merged_dwelling_count(rooms) == 5

    def test_duplicated_dwelling_object_is_not_double_counted(self):
        """duplicate() yields a new object with the SAME identifier -- still one dwelling."""
        dwelling = PhDwellings(_num_dwellings=1)
        rooms = [_room("rm_1", dwelling), _room("rm_2", dwelling.duplicate())]

        assert _merged_dwelling_count(rooms) == 1


class TestMergeOccupanciesNonResidential:
    """Non-residential and un-tagged models are floored at one unit."""

    def test_rooms_without_people_are_floored_to_one(self):
        """Non-res segments contribute zero dwellings, but must report at least 1."""
        rooms = [_room(f"rm_{i}", _with_people=False) for i in range(3)]

        assert _merged_dwelling_count(rooms) == 1

    def test_rooms_never_through_set_dwelling_are_floored_to_one(self):
        """Rooms still holding the PhDwellings.default() singleton contribute zero."""
        rooms = [_room(f"rm_{i}") for i in range(4)]

        assert rooms[0].properties.energy.people.properties.ph.dwellings.identifier == PhDwellings.default().identifier
        assert _merged_dwelling_count(rooms) == 1

    def test_untagged_rooms_do_not_each_become_a_dwelling(self):
        """Regression guard: 4 un-tagged Rooms must not report 4 dwelling units."""
        rooms = [_room(f"rm_{i}") for i in range(4)]

        assert _merged_dwelling_count(rooms) != 4


class TestMergeOccupanciesOccupantTotals:
    """Bedroom / occupant totals are summed across Rooms, not de-duplicated."""

    def test_bedrooms_and_people_are_summed(self):
        dwelling = PhDwellings(_num_dwellings=1)
        rooms = []
        for i in range(3):
            room = _room(f"rm_{i}", dwelling)
            prop_ph = room.properties.energy.people.properties.ph
            prop_ph.number_bedrooms = 2
            prop_ph.number_people = 1.5
            rooms.append(room)

        merged_prop_ph = merge_occupancies(rooms).properties.ph

        assert merged_prop_ph.number_bedrooms == 6
        assert merged_prop_ph.number_people == pytest.approx(4.5)
        assert merged_prop_ph.dwellings.num_dwellings == 1
