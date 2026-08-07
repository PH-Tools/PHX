# PLAN — Implementation sequence

Read [`PRD.md`](PRD.md) first — it holds the data-flow maps, the gating rule and its
derivation, the Phius protocol quotes, and the six-model test corpus.

> **For implementation, use [`plans/`](plans/).** This file is the sequencing overview; each
> phase there is a self-contained brief with exact edits, guardrails, tests, and a definition of
> done — written to be handed to a coding agent one phase at a time.

Follow `context/CODING_STANDARDS.md`. Conventional commits per phase (they drive the
semantic-release version bump).

## Ordering and independence

| phase | ships | blocked on |
|---|---|---|
| 0 — ACH ventilation 3600x | **separately, on its own** | nothing |
| 1 — test scaffolding | with phase 2 | nothing |
| 2 — Space occupancy load + TODO resolution | after 0 | nothing |
| 3 — schedule HB-style fallback | after 2 | nothing |
| 4 — lighting EFLH | **after 3** (never before) | nothing |
| 5 — goldens, validation, closeout | last | — |

Phase 4 before Phase 3 collapses FLH from 8760 to 0, because the utilization factor is `0.0`
today. Phase 0 is confirmed to ship as an independent commit — it is unrelated to the reported
symptom and has zero real-project exposure.

Phases 3 and 4 were previously gated on whether the fix was safe for residential models. The
WUFI A/B run settled it — the fields are inert on residential (PRD "Resolved question"), so
both phases apply to all models uniformly.

---

# Test strategy

Five layers. Layers 1-3 are the substance of Phase 1 and the acceptance gate for Phase 2.

## The central testing problem

**PHX cannot import `honeybee_grasshopper_ph`** — its package `__init__` pulls Rhino/`System`
bindings (verified: `ImportError: Failed to import System`). But the gating rule depends on an
invariant that lives in that repo:

> every room in a dwelling group carries the **same** `people_per_area`, computed as
> `group_total_number_people / avg_occ_rate / group_total_floor_area`, regardless of that
> room's own `number_people` — `set_res_occupancy.set_people_per_m2()`

Fast tests must therefore *reconstruct* that state, encoding an assumption that can drift.
**Layer 3 is the mitigation and must not be quietly dropped.**

## Layer 1 — synthetic gate matrix

`tests/test_from_HBJSON/test_create_rooms/test_occupancy_gate_matrix.py`

```python
@dataclass
class RoomSpec:
    name: str
    floor_area_m2: float
    number_people: float
    dwelling: str | None      # group tag; None = untagged (own group of one)


def build_rooms(specs, *, avg_occ_rate: float, hb_program: str) -> list[Room]:
    """Build HB-Rooms in the state 'HBPH - Set Occupancy' leaves behind.

    INVARIANT MIRRORED FROM honeybee_grasshopper_ph set_res_occupancy.set_people_per_m2():
      * rooms sharing a `dwelling` tag share ONE PhDwellings instance (num_dwellings=1)
      * every room in a group carries the SAME people_per_area:
            group_total_number_people / avg_occ_rate / group_total_floor_area
        -- regardless of that room's own number_people
      * a group totalling zero people gets people_per_area = 0.0
      * untagged rooms keep num_dwellings=0 and their HB program's people_per_area

    Anchored by test_gh_invariant_real_hbjson.py (layer 3). If that fails, this
    builder is stale and every expectation below is suspect.
    """
```

Parametrized over the eight PRD scenarios plus the six real models. **Assert per-room values,
not just the sum** — S5 and S8 pass on the total for the wrong reason otherwise.

## Layer 2 — implementation-independent invariants

`tests/test_from_HBJSON/test_create_rooms/test_occupancy_invariants.py`

