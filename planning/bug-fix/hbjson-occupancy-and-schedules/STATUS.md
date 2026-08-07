# STATUS — hbjson-occupancy-and-schedules

**Status:** In progress — Phases 0-4 complete; Phase 5 next
**Last updated:** 2026-08-06

## Readiness

| phase | ready? | note |
|---|---|---|
| 0 — ACH ventilation 3600x | **Complete** | 4 focused cases + Excel replay + full suite green |
| 1 — test scaffolding | **Complete** | 26 focused tests + 819-test full gate green |
| 2 — Space occupancy + TODO | **Complete** | 44 focused tests + 82.31-person real-project check + 837-test full gate green |
| 3 — schedule fallback | **Complete** | 8 focused tests + Excel replay + 845-test full gate green |
| 4 — lighting EFLH | **Complete** | 5 boundary tests + Excel replay + 850-test full gate green |
| 5 — goldens + closeout | **Yes** | Phases 0-4 complete |

Phases 0-4 are complete. Phase 2 resolves the reported METr symptom. Phase 3 derives HB-style
occupancy and lighting schedules from their annual hourly means. Phase 4 reports lighting
full-load hours as EFLH. Phase 5 is next.

## Current state

Planning is complete. Phase 0 corrects the ACH double-conversion and distributes every Room
ventilation term by unweighted Space floor-area fraction. Phase 1 adds the durable six-model
scenario corpus, a non-residential HBJSON/WUFI/METr reference, synthetic occupancy fixtures,
pre-merge and untagged-group invariants, all-six GH anchors, and defect characterization. Phase
2 now indexes explicit occupancy from pre-merge Rooms, gates per dwelling group, and distributes
the HB People load without losing occupants when Spaces do not tile a Room. The 44 focused tests
pass, the reported real project exports 82.31 occupants, the residential occupancy fields remain
byte-identical in WUFI XML and METr JSON, and the full gate passes (837 passed, 3 skipped, 1
deselected). Phase 3 now derives HB-style occupancy and lighting patterns as `0/24/365` with the
annual hourly mean as the utilization factor while preserving PH-style output and schedule-ID
alignment. The reported office factor is `0.286712`; the Generic Office and residential factors
are `0.288562` and `0.720833`. The eight focused schedule tests, Excel replay invariant, and
full gate pass (845 passed, 3 skipped, 1 deselected); the only golden movement required by the
round-trip contract is `Multi_Room_Complete.xml` `RelativeAbsenteeism` `0.0 -> 0.7208333333333333`.
Phase 4 now reports lighting EFLH as `annual_operating_hours × relative_utilization_factor`,
clamped to 0-8760. Its five boundary tests pass; the reported office, Generic Office, and
residential schedules produce 3009.51 / 2555.39 / 365.00 hours, and exporter movement is confined
to `LightingFullLoadHours` / `lFLoadH`. The 39-test Excel replay invariant and the full gate also
pass (850 passed, 3 skipped, 1 deselected). Phase 5 remains unimplemented. Every design and scope
question is resolved (D1-D10), the last one by a WUFI A/B run.

The planning source for the non-residential reference contained the intended four office
`People` loads but no serialized PH Spaces; `check_room_has_spaces()` is a no-op. The durable
test fixture therefore adds one full-floor PH Space per Room so Phase 2 can produce and assert
the planned `NumberOccupants 0.0 -> nonzero` delta.

Source of the report: METr showed `Occupant quantity = 0` on all five utilization zones of a
NON-RESIDENTIAL office project (`2616 {IA} 39 15th St`).

## Confirmed defects

| # | Defect | State | Location | Real-project exposure |
|---|---|---|---|---|
| 0 | ACH ventilation flow understated 3600x | **Fixed — Phase 0** | `from_HBJSON/create_rooms.py` | **None** — 0 of 37 projects |
| 1 | Space occupancy load never populated | **Fixed — Phase 2** | `from_HBJSON/create_rooms.py` | Every model without explicit PH occupancy |
| 2 | No HB→PH fallback for occupancy/lighting schedules | **Fixed — Phase 3** | `from_HBJSON/create_schedules.py` | **Every** project |
| 3 | Lighting full-load hours are the window, not EFLH | **Fixed — Phase 4** | `model/schedules/lighting.py:117-127` | **Every** project |

Not affected (verified): PHPP write path, PPP write path, `from_WUFI_XML` import, and the whole
explicit zone-level occupancy channel (`PhxZone.res_occupant_quantity`).

