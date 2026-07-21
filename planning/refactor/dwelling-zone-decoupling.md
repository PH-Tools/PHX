# Refactor: Decouple "Dwelling" from `Room.zone` (PHX side)

**Status:** Implemented (2026-07-21) — awaiting `honeybee_grasshopper_ph` (step 3), then the
`hbph_test_models.gh` end-to-end run.
**Date:** 2026-07-21
**Author:** Ed May + Claude
**Kind:** Cross-repo refactor. PHX is the **downstream consumer**. Its role here is
(a) to prove the upstream change is safe, and (b) to retire a duplicated helper.

**Companion docs (same slug in each repo):**
- `honeybee_ph/planning/refactor/dwelling-zone-decoupling.md` — **primary**; owns the shared
  helper, full evidence, and the design decision. Read it first.
- `honeybee_grasshopper_ph/planning/dwelling-zone-decoupling.md` — root cause (GH components)

**Blocked on:** `honeybee_ph` shipping `honeybee_energy_ph/dwellings.py`.

---

## 1. Why PHX is in scope

Two reasons — and note that **neither is a bug in PHX**.

1. **Clearance.** The upstream fix removes a `Room.zone` write in
   `HBPH - Set Dwelling`. Before that ships, we must be certain PHX (and therefore PHPP,
   WUFI XML, METr, and PPP) does not depend on it. **It does not** — see §2.
2. **Deduplication.** `cleanup.all_unique_ph_dwelling_objects()` is one of three
   independent implementations of "aggregate by dwelling identity" across the toolkit. It
   should delegate to the shared helper instead. See primary doc §1.

---

## 2. Clearance finding: PHX never reads `Room.zone`

```
grep -rn "\.zone\b" --include="*.py" PHX/     ->  0 hits
```

Swept across the whole repo (excluding `.venv`/`build`). **PHPP, WUFI XML, METr, and PPP are
all completely blind to `Room.zone`.** Removing the upstream write has zero effect on any
certification output.

PHX's grouping hierarchy is entirely separate:

```
HB Rooms
  └─ grouped by room.properties.ph.ph_bldg_segment.identifier    (create_project.py:35-51)
       └─ cleanup.merge_rooms()  ->  ONE merged HB Room per segment
            └─ create_variant.from_hb_room()  ->  1 PhxVariant -> 1 PhxZone
                 └─ HB-PH Spaces carried through -> PhxSpaces (TFA rooms)
```

`merge_rooms()` keeps only faces with `Outdoors` / `Ground` / `Adiabatic` boundary
conditions and discards interior `Surface` faces. **PHX already collapses each segment to a
single zone geometrically** — the caller's Room subdivision is invisible to it. Whether a
house is modeled as 1 Room or 6 changes nothing in WUFI/PHPP.

### How dwelling count actually reaches the outputs

```
PhDwellings  (identity = uuid4 str; __hash__/__eq__ on .identifier)
  └─ cleanup.all_unique_ph_dwelling_objects()      set() dedup by identity   :196-216
       └─ Σ num_dwellings over UNIQUE objects -> merged_ph_dwellings         :234-238
            └─ assigned to merged People                                     :282
                 └─ PeoplePhProperties.number_dwelling_units
                      ├─ PhxZone.res_number_dwellings          create_building.py:314
                      └─ ph_building_data.num_of_units         create_variant.py:296
                           ├─ WUFI : XML_Node("NumberUnits", …)  to_WUFI_XML/xml_schemas.py:373
                           ├─ PHPP : input_type="num_of_units"   PHPP/phpp_app.py:269
                           ├─ METr : "nUnits": … or 1            to_METr_JSON/metr_schemas.py:1376
                           └─ PPP  : num_units = … or 1          to_PPP/ppp_schemas.py:150
```

**The dedup is by object identity, and that is load-bearing.** *HBPH - Set Dwelling* creates
**one** `PhDwellings` per GH branch and attaches that same object to every Room in the
branch. PHX dedups six references to one object → `num_of_units = 1`. If each Room instead
carried its own `PhDwellings(1)`, PHX would sum to **6 dwelling units** in WUFI and PHPP.

This is exactly the mechanism the shared helper formalizes — so adopting it makes the
HB-side and PHX-side grouping provably the same logic, rather than two parallel
implementations that merely happen to agree.

`num_dwellings` also drives real Phius load math, not just a reported count
(`honeybee_energy_ph/load/ph_equipment.py:828-874` step functions on unit count;
`load/phius_residential.py` scales TV/lighting/garage loads). Getting it wrong is a silent
energy error.

---

## 3. Changes

### 3.1 Delegate `all_unique_ph_dwelling_objects()` to the shared helper

`PHX/from_HBJSON/cleanup.py:196-216` becomes a thin wrapper over
`honeybee_energy_ph.dwellings.unique_dwelling_objects()`, or is deleted and its call site at
`:236` switched to `total_dwelling_count()`.

Behavior must be **identical**. Two details to preserve:

- The existing `try/except MissingEnergyPropertiesError` skip
  (`PHX/from_HBJSON/_type_utils.py:30`, `get_room_people()` at `:175`) — the shared helper
  handles People-less Rooms by falling back to `room.identifier`, so the semantics must be
  reconciled deliberately, not assumed. For *counting*, a People-less Room must contribute
  **zero**, not a phantom dwelling.
- `max(total_ph_dwellings, 1)` at `:238` stays. It floors non-residential segments at one
  unit and is relied on downstream (`or 1` guards in the METr and PPP writers).

### 3.2 Landing order