1. **Merge-trap guard (R5).** Build a multi-room non-residential model, run
   `cleanup.merge_rooms()`, assert the merged room reports `is_residential=True` and a summed
   `number_people` (documenting why it is unusable), that each Space's `.host` still reports the
   original values, and that the built `PhxProject` has nonzero space occupancy. Without this,
   re-pointing the gate at the merged room looks harmless and silently zeroes every non-res
   project.
2. **Untagged rooms are not pooled (R6).** Two untagged rooms, explicit people on one only,
   nonzero program `people_per_area` on the other → the second must still fall back. This is the
   case no real model covers (see PRD "Known coverage gap") and the only test that catches the
   `get_dwelling_obj` serialization bug.
3. **Channels are mutually exclusive (R15).** Over every fixture: if
   `res_occupant_quantity > 0`, every Space in that zone has `peak_occupancy == 0`. Holds
   trivially today and becomes load-bearing after Phase 2. The durable net.
4. **Space totals preserve room totals (R7, R0b).** Σ Space occupancy == room peak occupancy;
   Σ Space ventilation == `hb_room_peak_ventilation_airflow_total() × 3600`.
5. **`DwellingOccupancyIndex` units.** Group keying, untagged handling, totals, empty model.

## Layer 3 — anchor against real component output

`tests/test_from_HBJSON/test_create_rooms/test_gh_invariant_real_hbjson.py`

Asserts layer 1's builder against the six committed models in [`HBJSON/`](HBJSON/) — real
Grasshopper output, no cross-repo import, runs everywhere including CI. Chiefly:

```python
def test_group_uniform_density_invariant():
    """03: one dwelling, 4 rooms, occupancy on a subset -> uniform group density."""
    # group total 7 people, 400 m2, sched mean 0.720833
    assert every room.people_per_area == pytest.approx(7 / 0.720833 / 400, rel=1e-6)
```

Optional local-only extra: load `set_res_occupancy.py` by file path with a stubbed
`ph_gh_component_io` and re-derive the invariant, `skipif` on the sibling repo's absence. The
prototype is [`scenario_harness.py`](scenario_harness.py) /
[`scenario_harness_sfh.py`](scenario_harness_sfh.py) — delete both when this packet is archived.

## Layer 4 — reference/golden

`01_no_dwelling_no_occupancy.hbjson` becomes the non-residential reference case in
`tests/conftest.py` (`to_xml_reference_cases`, `to_metr_json_reference_cases`). Existing
residential cases unchanged through Phase 2; changed only in the named fields in Phases 0, 3, 4.
Diffs reviewed field by field.

## Layer 5 — negative checks and real-project validation

- `tests/test_xl_replay/` passes **unchanged** (R13). Movement means the PHPP path was touched.
- `test_to_PPP` green.
- WUFI-XML round-trip on `_ridgeway` / `_la_mora` (R14).
- Re-export `39_15th_ST_260806.hbjson`; open in METr.

---

# Phases

## Phase 0 — ACH ventilation double-conversion + uniform Space flow distribution

**Independent commit. No real-project exposure (0 of 37).**

File: `PHX/from_HBJSON/create_rooms.py` (`calc_space_ventilation_flow_rate`, `:24-66`)

Replace the body's four flow terms with the room-total-then-distribute form in PRD
"Resolving the pre-existing ventilation TODO". Specifically:

1. Rename the third unpacked value to `flow_by_ach_m3s` and **delete the `/ 3_600`** — the
   value from `hb_room_vent_flowrates()` is already m³/s.
2. Compute `room_peak_occupancy = hb_room_ppl_per_area(host) * host.floor_area` and multiply
   flow-per-person by it, not by the Space area.
3. Multiply flow-per-area by `host.floor_area`, not the Space area.
4. Apply `frac = _space.floor_area / host_room_prop_ph.total_space_floor_area` to all four.
5. Delete the `# TODO: Unweighted or weighted?` comment and replace it with a one-line note
   recording the decision (room total, distributed by unweighted Space floor-area fraction).
6. Guard `total_space_floor_area == 0`.