## Decisions made

**D1 — Gating rule: explicit PH occupancy wins, evaluated per dwelling group.** A per-room gate
inverts the intent, because `set_res_occupancy.set_people_per_m2()` normalizes a dwelling's
occupants across the whole group. Verified: three of six real models leak under a per-room gate;
the standard SFH pattern (one dwelling, occupants on bedrooms only) leaks 2.43 phantom occupants.

**D2 — Group key is `num_dwellings >= 1`, not `get_dwelling_obj()`.** The latter does not survive
an HBJSON round-trip — `PhDwellings.default()` mints a per-process `uuid4`, so every untagged
room shares the serialized identifier and pools into one group.

**D3 — `number_people` stays non-nullable.** An explicit `0` is already carried by
`people_per_area`. Making it nullable needs None-guards in three places plus a GH change, and
every existing HBJSON already serializes `0.0`.

**D4 — Case 02 behavior accepted.** Dwellings tagged but occupancy never set → fall back to the
Honeybee-Energy program. Confirmed intended.

**D5 — No warning needed.** An earlier draft warned on "dwelling-tagged but no explicit people".
The group gate makes those cases correct outright and D4 makes the remainder intended.

**D6 — Option B for distributing occupants across Spaces**, and the pre-existing ventilation
`TODO` resolved the same way. Option B strictly dominates: algebraically identical to Option A
when Spaces tile the room, correct when they don't.

**D7 — `RelativeAbsenteeism` is a utilization factor, not an absence factor.** PHX's existing
mapping is correct; no change. Settled by the Phius standards library (an open office at `1.0`,
a public restroom at `0.1`) — the reverse reading is absurd.

**D8 — Defects 2 and 3 are one protocol.** `Defect 2 shape × Defect 3 multiplication = 8760 ×
mean = EFLH`, exactly what the 2021 Phius thread specifies. Not two independent judgment calls.

**D9 — Phase 0 ships as its own commit.** Unrelated to the reported symptom, different blast
radius, must be reviewable alone.

**D10 — Defects 2 and 3 apply to all models, residential included.** The WUFI A/B run showed
both fields are inert for `BuildingCategory=1`, so there is no re-certification risk and no
reason to gate by building category. Golden fields change; residential WUFI results do not.

## Next step

Begin [`plans/PHASE-5-goldens-and-closeout.md`](plans/PHASE-5-goldens-and-closeout.md).

The six phase plans in [`plans/`](plans/) are the handoff surface — each is self-contained and
can be given to a coding agent on its own.

## Resolved question — do Defects 2 and 3 apply to residential?

**Answer: the fields are inert on residential. Apply uniformly; no re-certification concern.**

WUFI Plus Free 3.6.0.1, case 03 (reported by WUFI as *"Passive house: Residential"*), four
variants isolating each field. Screenshots in `WUFI/`.

| variant | `relAbs` | EFLH | Heating | Cooling | Source | Site |
|---|---|---|---|---|---|---|
| A | 0.0 | 8760 | 153.66 | 12.22 | 604 | 5.28 |
| B1 lighting only | 0.0 | **2555** | 153.66 | 12.22 | 604 | 5.28 |
| B2 absenteeism only | **0.7208** | 8760 | 153.66 | 12.22 | 604 | 5.28 |
| B corrected | **0.7208** | **2555** | 153.66 | 12.22 | 604 | 5.28 |

Identical to the last digit. Two independent confirmations: site energy of 5.28 kWh/m²a rules
out the 92.4 kWh/m²a the lighting load would have contributed; and WUFI stripped
`LightingFullLoadHours` and `NumberOccupants` on save, returning A and B1 **byte-identical**.

Full write-up, including the limits of the test, in `PRD.md` → "Resolved question".

## Blockers

None external.

## Test corpus

Six Grasshopper models in [`HBJSON/`](HBJSON/), definitions in
[`grasshopper-model/`](grasshopper-model/), and durable test copies in
`tests/reference_files/from_grasshopper_tests/hbjson/occupancy_scenarios/`. Full table in
`PRD.md`. Highlights:

- **03** anchors the group-uniform density invariant to 8 decimal places
  (`7 / 0.720833 / 400 = 0.02427746`, actual `0.02427746`).
- **04** is the contrast case — untagged rooms normalize *per room*, tagged *per group*.
- **05** proves dwelling-group separation (two dwellings, identical geometry, different densities).

