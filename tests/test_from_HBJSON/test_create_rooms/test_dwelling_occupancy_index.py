"""Unit tests for explicit PH occupancy indexing by dwelling group."""

from PHX.from_HBJSON._dwelling_occupancy import DwellingOccupancyIndex
from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import RoomSpec, build_rooms


def _build(specs: list[RoomSpec]):
    return build_rooms(
        specs,
        avg_occ_rate=0.5,
        hb_program="2019::SmallOffice::OpenOffice",
        apply_set_occupancy=False,
    )


def test_tagged_rooms_are_totalled_by_dwelling_group():
    """Explicit people on one Room suppress every Room in that dwelling."""
    rooms = _build(
        [
            RoomSpec("dwelling_a_1", 100, 0, "A"),
            RoomSpec("dwelling_a_2", 100, 3, "A"),
            RoomSpec("dwelling_b", 100, 0, "B"),
        ]
    )

    index = DwellingOccupancyIndex.from_hb_rooms(rooms)

    assert index.has_explicit_occupancy(rooms[0]) is True
    assert index.has_explicit_occupancy(rooms[1]) is True
    assert index.has_explicit_occupancy(rooms[2]) is False


def test_untagged_rooms_are_each_their_own_group():
    """One untagged Room's explicit people do not suppress another Room."""
    rooms = _build(
        [
            RoomSpec("explicit", 100, 3, None),
            RoomSpec("program", 100, 0, None),
        ]
    )

    index = DwellingOccupancyIndex.from_hb_rooms(rooms)

    assert index.has_explicit_occupancy(rooms[0]) is True
    assert index.has_explicit_occupancy(rooms[1]) is False


def test_empty_room_list_builds_an_empty_index():
    """An empty Honeybee model has no explicit occupancy."""
    index = DwellingOccupancyIndex.from_hb_rooms([])

    assert index._totals == {}


def test_room_without_people_load_contributes_zero():
    """Missing People loads are ignored rather than raising."""
    room = _build([RoomSpec("no_people", 100, 0, None)])[0]
    room.properties.energy.people = None

    index = DwellingOccupancyIndex.from_hb_rooms([room])

    assert index.has_explicit_occupancy(room) is False