Tests: R0 (0.5 ACH / 300 m³ → 150 m³/hr) and R0b (Σ Spaces == room total).

**Verification gate:** `Multi_Room_Complete` ventilation goldens move — that is the bug being
corrected; review the delta explicitly. No other fixture moves. `test_xl_replay` unchanged.

**Commit:** `fix(from_hbjson): correct 3600x understatement of ACH-based ventilation in Space airflow`

---

## Phase 1 — Test scaffolding and the non-residential reference case

**No behavior change.**

1. Wire `01_no_dwelling_no_occupancy.hbjson` into `tests/conftest.py` as the non-residential
   reference case; generate and commit its goldens against **current** behavior so Phase 2's
   diff is legible (`NumberOccupants` `0.0` → nonzero, nothing else).
2. Write the layer-1 builder with the invariant docstring.
3. Write layers 2 and 3 in full. Layer-2 invariants 1-3 hold today (1 and 2 trivially, 3 because
   B is always zero) — expected; they are nets, not discovery tests.
4. Characterization tests pinning today's behavior, labelled by defect: non-res space
   `peak_occupancy == 0.0`; no-PH-periods schedule → `(0, 24, 365.0, 0.0)`;
   `full_load_lighting_hours == 8760`.

**Verification gate:** full suite green, no existing golden changes.

**Commit:** `test(from_hbjson): add non-residential reference case and occupancy gate scaffolding`

---

## Phase 2 — Space occupancy load, gated per dwelling group

### 2a — the index

New file `PHX/from_HBJSON/_dwelling_occupancy.py`:

```python
@dataclass
class DwellingOccupancyIndex:
    """Total explicit PH occupancy (`number_people`) per dwelling group.

    Built from the PRE-MERGE Honeybee-Rooms. See PRD "The gating rule" for why the
    total must be per-group, and why the merged room cannot be used.
    """
    _totals: dict[str, float]

    @staticmethod
    def _key(_hb_room: room.Room) -> str:
        # -- num_dwellings >= 1 is the ONLY serialization-stable "is tagged" test.
        # -- get_dwelling_obj()/_is_default_dwelling() compare against a per-process
        # -- PhDwellings.default() uuid4, so after an HBJSON round-trip every untagged
        # -- room shares one identifier and would pool into a single group.
        pph = _hb_room.properties.energy.people.properties.ph
        return pph.dwellings.identifier if pph.number_dwelling_units >= 1 else _hb_room.identifier

    @classmethod
    def from_hb_rooms(cls, _hb_rooms: list[room.Room]) -> DwellingOccupancyIndex: ...

    def has_explicit_occupancy(self, _hb_room: room.Room) -> bool:
        return bool(self._totals.get(self._key(_hb_room), 0.0))
```

### 2b — thread it through

Built once in `create_project.convert_hb_model_to_PhxProject()` from `_hb_model.rooms`
(**pre-merge**, before the `sort_hb_rooms_by_bldg_segment` loop at `create_project.py:145`),
then down the existing chain, which already carries three collection objects in this exact
shape:

```
create_project.convert_hb_model_to_PhxProject      build here from _hb_model.rooms
  └─ create_variant.from_hb_room(...)                          + _dwelling_occupancy
       └─ create_variant.add_building_from_hb_room(...)        + _dwelling_occupancy
            └─ create_building.create_zone_from_hb_room(...)   + _dwelling_occupancy
                 └─ create_rooms.create_room_from_space(...)   + _dwelling_occupancy
```

Build at **project** level, not from the merged room's `{sp.host for sp in spaces}` — a
dwelling room contributing `number_people` but having no PH Spaces would be missing from the
latter, dropping the group total to zero and reopening the leak.

### 2c — the gate and Option B distribution

`create_rooms.py`, replacing `:140-143`:

```python
    if hbe_occ:
        new_room.occupancy.schedule = _occ_sched_collection[hbe_occ.occupancy_schedule.identifier]

        # -- Explicit PH occupancy wins, evaluated per DWELLING GROUP. When any room in
        # -- the group states 'number_people', that dwelling is expressed through the
        # -- zone-level channel (PhxZone.res_occupant_quantity) and every Space in the
        # -- group must stay at 0: 'people_per_area' is a group-uniform PEAK density
        # -- back-computed from the same input, so emitting both double-counts.
        # -- NOTE: '_space.host' is the ORIGINAL un-merged room. The merged room is
        # -- unusable - merge_occupancies() forces PhDwellings(max(count, 1)) and sums
        # -- number_people onto it (cleanup.py:217, :260).
        if not _dwelling_occupancy.has_explicit_occupancy(_space.host):
            # -- Distribute the ROOM's total peak occupancy across its Spaces by
            # -- floor-area fraction, so Spaces that do not tile the room do not
            # -- silently delete occupants. Identical to density x space-area when
            # -- they do tile. See PRD "Option B".
            room_peak_occupancy = hbe_occ.people_per_area * _space.host.floor_area
            new_room.peak_occupancy = room_peak_occupancy * (
                _space.floor_area / host_room_prop_ph.total_space_floor_area
            )
```

Use the `PhxSpace.peak_occupancy` setter — it already divides by `floor_area` and guards
`ZeroDivisionError`.

### 2d — tests

Write the layer-1 matrix TDD-style: expectations first, watch cases 01/02 fail, implement,
watch all six real models plus the eight synthetic scenarios pass.

**Verification gate:**
- All six real models match the PRD table; all eight synthetic scenarios pass, per-room.
- Layer-2 invariants green — R15 and R7 now load-bearing.
- `Multi_Room_Complete` / `Default_Model_Single_Zone` occupancy goldens **unchanged**.
- `test_xl_replay` unchanged.
- Real project: 15.04 / 13.91 / 29.25 / 22.23 / 1.88, total 82.3.

**Commit:** `fix(from_hbjson): set the Space occupancy load from the HB People load when no explicit PH occupancy is set`

> Phase 2 resolves the reported METr symptom. Worth shipping on its own so the fix reaches the
> project ahead of the schedule work in Phases 3-4.

---

## Phase 3 — HB-style fallback for occupancy and lighting schedules

**Status:** Complete — 8 focused tests, Excel replay, and the 845-test full gate pass.

(Scope question resolved — see PRD "Resolved question". Applies to all models.)

File: `PHX/from_HBJSON/create_schedules.py`. Mirror the ventilation structure at `:139-176`:

1. Add `_room_has_ph_style_occupancy()` / `_room_has_ph_style_lighting()` on the model of
   `_room_has_ph_style_ventilation()` (`:23-49`) — `bool(prop_ph.daily_operating_periods)`,
   missing schedule → `False`.
2. Split into `_create_*_from_ph_style()` / `..._from_hb_style()`. The `_ph_style` bodies move
   **verbatim** — R10 requires bit-identical output.
3. `_hb_style` assigns through the existing `annual_utilization_factor` setter
   (`schedules/occupancy.py:70-82`, `schedules/lighting.py:84-96`) rather than hand-setting four
   fields, so the `0 / 24 / 365 / factor` shape has one definition:

   ```python
   new_sched.annual_utilization_factor = mean(hbe_schedule.values())
   ```

4. Keep identifier / `display_name` / id-num alignment identical across branches. The collection
   is keyed on `identifier`, and `metr_schemas.py:1180/1203` and `xml_schemas.py:1853/1865`
   reference `schedule.id_num` — getting this wrong silently re-points patterns to other rooms.
5. Add R11: converting a PH-style pattern to its HB-style equivalent preserves
   `annual_utilization_factor` (`Office Workspace Open` → `0.313927` both ways). Better than
   asserting magic numbers — it tests the property the Phius protocol cares about.

