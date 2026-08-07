# Phase 2 — Populate the Space occupancy load, gated per dwelling group

**Status:** Complete — 44 focused tests, the 82.31-person real-project check, residential
field-level comparisons, Excel replay, and the 837-test full gate pass.

**This phase resolves the reported symptom.** After it, `2616 {IA} 39 15th St` exports 82.3
occupants instead of 0.

**Depends on:** Phase 0 (same function), Phase 1 (the tests that verify this).

---

## Context

`create_room_from_space()` wires up the occupancy **schedule** but never the occupancy **load**:

```python
# PHX/from_HBJSON/create_rooms.py:140-143
if hbe_occ:
    occ_sched_id = hbe_occ.occupancy_schedule.identifier
    new_room.occupancy.schedule = _occ_sched_collection[occ_sched_id]
```

`PhxSpace.occupancy.load.people_per_m2` keeps its `0.0` default, so
`peak_occupancy = people_per_m2 * floor_area` is **always 0** for any model built from HBJSON.
Compare the lighting branch four lines below, which *does* set `load.installed_w_per_m2` — this
is an omission, not a design decision.

## The rule (D1)

> **Explicit PH occupancy wins, evaluated per dwelling group.**
>
> If **any** room in a Space's dwelling group carries an explicit `number_people`, every Space
> in that group exports `NumberOccupants = 0` — the occupancy is already expressed at the zone
> level via `PhxZone.res_occupant_quantity`. Otherwise, derive from the Honeybee-Energy `People`
> load. An untagged room is its own group of one.

### Why per-group and not per-room

`set_res_occupancy.set_people_per_m2()` normalizes a dwelling's occupants across the **whole
group** — every room in it receives the *same* `people_per_area` regardless of its own
`number_people`. A per-room gate therefore reads a per-group quantity and picks the wrong rooms:
it skips the room holding the explicit number and falls through on the rooms holding `0`.

That is the standard single-family shape (one dwelling, occupants entered on the bedrooms).
Three of the six real test models leak under a per-room gate.

### Why the group key is `num_dwellings >= 1` (D2)

`honeybee_energy_ph.dwellings.get_dwelling_obj()` **does not survive an HBJSON round-trip**.
`PhDwellings.default()` mints a fresh `uuid4` per process; the Grasshopper session's default
identifier is serialized into the file, and on re-import `_is_default_dwelling()` compares it
against *this* process's default and misses. Every untagged room then shares one identifier and
pools into a single group.

`num_dwellings >= 1` is serialization-stable and is already the codebase's definition of "is a
dwelling" (`PeoplePhProperties.is_residential`).

### Why Option B for distribution (D6)

`people_per_area` is per m² of **HB-Room** floor, but `peak_occupancy` multiplies by **Space**
floor area. Where Spaces do not tile the room, occupants are silently deleted
(`Multi_Room_Complete`: 48.40 m² room vs 21.78 m² of Spaces — 55% lost).

Distribute the room total by Space floor-area fraction instead. It is **algebraically identical**
when Spaces tile (the common default-Space case) and correct when they do not, so it strictly
dominates.

---

## Files you may touch

```
PHX/from_HBJSON/_dwelling_occupancy.py     (new)
PHX/from_HBJSON/create_rooms.py            (the gate)
PHX/from_HBJSON/create_building.py         (thread the index)
PHX/from_HBJSON/create_variant.py          (thread the index)
PHX/from_HBJSON/create_project.py          (build the index)
tests/test_from_HBJSON/test_create_rooms/  (matrix + index tests)
```

---

## Step 2a — the index

New file `PHX/from_HBJSON/_dwelling_occupancy.py`:

```python
# -*- Python Version: 3.10 -*-

"""Index of explicit PH occupancy (`number_people`) totalled per dwelling group."""

from __future__ import annotations

from dataclasses import dataclass, field

from honeybee import room


@dataclass
class DwellingOccupancyIndex:
    """Total explicit PH occupancy (`number_people`) per dwelling group.

    MUST be built from the PRE-MERGE Honeybee-Rooms. After cleanup.merge_rooms(),
    the merged room reports one dwelling holding the whole building's occupancy --
    merge_occupancies() forces PhDwellings(max(count, 1)) (cleanup.py:217) and sums
    number_people onto it (cleanup.py:260).
    """

    _totals: dict[str, float] = field(default_factory=dict)

    @staticmethod
    def _key(_hb_room: room.Room) -> str:
        """Return the dwelling-group key for a Room.

        `num_dwellings >= 1` is the ONLY serialization-stable "is tagged" test.
        get_dwelling_obj() / _is_default_dwelling() compare against a PER-PROCESS
        PhDwellings.default() uuid4, so after an HBJSON round-trip every untagged
        room shares the serialized default identifier and would pool into one
        group. Untagged rooms must each form a group of one.
        """
        ...

    @classmethod
    def from_hb_rooms(cls, _hb_rooms: list[room.Room]) -> DwellingOccupancyIndex:
        """Total `number_people` per group across the given (pre-merge) Rooms."""
        ...

    def has_explicit_occupancy(self, _hb_room: room.Room) -> bool:
        """True if ANY room in this Room's dwelling group states `number_people`."""
        return bool(self._totals.get(self._key(_hb_room), 0.0))
```

Handle rooms with no energy properties / no `people` load gracefully — treat them as
contributing `0.0`, not as an error.

---

## Step 2b — thread it through

Build **once** in `create_project.convert_hb_model_to_PhxProject()` from `_hb_model.rooms`,
**before** the `sort_hb_rooms_by_bldg_segment` loop (~line 145), then pass down the chain that
already carries three collection objects in exactly this shape:

```
create_project.convert_hb_model_to_PhxProject     <- build here, from _hb_model.rooms
  └─ create_variant.from_hb_room(...)                        + _dwelling_occupancy
       └─ create_variant.add_building_from_hb_room(...)      + _dwelling_occupancy
            └─ create_building.create_zone_from_hb_room(...) + _dwelling_occupancy
                 └─ create_rooms.create_room_from_space(...) + _dwelling_occupancy
```

Add the parameter after `_lighting_sched_collection` in each signature, and document it in each
docstring in the existing style.

> **Do NOT build it from the merged room's `{sp.host for sp in spaces}`.** That is less
> plumbing but wrong: a dwelling room that contributes `number_people` while having no PH Spaces
> would be missing from the set, dropping its group total to zero and reopening the leak.

---

## Step 2c — the gate

`PHX/from_HBJSON/create_rooms.py`, replacing lines 140-143:

```python
    # -- Keep the new room's Occupancy reference aligned with the HB-Room's
    if hbe_occ:
        new_room.occupancy.schedule = _occ_sched_collection[hbe_occ.occupancy_schedule.identifier]

        # -- Explicit PH occupancy wins, evaluated per DWELLING GROUP. When any room in
        # -- the group states 'number_people', that dwelling is already expressed through
        # -- the zone-level channel (PhxZone.res_occupant_quantity) and every Space in the
        # -- group must stay at 0: 'people_per_area' is a group-uniform PEAK density
        # -- back-computed from the same input, so emitting both would double-count.
        # -- NOTE: '_space.host' is the ORIGINAL un-merged room. The merged room is
        # -- unusable here -- merge_occupancies() forces PhDwellings(max(count, 1)) and
        # -- sums number_people onto it (cleanup.py:217, :260).
        if not _dwelling_occupancy.has_explicit_occupancy(_space.host):
            # -- Distribute the ROOM's total peak occupancy across its Spaces by
            # -- floor-area fraction, so Spaces that do not tile the Room do not
            # -- silently delete occupants. Identical to (density x Space area) when
            # -- they do tile.
            host = _space.host
            room_peak_occupancy = hbe_occ.people_per_area * host.floor_area
            total_space_fa = get_ph_prop_from_room(host).total_space_floor_area
            if total_space_fa:
                new_room.peak_occupancy = room_peak_occupancy * (_space.floor_area / total_space_fa)
```

Assign through the **`PhxSpace.peak_occupancy` setter** (`PHX/model/spaces.py:117`) — it already
divides by `floor_area` and guards `ZeroDivisionError`.

`hbe_occ` already resolves through `_space.host` via `_get_energy_properties_from_space(_space)`
at line 100, so no new lookup is needed for the People load itself.

---

## Guardrails

- **Never** gate on the merged room, on `PhxZone.res_number_dwellings`, or on the variant's
  certification category. All three classify every project as residential.
- **Never** gate per-room. If models 03/05/06 produce `2.43` / `0.69` / `0.69`, the gate is
  per-room.
- **Do not** modify `set_zone_occupancy()` or anything else in the zone-level channel.
- **Do not** remove the dead area-weighted `people_per_area` in `cleanup.py:257`. Unrelated.

---

## Tests

Write the layer-1 matrix TDD-style: expectations first, watch models 01/02 fail, implement,
watch all six pass.

`tests/test_from_HBJSON/test_create_rooms/test_occupancy_gate_matrix.py`

| model | zone (A) | expected per-space (B) |
|---|---|---|
| `01_no_dwelling_no_occupancy` | 0.0 | **22.60** |
| `02_single_dwelling_no_occupancy` | 0.0 | **22.60** |
| `03_single_dwelling_set_occupancy` | 7.0 | **0.00** |
| `04_no_dwelling_set_occupancy` | 7.0 | **0.00** |
| `05_multiple_dwelling_set_occupancy` | 7.0 | **0.00** |
| `06_res_with_hallway` | 7.0 | **0.00** |

Plus the eight synthetic scenarios from `../PRD.md` → "Verified scenario matrix", built with the
Phase-1 `build_rooms()` helper.

**Assert per-room values, not just the sum.** Several scenarios pass on the total for the wrong
reason.

Also add the `DwellingOccupancyIndex` unit tests (layer-2 invariant 5): group keying, untagged
handling, totals, empty model, rooms without a People load.

---

## Verification gate

```bash
python -m pytest tests/test_from_HBJSON/test_create_rooms/ -v
python -m pytest tests/test_xl_replay/ -v      # MUST be unchanged
python -m pytest tests/
```

Real-project check — the reason this packet exists:

```
-FLOOR_01_default_space   fa=  266.16  peak_occ=  15.04
-FLOOR_02_default_space   fa=  246.10  peak_occ=  13.91
-FLOOR_03_default_space   fa=  517.58  peak_occ=  29.25
-FLOOR_04_default_space   fa=  393.45  peak_occ=  22.23
-FLOOR_05_default_space   fa=   33.32  peak_occ=   1.88
                                       TOTAL      82.31
```

(Command in `README.md` → "Verification commands".)

Golden movement: **`Non_Residential_Office` occupancy fields only.**
`Multi_Room_Complete` and `Default_Model_Single_Zone` occupancy must be **unchanged** — they are
residential and hit the skip branch.

---

## Definition of done

- [x] All six real models match the table, asserted per-room
- [x] All eight synthetic scenarios pass
- [x] Layer-2 invariants still green — R15 and R7 now load-bearing, not trivial
- [x] Real project totals 82.31 occupants
- [x] Residential fixtures' occupancy fields unchanged
- [x] `tests/test_xl_replay/` unchanged
- [x] `res_occupant_quantity` / `res_number_bedrooms` unchanged everywhere

## Commit

```
fix(from_hbjson): set the Space occupancy load from the HB People load when no explicit PH occupancy is set
```
