# Phase 0 — ACH ventilation double-conversion + uniform Space flow distribution

**Ships as its own commit.** Unrelated to the occupancy work; different blast radius; must be
reviewable alone (D9).

**Depends on:** nothing. Start here.

---

## Context

`calc_space_ventilation_flow_rate()` splits a Honeybee-Room's ventilation across its
Honeybee-PH Spaces. It has two problems.

### Problem 1 — a 3600x units error

`hb_room_vent_flowrates()` (in `honeybee_ph_utils.ventilation`) returns a 4-tuple. Its **third**
element is **already m³/s** — the function computes
`vent_program.air_changes_per_hour * _hb_room.volume / 3600` — and its docstring says
`"[2] (m3s)"`.

PHX unpacks that element into a local named `air_changes_per_hour` and divides by 3600 **again**:

```python
m3s_by_ach = (air_changes_per_hour * space_percent_of_total) / 3_600
```

Measured on a 100 m² / 300 m³ room at 0.5 ACH:

```
correct                 0.04166667 m3/s  = 150.000 m3/hr
current code gives      0.00001157 m3/s  =   0.042 m3/hr        understated 3600x
```

Three of the four unpacked names describe *rates* that need multiplying; one describes a *flow*
that does not. The misleading local name is the entire cause.

### Problem 2 — an unresolved TODO, and inconsistent distribution

The function carries `# TODO: Unweighted or weighted? Which is right?` and already mixes two
strategies in one body:

- flow-by-person and flow-by-area → density × **Space** area
- flow-by-ACH and flow-by-zone → room total × **area fraction**

Resolve it uniformly to **room total × area fraction** for all four (D6). This is the same rule
Phase 2 applies to occupancy, so the two stop disagreeing.

### Real-project exposure: none

The bug only manifests when a room uses ACH-based ventilation **and** its Spaces carry no
`_v_sup` override — `create_rooms.py:126-133` discards the computed flow whenever `_v_sup` /
`_v_eta` is set. A survey of all 56 project folders (37 readable) found **0 exposed**. Two
projects use ACH ventilation but override every Space.

Only `tests/reference_files/from_grasshopper_tests/hbjson/Multi_Room_Complete.hbjson` is
exposed (0.4 ACH, no `_v_sup`). This is a fixture-only change.

---

## Files you may touch

```
PHX/from_HBJSON/create_rooms.py                                    (the fix)
tests/test_from_HBJSON/test_create_rooms/__init__.py               (new)
tests/test_from_HBJSON/test_create_rooms/test_space_ventilation_flow.py   (new)
```

Nothing else.

---

## The change

`PHX/from_HBJSON/create_rooms.py`, function `calc_space_ventilation_flow_rate` (currently
lines 24-66).

### Before

```python
    host_room_prop_ph = get_ph_prop_from_room(host)
    (
        flow_per_person,
        flow_per_area,
        air_changes_per_hour,
        flow_per_zone,
    ) = hb_room_vent_flowrates(host)
    # TODO: Unweighted or weighted? Which is right?
    ref_flr_area = _space.floor_area

    # -- Basic flow rates
    m3s_by_occupancy = ref_flr_area * hb_room_ppl_per_area(host) * flow_per_person
    m3s_by_area = ref_flr_area * flow_per_area

    # -- Figure out % of the HB-Room that the Space represents
    # -- For the Flow-by-Zone and Flow-by_ACH, need to calc the Room total flow
    # -- and then calc the % of that total that this one space represents.
    hb_room_total_space_fa = host_room_prop_ph.total_space_floor_area
    space_percent_of_total = ref_flr_area / hb_room_total_space_fa

    m3s_by_ach = (air_changes_per_hour * space_percent_of_total) / 3_600
    m3s_by_zone = flow_per_zone * space_percent_of_total

    return (m3s_by_occupancy + m3s_by_area + m3s_by_zone + m3s_by_ach) * 3_600
```

### After