**Known gap:** no real model discriminates `get_dwelling_obj` from `num_dwellings >= 1`, because
every untagged zero-people room here also has `people_per_area = 0.0`. Covered by a synthetic
unit test (PLAN layer 2, invariant 2) rather than another export.

## Notes and limits

1. **The gate must read pre-merge state.** `merge_occupancies()` both forces
   `PhDwellings(max(count, 1))` (`cleanup.py:217`) and sums `number_people` onto the merged room
   (`:260`). `_space.host` is the original un-merged room and the only valid source. Guarded by
   an invariant test — do not rely on the code comment alone.
2. **Build the dwelling index at project level** from `_hb_model.rooms`, not from the merged
   room's space hosts. A dwelling room with `number_people` but no PH Spaces would be missing,
   dropping the group total to zero.
3. **Test-drift risk.** PHX cannot import `honeybee_grasshopper_ph` (Rhino `System` bindings), so
   fast tests reconstruct post-*Set Occupancy* state rather than producing it. Mitigated by the
   six committed real models (test layer 3).
4. **The Phius email thread is filed** in `phius-correspondance-background/` and is the sole
   authority for Defects 2 and 3. **Read order is 01 → 03 → 02** — the filenames do not sort
   chronologically (Sep 24 → Sep 28 → Oct 7). Phase 4 rests entirely on the Oct 7 line,
   *"the EFLH overrides the lighting"*.
5. **Explicit `0` destroys HB-side occupancy.** Running *Set Occupancy* with `0` also zeroes
   `people_per_area`, so the room loses its E+ people load. Pre-existing upstream behavior; it is
   *why* the fallback is safe for the hallway/retail cases, but it is a modeling wart.
6. **`merge_occupancies()` computes a dead area-weighted `people_per_area`** (`cleanup.py:257`)
   that nothing reads. Stays dead under this design. Flagged, not removed.
7. **8 project HBJSONs fail to load** with `KeyError: 'divisions'` in `honeybee_energy_ph`
   material deserialization — old files against the current package. Unrelated; means those
   models cannot be re-exported without a re-save.
8. **Evidence that residential per-space occupancy stays zero is WUFI's own output.**
   `_ridgeway.xml` (206 spaces) and `_la_mora.xml` carry `NumberOccupants=0.0` throughout while
   `OccupantQuantityUserDef` is 191 / 123. Inference from saved files, not documentation.
9. **`School.xml` is not usable as a non-residential reference** — `BuildingCategory=2`, but both
   `LoadPerson` entries carry `NumberOccupants=0.0` *and* `FloorAreaUtilizationZone=0.0`. A stub.
10. **WUFI discards all-zero `LoadsPersonsPH` / `LoadsLightingsPH` blocks on re-save.** Observed
    on the superseded case-03 round-trip. `_ridgeway.xml` keeps its 206 zero-occupant entries
    because they carry real `FloorAreaUtilizationZone` values and pattern references. Once
    Defect 1 lands and occupants are nonzero, these sections will start surviving the round-trip
    on models where they currently vanish — a change in WUFI's saved file, not only in ours.
11. **Never A/B-test a file that has been through WUFI.** It rewrites `DataVersion`,
    `ProgramVersion`, `Scope`, roughly doubles the tag count, and drops sections it considers
    empty. Always edit the raw PHX export. This destroyed the test inputs twice; the four
    `WUFI/AB_case03_*.xml` files have been regenerated from source and set read-only, and the
    `.png` screenshots are the result record.
12. **The METr A/B pair was never run.** `METr/AB_case03_*.json` are ready, but METr currently
    errors on this model owing to a pre-existing, unrelated foundations issue. Worth re-running
    once that is fixed — METr surfaced the original symptom and may consume these fields
    differently from WUFI.

## Adjacent bugs to file (PLAN Phase 5)

| # | Bug | Repo | State |
|---|---|---|---|
| 1 | `get_dwelling_obj()` breaks across HBJSON round-trip | `honeybee_ph` | To file |
| 2 | `_num_people` list padding repeats the last value | `honeybee_grasshopper_ph` | To file |
| 3 | `Infiltration from ACH` 50Pa output unit mismatch | `honeybee_grasshopper_ph_plus` | **Written up** — `planning/bug-fixes/infiltration-from-ach-units.md` |
| 4 | `FloorAreaUtilizationZone`: WUFI writes `floor_area`, METr writes `weighted_floor_area` | PHX | To file |