**Verification gate:** `relAbs` == annual mean (0.2867 / 0.2886 / 0.7208); PH-style fixture
byte-identical; golden diffs confined to `BeginUtilization` / `EndUtilization` /
`AnnualUtilizationDays` / `RelativeAbsenteeism` and METr equivalents.

**Commit:** `fix(from_hbjson): derive occupancy and lighting utilization patterns from HB schedules when no PH operating periods are set`

---

## Phase 4 — lighting full-load hours as EFLH

**Status:** Complete — 5 boundary tests, Excel replay, and the 850-test full gate pass.

**Must follow Phase 3.** (Scope question resolved — see PRD "Resolved question".)

File: `PHX/model/schedules/lighting.py`

```python
@property
def full_load_lighting_hours(self) -> float:
    """Return the annual equivalent full-load lighting hours (EFLH), clamped 0-8760.

    EFLH is the load-weighted hour count -- SUM(hourly load fraction) over the year --
    not the operating window. Per the 2021 Phius protocol (see PRD), this value
    OVERRIDES the lighting utilization pattern in WUFI, so it must be the load.
    """
    return max(0, min(8760, self.annual_operating_hours * self.relative_utilization_factor))
```

**Verification gate:** boundaries (factor `0.0`, `1.0`, and a case exceeding 8760 pre-clamp);
39 15th St `8760 → 3010`; `Multi_Room_Complete` `8760 → 365` — confirm before recording, it
moves a residential model.

**Commit:** `fix(model): report lighting full-load hours as EFLH (load-weighted), not the operating window`

---

## Phase 5 — Goldens, validation, closeout

1. Re-record affected reference files. Review **field by field**; every changed value maps to a
   requirement row or it is a bug in the change.
2. Layer-5 negative checks.
3. Re-export the real project; confirm in METr.
4. Docs: `docs/reference/phx-model-reference.md` — the two occupancy channels, the
   mutual-exclusion invariant, the gating rule, and the EFLH convention.
   `docs/dev/exporter-patterns.md` if the schedule-fallback pattern generalizes. Cite the
   Phius thread (`phius-correspondance-background/`) for the EFLH convention — when this packet
   is archived that folder goes with it, so the public docs need the reasoning restated, not
   just a link.
6. Delete `scenario_harness*.py`. Fold outcomes into `context/`, move this folder to
   `planning/archive/`, update `planning/STATUS.md` and `archive/README.md`.
7. File the three adjacent upstream bugs (PRD "Adjacent bugs" 1, 2, 4). Bug 3 is already written
   up in `honeybee_grasshopper_ph_plus/planning/bug-fixes/`.

**Verification gate:** `python -m pytest tests/` fully green.

**Commit:** `test(reference): re-record WUFI-XML and METr-JSON goldens for Space loads and utilization patterns`

---

# Risk register

| Risk | Mitigation |
|---|---|
| Gate re-pointed at the merged room → every non-res project silently zeroed | Layer-2 invariant 1, written in Phase 1 before the fix exists |
| Gate reverted to per-room → phantom occupants on the commonest project shape | Layer-1 matrix; cases 03/05/06 are the discriminating rows |
| Group key reverted to `get_dwelling_obj()` → untagged rooms pool after round-trip | Layer-2 invariant 2 (no real model covers this) |
| Layer-1 builder drifts from the real GH component | Layer 3 against six committed real models |
| Index built from merged-room hosts → dwelling rooms without Spaces drop out | Phase 2b builds at project level; rationale recorded inline |
| Phase 4 before Phase 3 → FLH collapses to 0 | Ordering table; Phase 4 gate checks a nonzero result |
| Schedule id-num re-alignment in Phase 3 re-points patterns | Phase 3 step 4; golden diff scoped to five fields |
| Phase 0 conflated with the occupancy work in review | Separate commit, separate phase, explicit "no real-project exposure" note |
| Phases 3/4 move numbers on certified residential models | Ruled out by the WUFI A/B run - both fields inert for `BuildingCategory=1` (D10) |