```python
    host_room_prop_ph = get_ph_prop_from_room(host)
    (
        flow_per_person,  # -- m3/s PER PERSON
        flow_per_area,  # -- m3/s PER M2 of HB-Room floor
        flow_by_ach_m3s,  # -- m3/s TOTAL for the Room (already ach * volume / 3600)
        flow_per_zone,  # -- m3/s TOTAL for the Room
    ) = hb_room_vent_flowrates(host)

    # -- Each of the four flow-types is calculated as the HB-Room TOTAL, then distributed
    # -- to the Space by its share of the Room's total Space floor-area. This keeps
    # -- 'sum(Space flows) == Room total' exactly, and matches how Space occupancy is
    # -- distributed in 'create_room_from_space'. (Resolves the former
    # -- "Unweighted or weighted?" TODO: unweighted Space floor-area fraction.)
    hb_room_total_space_fa = host_room_prop_ph.total_space_floor_area
    if not hb_room_total_space_fa:
        return 0.0
    space_percent_of_total = _space.floor_area / hb_room_total_space_fa

    room_peak_occupancy = hb_room_ppl_per_area(host) * host.floor_area

    m3s_by_occupancy = flow_per_person * room_peak_occupancy * space_percent_of_total
    m3s_by_area = flow_per_area * host.floor_area * space_percent_of_total
    m3s_by_ach = flow_by_ach_m3s * space_percent_of_total
    m3s_by_zone = flow_per_zone * space_percent_of_total

    return (m3s_by_occupancy + m3s_by_area + m3s_by_zone + m3s_by_ach) * 3_600
```

### Checklist

- [ ] Third unpacked name is `flow_by_ach_m3s`, **not** `air_changes_per_hour`
- [ ] The `/ 3_600` on `m3s_by_ach` is **deleted** (the trailing `* 3_600` on the return stays —
      that converts the m³/s sum to m³/hr and is correct)
- [ ] `flow_per_person` multiplies `room_peak_occupancy`, not a Space area
- [ ] `flow_per_area` multiplies `host.floor_area`, not `_space.floor_area`
- [ ] All four terms carry `space_percent_of_total`
- [ ] The `# TODO: Unweighted or weighted?` comment is gone, replaced by the decision note
- [ ] Zero-division guard on `hb_room_total_space_fa`
- [ ] Update the function docstring to state that it returns the Space's *share* of the Room total

---

## Guardrails

- **Do not touch** `create_room_from_space` — that is Phase 2.
- **Do not touch** the `_v_sup` / `_v_eta` / `_v_tran` override block at `:126-133`. It runs
  after this function and legitimately discards its result.
- **Do not** "fix" `hb_room_vent_flowrates()` upstream. It is correct and its docstring is
  accurate. The bug is PHX's local naming.

---

## Tests to write

`tests/test_from_HBJSON/test_create_rooms/test_space_ventilation_flow.py`

### R0 — ACH is not double-converted

```python
def test_ach_flow_is_not_divided_by_3600_twice():
    """A 300 m3 room at 0.5 ACH must yield 150 m3/hr, not 0.042."""
    # 0.5 ACH * 300 m3 = 150 m3/hr
    # Build an HB-Room (10 x 10 x 3) with a single default Space covering the full
    # floor area, ventilation set to air_changes_per_hour=0.5 and every other
    # flow-type zeroed, then assert calc_space_ventilation_flow_rate(...) == 150.0
```

Zero out `flow_per_person`, `flow_per_area`, and `flow_per_zone` so the assertion isolates the
ACH term.

### R0b — Space flows sum to the Room total

```python
def test_space_flows_sum_to_room_total():
    """Sum over Spaces must equal the HB-Room's own total, for any mix of flow types."""
    # Use honeybee_ph_utils.ventilation.hb_room_peak_ventilation_airflow_total(room)
    # as the independent reference. It returns m3/s -- multiply by 3600.
    # Test with (a) a single Space tiling the room, and (b) two Spaces that together
    # cover only part of the room floor area.
```

This is the invariant the rewrite buys, and it is what stops a future change reverting to the
per-Space-area form.

### Boundary

```python
def test_zero_total_space_floor_area_returns_zero():
    """A Room whose Spaces sum to zero floor area must not raise ZeroDivisionError."""
```

---

## Verification gate

```bash
python -m pytest tests/test_from_HBJSON/test_create_rooms/ -v      # new tests pass
python -m pytest tests/test_xl_replay/ -v                          # MUST be unchanged
python -m pytest tests/                                            # full suite
```

Expected golden movement: **`Multi_Room_Complete` ventilation values only.** It is the sole
fixture with ACH-based ventilation and no `_v_sup` override, and its flows will rise sharply —
that is the bug being corrected. Inspect the delta and confirm it matches
`0.4 ACH x room volume`. **No other fixture may move.** If `Default_Model_Single_Zone` or the
Excel replay moves, stop and re-read the change.

---

## Definition of done

- [ ] All three new tests pass
- [ ] Full suite green
- [ ] `tests/test_xl_replay/` byte-identical
- [ ] `Multi_Room_Complete` ventilation delta inspected and explained; no other fixture moved
- [ ] The TODO comment is gone and the decision is recorded in its place

## Commit

```
fix(from_hbjson): correct 3600x understatement of ACH-based ventilation in Space airflow
```
