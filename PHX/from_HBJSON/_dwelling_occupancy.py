# -*- Python Version: 3.10 -*-

"""Index explicit PH occupancy (``number_people``) by dwelling group."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from honeybee import room

from PHX.from_HBJSON._type_utils import MissingEnergyPropertiesError, get_room_people


@dataclass
class DwellingOccupancyIndex:
    """Total explicit PH occupancy (``number_people``) per dwelling group.

    The index must be built from the pre-merge Honeybee Rooms. After
    ``cleanup.merge_rooms()``, the merged Room reports one dwelling containing
    the whole building's occupancy: ``merge_occupancies()`` forces at least one
    dwelling and sums ``number_people`` onto it.
    """

    _totals: dict[str, float] = field(default_factory=dict)

    @staticmethod
    def _key(_hb_room: room.Room) -> str:
        """Return the serialization-stable dwelling-group key for a Room.

        ``num_dwellings >= 1`` is the tagged-dwelling test. The Honeybee-PH
        default dwelling identifier does not survive an HBJSON round-trip, so
        untagged Rooms must be keyed individually by Room identifier.
        """
        try:
            people = get_room_people(_hb_room)
        except MissingEnergyPropertiesError:
            return f"room:{_hb_room.identifier}"

        people_ph = people.properties.ph
        if people_ph.number_dwelling_units >= 1:
            return f"dwelling:{people_ph.dwellings.identifier}"
        return f"room:{_hb_room.identifier}"

    @classmethod
    def from_hb_rooms(cls, _hb_rooms: Iterable[room.Room]) -> DwellingOccupancyIndex:
        """Total ``number_people`` per group across pre-merge Honeybee Rooms."""
        totals: dict[str, float] = {}
        for hb_room in _hb_rooms:
            key = cls._key(hb_room)
            try:
                people = get_room_people(hb_room)
            except MissingEnergyPropertiesError:
                totals.setdefault(key, 0.0)
                continue

            totals[key] = totals.get(key, 0.0) + float(people.properties.ph.number_people)
        return cls(totals)

    def has_explicit_occupancy(self, _hb_room: room.Room) -> bool:
        """Return True if any Room in this Room's group states ``number_people``."""
        return bool(self._totals.get(self._key(_hb_room), 0.0))
