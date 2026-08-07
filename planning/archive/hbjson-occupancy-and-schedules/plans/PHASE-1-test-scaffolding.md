# Phase 1 — Test scaffolding, fixture builder, non-residential reference case

**No behavior change.** Pure test infrastructure. Ships with Phase 2.

**Depends on:** nothing (can run in parallel with Phase 0).

---

## Why this phase exists

Two reasons, both load-bearing.

**1. There is no non-residential reference case in the repo.** That is *why* Defect 1 survived
undetected for so long — every fixture is residential, and residential occupancy flows through
a different channel that works correctly.

**2. The golden-file mechanism does not protect us.** See `README.md` → "The golden-file
mechanism does NOT protect you". `test_xml_output` is `assert True`; the METr test compares
top-level keys only. A whole-file comparison will not catch a regression, so this phase builds
**targeted field-level assertions** instead. Those are the actual safety net for Phases 2-4.

---

## Files you may create / touch

```
tests/conftest.py                                                   (extend fixtures)
tests/test_from_HBJSON/test_create_rooms/__init__.py                (may exist from Phase 0)
tests/test_from_HBJSON/test_create_rooms/_occupancy_fixtures.py     (new — layer 1 builder)
tests/test_from_HBJSON/test_create_rooms/test_occupancy_invariants.py     (new — layer 2)
tests/test_from_HBJSON/test_create_rooms/test_gh_invariant_real_hbjson.py (new — layer 3)
tests/test_from_HBJSON/test_create_rooms/test_characterization.py    (new — pins today)
tests/reference_files/from_grasshopper_tests/hbjson/                 (add the non-res fixture)
```

No `PHX/` source changes in this phase.

---

## Step 1 — add the non-residential reference fixture

Copy `../HBJSON/01_no_dwelling_no_occupancy.hbjson` into
`tests/reference_files/from_grasshopper_tests/hbjson/Non_Residential_Office.hbjson`.

Why this one: four untagged rooms on `Generic Office Program` with a real
`people_per_area = 0.0565` and no dwelling tags — exactly the shape that currently exports zeros.
Expected per-space occupancy after Phase 2 is **22.60** total (4 rooms x 100 m² x 0.0565).

Wire it into both fixtures in `tests/conftest.py` (`to_xml_reference_cases` at ~line 151 and
`to_metr_json_reference_cases` at ~line 170), following the existing tuple pattern. Generate its
reference XML/JSON against **current (buggy) behavior** and commit them, so Phase 2's diff is
legible: `NumberOccupants` goes `0.0` → nonzero and nothing else moves.

---

## Step 2 — the layer-1 fixture builder

`tests/test_from_HBJSON/test_create_rooms/_occupancy_fixtures.py`

PHX **cannot import `honeybee_grasshopper_ph`** — its package `__init__` pulls Rhino/`System`
bindings. So the fast tests must *reconstruct* the state that *HBPH - Set Occupancy* leaves
behind. That encodes an assumption, which layer 3 exists to anchor.

```python
@dataclass
class RoomSpec:
    name: str
    floor_area_m2: float
    number_people: float
    dwelling: str | None      # group tag; None = untagged (own group of one)


def build_rooms(specs: list[RoomSpec], *, avg_occ_rate: float, hb_program: str) -> list[Room]:
    """Build HB-Rooms in the state that 'HBPH - Set Occupancy' leaves behind.

    INVARIANT MIRRORED FROM honeybee_grasshopper_ph
    set_res_occupancy.set_people_per_m2():

      * rooms sharing a `dwelling` tag share ONE PhDwellings instance, num_dwellings=1
      * every room in a group carries the SAME people_per_area:
            group_total_number_people / avg_occ_rate / group_total_floor_area
        -- regardless of that individual room's own number_people
      * a group totalling zero people gets people_per_area = 0.0
      * untagged rooms keep num_dwellings=0 and their HB program's people_per_area

    Anchored by test_gh_invariant_real_hbjson.py (layer 3). If that test starts
    failing, this builder is stale and every expectation built on it is suspect.
    """
```

The group-uniform density is the whole reason the gate must be per-group rather than per-room
(D1). Get this builder wrong and every downstream expectation is wrong in the same direction.

---

## Step 3 — layer 2, implementation-independent invariants

`tests/test_from_HBJSON/test_create_rooms/test_occupancy_invariants.py`

These hold *today* (1 and 2 trivially; 3 because per-space occupancy is always zero) and become
load-bearing after Phase 2. They are nets, not discovery tests. Write them now, before the fix
exists — that is the point.

### Invariant 1 — merge-trap guard (R5)

```python
def test_gate_must_read_pre_merge_state():
    """The merged room is unusable as a dwelling-occupancy source.

    cleanup.merge_occupancies() forces PhDwellings(max(count, 1)) (cleanup.py:217)
    AND sums number_people onto the merged room (cleanup.py:260). So a merged
    NON-residential model reports is_residential=True with a summed occupancy.
    Only `_space.host` -- the original un-merged room -- is a valid source.
    """
    # 1. build a multi-room NON-residential model
    # 2. run cleanup.merge_rooms()
    # 3. assert the merged room reports is_residential is True   <- documents WHY it is unusable
    # 4. assert each Space's .host still reports its ORIGINAL number_people / num_dwellings
```

