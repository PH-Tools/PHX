"""Synthetic Honeybee Room fixtures for occupancy-channel tests."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path

from honeybee.model import Model
from honeybee.room import Room
from honeybee_energy.lib.programtypes import program_type_by_identifier
from honeybee_energy_ph.properties.load.people import PhDwellings
from honeybee_ph.space import Space, SpaceFloor, SpaceFloorSegment, SpaceVolume
from ladybug_geometry.geometry3d import Point3D

from PHX.from_HBJSON import read_HBJSON_file

REFERENCE_HBJSON_DIR = Path("tests", "reference_files", "from_grasshopper_tests", "hbjson")
OCCUPANCY_SCENARIO_DIR = REFERENCE_HBJSON_DIR / "occupancy_scenarios"
NON_RES_FIXTURE = REFERENCE_HBJSON_DIR / "Non_Residential_Office.hbjson"
GENERIC_OFFICE_OCCUPANCY_MEAN = 0.28856164383561644
OCCUPANCY_CORPUS_CASES = (
    ("01_no_dwelling_no_occupancy.hbjson", False),
    ("02_single_dwelling_no_occupancy.hbjson", False),
    ("03_single_dwelling_set_occupancy.hbjson", True),
    ("04_no_dwelling_set_occupancy.hbjson", True),
    ("05_multiple_dweling_set_occupancy.hbjson", True),
    ("06_res_with_hallway.hbjson", True),
)


@dataclass(frozen=True)
class RoomSpec:
    """Inputs needed to reconstruct post-Set Occupancy Honeybee Rooms."""

    name: str
    floor_area_m2: float
    number_people: float
    dwelling: str | None


def room_specs_from_rooms(rooms: list[Room]) -> list[RoomSpec]:
    """Reconstruct synthetic fixture inputs from real Grasshopper Room state."""
    return [
        RoomSpec(
            room.identifier,
            room.floor_area,
            room.properties.energy.people.properties.ph.number_people,
            (
                str(room.properties.energy.people.properties.ph.dwellings.identifier)
                if room.properties.energy.people.properties.ph.number_dwelling_units >= 1
                else None
            ),
        )
        for room in rooms
    ]


def _add_full_floor_space(_hb_room: Room) -> Space:
    """Add one PH Space whose floor tiles the Honeybee Room floor."""
    segment = SpaceFloorSegment()
    segment.geometry = _hb_room.floors[0].geometry

    floor = SpaceFloor()
    floor.add_floor_segment(segment)
    volume = SpaceVolume()
    volume.floor = floor

    ph_space = Space(_host=_hb_room)
    ph_space.name = f"{_hb_room.display_name}_default_space"
    ph_space.add_new_volumes(volume)
    _hb_room.properties.ph.add_new_space(ph_space)
    return ph_space


def load_hb_model(_path: Path) -> Model:
    """Load a Honeybee model through PHX's production HBJSON reader."""
    hbjson = read_HBJSON_file.read_hb_json_from_file(_path)
    return read_HBJSON_file.convert_hbjson_dict_to_hb_model(hbjson)


def build_rooms(
    specs: list[RoomSpec],
    *,
    avg_occ_rate: float,
    hb_program: str,
    apply_set_occupancy: bool = True,
) -> list[Room]:
    """Build HB Rooms in the state that ``HBPH - Set Occupancy`` leaves behind.

    INVARIANT MIRRORED FROM honeybee_grasshopper_ph
    ``set_res_occupancy.set_people_per_m2()``:

    * rooms sharing a ``dwelling`` tag share one ``PhDwellings`` instance;
    * every room in a tagged group carries the same ``people_per_area``::

          group_total_number_people / avg_occ_rate / group_total_floor_area

      regardless of that individual room's own ``number_people``;
    * untagged rooms are normalized independently when Set Occupancy is applied;
    * a group or untagged room totalling zero people gets ``people_per_area = 0``;
    * when Set Occupancy is not applied, the HB program density is preserved.

    The six real Grasshopper exports in
    ``test_gh_invariant_real_hbjson.py`` anchor this reconstruction. If those
    tests fail, this builder is stale and its downstream expectations are suspect.
    """
    if avg_occ_rate <= 0:
        raise ValueError("avg_occ_rate must be greater than zero")

    rooms: list[Room] = []
    dwelling_objects: dict[str, PhDwellings] = {}
    for index, spec in enumerate(specs):
        side_length = sqrt(spec.floor_area_m2)
        hb_room = Room.from_box(spec.name, side_length, side_length, 3.0, origin=Point3D(index * 20, 0, 0))
        hb_room.properties.energy.program_type = program_type_by_identifier(hb_program)
        hb_room.properties.energy.people = hb_room.properties.energy.people.duplicate()

        people = hb_room.properties.energy.people
        people.unlock()
        people.properties.ph.number_people = spec.number_people
        if spec.dwelling is not None:
            dwelling = dwelling_objects.setdefault(spec.dwelling, PhDwellings(_num_dwellings=1))
            people.properties.ph.dwellings = dwelling

        _add_full_floor_space(hb_room)
        rooms.append(hb_room)

    if not apply_set_occupancy:
        for room in rooms:
            room.properties.energy.people.lock()
        return rooms

    tagged_groups: dict[str, list[Room]] = {}
    for room in rooms:
        people = room.properties.energy.people
        if people.properties.ph.number_dwelling_units >= 1:
            tagged_groups.setdefault(str(people.properties.ph.dwellings.identifier), []).append(room)
        else:
            people.people_per_area = people.properties.ph.number_people / avg_occ_rate / room.floor_area

    for group_rooms in tagged_groups.values():
        group_people = sum(room.properties.energy.people.properties.ph.number_people for room in group_rooms)
        group_floor_area = sum(room.floor_area for room in group_rooms)
        group_density = group_people / avg_occ_rate / group_floor_area
        for room in group_rooms:
            room.properties.energy.people.people_per_area = group_density

    for room in rooms:
        room.properties.energy.people.lock()
    return rooms
