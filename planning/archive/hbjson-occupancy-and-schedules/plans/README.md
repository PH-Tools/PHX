# plans/ — phased implementation, agent-ready

Seven self-contained phase plans. Each one can be handed to a coding agent on its own: it states
its own context, exact edits, guardrails, tests, verification commands, and definition of done.

**Read `../PRD.md` for the *why*.** These files are the *how*. Where a phase depends on a
decision, it names the decision (D1-D10, in `../STATUS.md`) rather than re-arguing it.

## Order

| # | Plan | Ships | Depends on |
|---|---|---|---|
| 0 | [`PHASE-0-ach-ventilation-units.md`](PHASE-0-ach-ventilation-units.md) | **its own commit** | — |
| 1 | [`PHASE-1-test-scaffolding.md`](PHASE-1-test-scaffolding.md) | with Phase 2 | — |
| 2 | [`PHASE-2-space-occupancy-load.md`](PHASE-2-space-occupancy-load.md) | own commit | Phases 0, 1 |
| 3 | [`PHASE-3-schedule-hb-fallback.md`](PHASE-3-schedule-hb-fallback.md) | own commit | Phase 2 |
| 4 | [`PHASE-4-lighting-eflh.md`](PHASE-4-lighting-eflh.md) | own commit | **Phase 3 — never before** |
| 5 | [`PHASE-5-goldens-and-closeout.md`](PHASE-5-goldens-and-closeout.md) | own commit | 0-4 |
| 6 | [`PHASE-6-wufi-roundtrip-stabilization.md`](PHASE-6-wufi-roundtrip-stabilization.md) | own commit | Phase 5 R14 blocker |

Phase 4 before Phase 3 collapses lighting full-load hours from 8760 to **0**, because the
utilization factor is `0.0` until Phase 3 lands. This is the one ordering mistake that produces
a plausible-looking wrong number rather than a test failure.

## Global guardrails

Apply to every phase.

1. **Never widen the scope.** Each plan lists exactly the files it may touch. Anything else is
   a separate change, even if it looks broken. Four adjacent bugs are already catalogued in
   `../STATUS.md` — do not fix them here.
2. **The zone-level occupancy channel is untouchable.** `PhxZone.res_occupant_quantity`,
   `res_number_bedrooms`, `<OccupantQuantityUserDef>`, `loadsZ.nOcc`. These work. Every phase
   must leave them byte-identical.
3. **`tests/test_xl_replay/` must never move.** It records exact Excel cell writes. Any change
   there means the PHPP path was touched and the change is wrong.
4. **Read pre-merge state when gating on dwellings.** After `cleanup.merge_rooms()` the merged
   room reports `is_residential=True` and a summed `number_people` for *every* model — see
   `../STATUS.md` note 1. Use `_space.host`.
5. **Never A/B-test a WUFI-saved file.** WUFI rewrites `DataVersion`/`ProgramVersion`/`Scope`,
   roughly doubles the tag count, and silently drops sections it considers empty. Always work
   from raw PHX output. This destroyed test inputs three times during planning.
6. **Conventional commits.** They drive the semantic-release version bump on merge to `main`.
   Each phase states its exact commit message.
7. **Run the full suite before and after**, not just the new tests:
   ```
   python -m pytest tests/
   ```

## The golden-file mechanism does NOT protect you

`../PLAN.md` refers to reviewing golden diffs. Be aware of what actually exists today:

| test | what it really asserts |
|---|---|
| `tests/test_to_WUFI_xml/test_reference_cases/test_xml_output.py` | **`assert True`** — the comparison is commented out |
| `tests/test_to_METr_JSON/.../test_metr_json_output.py` | top-level **keys only**, no values |

So a whole-file golden comparison will not catch a regression, and an agent looking for a
failing golden diff will find nothing. **Phase 1 therefore adds targeted field-level assertions**
for exactly the fields each phase touches. Those assertions — not the reference files — are the
safety net. Do not "fix" the disabled comparison as part of this work; enabling it wholesale
will fail for unrelated pre-existing reasons and is its own project.

## Verification commands

```bash
# full suite
python -m pytest tests/

# this packet's tests
python -m pytest tests/test_from_HBJSON/test_create_rooms/ -v

# the Excel golden state (must be unchanged)
python -m pytest tests/test_xl_replay/ -v

# export the real reported project and inspect
PYTHONPATH=. python - <<'PY'
from PHX.from_HBJSON import read_HBJSON_file, create_project
p = "/Users/em/Dropbox/bldgtyp/2616 {IA} 39 15th St/14_HBJSON/39_15th_ST_260806.hbjson"
m = read_HBJSON_file.convert_hbjson_dict_to_hb_model(read_HBJSON_file.read_hb_json_from_file(p))
proj = create_project.convert_hb_model_to_PhxProject(m, _group_components=True, _merge_faces=False)
for v in proj.variants:
    for z in v.building.zones:
        for sp in z.spaces:
            print(f"{sp.display_name:34s} fa={sp.floor_area:8.2f} peak_occ={sp.peak_occupancy:7.2f}")
PY
```

## Test corpus

Six real Grasshopper models in `../HBJSON/`. Expected per-space occupancy totals after Phase 2:

| model | zone-level (A) | per-space (B) |
|---|---|---|
| `01_no_dwelling_no_occupancy` | 0.0 | **22.60** |
| `02_single_dwelling_no_occupancy` | 0.0 | **22.60** |
| `03_single_dwelling_set_occupancy` | 7.0 | **0.00** |
| `04_no_dwelling_set_occupancy` | 7.0 | **0.00** |
| `05_multiple_dwelling_set_occupancy` | 7.0 | **0.00** |
| `06_res_with_hallway` | 7.0 | **0.00** |

A per-**room** gate (the wrong implementation) produces `2.43`, `0.00`, `0.69`, `0.69` on models
03-06. If you see those numbers, the gate is per-room and must be fixed.