Without this, re-pointing the gate at the merged room looks harmless in review and silently
zeroes every non-residential project.

### Invariant 2 — untagged rooms are not pooled (R6)

```python
def test_untagged_rooms_are_each_their_own_group():
    """Two untagged rooms: explicit people on one, nonzero program density on the other.
    The second must still fall back to the HB load.

    After an HBJSON round-trip, PhDwellings.default() no longer matches --
    it mints a fresh uuid4 per process -- so every untagged room shares the
    SERIALIZED default identifier. Keying on get_dwelling_obj() would pool them
    into one group and suppress the second room. Key on num_dwellings >= 1 (D2).
    """
```

**No real model in the corpus covers this** — every untagged zero-people room there also has
`people_per_area == 0.0`, so the answers coincide. This synthetic test is the only thing that
catches it.

### Invariant 3 — channels are mutually exclusive (R15)

```python
def test_occupancy_channels_are_mutually_exclusive():
    """For every fixture: if a zone has res_occupant_quantity > 0, every Space in
    that zone must have peak_occupancy == 0. Occupancy is expressed either at the
    zone level OR per-space, never both -- emitting both double-counts."""
```

The durable regression net. It survives any future re-implementation of the gate.

### Invariant 4 — totals are preserved (R7, R0b)

```python
def test_space_totals_preserve_room_totals():
    """Sum over Spaces == the HB-Room total, for occupancy and for ventilation."""
```

### Invariant 5 — `DwellingOccupancyIndex` units

Placeholder in this phase (the class arrives in Phase 2); write the group-keying, untagged
handling, totals, and empty-model cases as soon as it exists.

---

## Step 4 — layer 3, anchor against real component output

`tests/test_from_HBJSON/test_create_rooms/test_gh_invariant_real_hbjson.py`

Asserts the layer-1 builder's assumption against the six committed models in `../HBJSON/`. Real
Grasshopper output, no cross-repo import, runs in CI.

```python
def test_group_uniform_density_invariant():
    """03: one dwelling, 4 rooms, occupancy on a subset -> uniform group density.

    group total 7 people, 400 m2, occupancy schedule mean 0.720833
    predicted 7 / 0.720833 / 400 = 0.02427746
    """
    # every one of the 4 rooms must carry 0.02427746, despite number_people
    # being 0, 1, 2 and 4 respectively


def test_untagged_rooms_normalize_per_room():
    """04: same occupancy figures, NO dwelling tag -> per-room densities
    0.0, 0.01387, 0.02775, 0.05549 (n_ppl / 0.720833 / 100)."""


def test_separate_dwellings_normalize_independently():
    """05: two dwellings, identical geometry -> different densities
    1/0.7208/200 = 0.00694  and  6/0.7208/200 = 0.04162."""
```

03-vs-04 is the contrast pair that proves group-vs-room normalization; 05 proves group
separation.

---

## Step 5 — characterization tests (pin today's behavior)

`tests/test_from_HBJSON/test_create_rooms/test_characterization.py`

Label each with the defect it pins, so Phase 2/3/4 know exactly which expectations to flip.

```python
def test_DEFECT_1_space_peak_occupancy_is_currently_zero(): ...       # -> nonzero in Phase 2
def test_DEFECT_2_schedule_with_no_ph_periods_is_degenerate(): ...    # (0, 24, 365.0, 0.0)
def test_DEFECT_3_full_load_lighting_hours_is_currently_8760(): ...   # -> EFLH in Phase 4
```

---

## Guardrails

- **No `PHX/` source changes.** If a test cannot be written without one, the plan is wrong —
  stop and flag it.
- **Do not enable the disabled golden comparison** in `test_xml_output.py`. It will fail for
  unrelated pre-existing reasons. Targeted field assertions are the mechanism here.
- Existing reference files must not change in this phase.

---

## Verification gate

```bash
python -m pytest tests/                # full suite green, including the new tests
git diff --stat tests/reference_files/ # ONLY the new non-res fixture + its goldens
```

---

## Definition of done

- [ ] `Non_Residential_Office.hbjson` committed and wired into both `conftest.py` fixtures
- [ ] Its reference XML/JSON committed, generated against **current** behavior
- [ ] `_occupancy_fixtures.build_rooms()` exists with the invariant docstring
- [ ] Layer-2 invariants 1-4 written and passing
- [ ] Layer-3 anchors written and passing against all six real models
- [ ] Characterization tests written and passing, labelled by defect
- [ ] No `PHX/` source file modified
- [ ] No existing reference file modified

## Commit

```
test(from_hbjson): add non-residential reference case and occupancy gate scaffolding
```