**PHX lands second of three (decided 2026-07-21):**

```
1. honeybee_ph  →  deploy/install  →  2. PHX  →  deploy/install  →  3. honeybee_grasshopper_ph
```

PHX goes **before** the Grasshopper repo deliberately. It is the only one of the three with
real test coverage, so it validates the shared helper against golden `NumberUnits` values
while the GH components are still untouched — isolating a helper defect from a component
defect. If both landed together, a broken unit count would be ambiguous between the two.

Each repo must be released and installed before the next begins.

This work is still **low-risk**: PHX is already correct, and this is deduplication only. But
it is no longer "deferrable last" — it is the verification gate for the shared helper.

---

## 4. Verification

PHX has real test coverage, so this is the strongest gate in the whole refactor.

1. **Full `pytest` suite green** — especially `tests/test_from_HBJSON/`,
   `tests/test_to_WUFI_xml/`, `tests/test_to_METr_JSON/`, `tests/test_to_PPP/`.
2. **Golden-value check on `NumberUnits`.** Before/after comparison of emitted WUFI XML for:
   - an SFH model (N Rooms, one shared `PhDwellings(1)`) → `NumberUnits` **1**
   - an MF model (per-unit `PhDwellings`) → `NumberUnits` = actual unit count
   - a non-residential segment → `NumberUnits` **1** (the `max(…, 1)` floor)
3. **End-to-end from Grasshopper** — `tests/_source_gh/hbph_test_models.gh`. This is the only
   test that exercises the GH components and PHX together, and therefore the only one that
   catches a regression in the upstream `set_dwelling.py` change. Run it **after** the GH
   repo changes land.
4. **Regression guard:** confirm no `.zone` reference reappears —
   `grep -rn "\.zone\b" --include="*.py" PHX/` must stay at 0 hits.

---

## 5. Definition of Done

- [x] `honeybee_ph` helper shipped and importable — **honeybee-ph 1.33.30** on PyPI
- [x] Dependency floor raised to `>=1.33.30`; `uv.lock` + venv synced (venv was stale at 1.33.24)
- [x] `cleanup.all_unique_ph_dwelling_objects()` **removed**; `merge_occupancies()` calls
      `total_dwelling_count()` (single caller, no external importers — verified across all repos)
- [x] `max(total, 1)` floor preserved; People-less Rooms contribute 0
- [x] Full pytest suite green — **750 passed, 3 skipped, 1 deselected** (baseline 741 + 9 new)
- [x] `NumberUnits` equivalence proven old-vs-new across 7 configurations (§4.2)
- [x] Regression guard: `grep -rn "\.zone\b" PHX/` → **0 hits**
- [x] `context/ARCHITECTURE.md` — Room grouping / dwelling counting / `Room.zone` notes
- [ ] `hbph_test_models.gh` end-to-end — **run after the GH changes land** (step 3)
- [ ] Row updated in `planning/STATUS.md`
- [ ] On completion of all three repos: move to `planning/archive/dwelling-zone-decoupling/`

### Equivalence result (2026-07-21)

The old `all_unique_ph_dwelling_objects()` was re-implemented verbatim and compared against
the new helper. `NumberUnits` is the value that actually reaches the writers, after the
`max(total, 1)` floor:

| Case | OLD | NEW | NumberUnits |
|---|---|---|---|
| SFH: 6 Rooms, one shared `PhDwellings(1)` | 1 | 1 | 1 |
| MF: 4 Rooms, distinct `PhDwellings(1)` | 4 | 4 | 4 |
| MF block: 1 Room holding `PhDwellings(4)` | 4 | 4 | 4 |
| Mixed: shared(2) × 2 Rooms + distinct(3) | 5 | 5 | 5 |
| Non-res: Rooms with no People load | 0 | 0 | **1** (floor) |
| Untagged: People, but default `PhDwellings` | 0 | 0 | **1** (floor) |
| Empty Room list | 0 | 0 | n/a |

Identical in every case. Behavioral differences, both improvements:

1. The old version returned `list(set(...))` — **non-deterministic order**. The new helper
   returns first-appearance order. Irrelevant to the sum, but now reproducible.
2. The old version relied on `MissingEnergyPropertiesError` to skip People-less Rooms; the
   new helper returns `None` from `get_dwelling_obj()` for no-energy / no-People / default
   singleton alike. Same totals, one predicate instead of an exception path.

### New coverage

`tests/test_from_HBJSON/test_cleanup/test_merge_occupancies.py` — 9 tests. `merge_occupancies()`
previously had **zero** direct coverage despite producing a certification-critical number.
Includes an explicit regression guard that 4 un-tagged Rooms do not report 4 dwelling units.

---

## 6. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Dwelling counts shift in WUFI/PHPP/METr output | **High** | §4.2 golden-value check; this is the whole reason PHX is in scope |
| People-less Rooms start contributing a phantom dwelling | Medium | Explicit reconciliation in §3.1; test case |
| `max(…, 1)` floor dropped → non-res segments report 0 units | Medium | Explicit DoD item |
| Shared helper's py2.7 style trips PHX linting/typing | Low | PHX is 3.10+; importing a 2.7-style module is fine, but `mypy` may need a stub |

---

## 7. Note for future readers

If you are here because dwelling counts look wrong in WUFI or PHPP, the chain is in §2. The
single most likely cause is **`PhDwellings` object identity not being shared** across the
Rooms of one dwelling — the count is a sum over *unique objects*, so duplicating the object
duplicates the dwelling. Check that the Rooms genuinely reference the same instance, not
merely equal values.
