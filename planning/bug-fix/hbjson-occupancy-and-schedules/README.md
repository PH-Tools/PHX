# hbjson-occupancy-and-schedules

**Status:** In progress — Phases 0-3 complete; Phase 4 next
**Opened:** 2026-08-06

Four defects were identified in the `from_HBJSON` conversion path. At packet opening, three
caused PHX models built from HBJSON to export **zero per-space occupants** and a **degenerate utilization pattern**
(`0-24 h`, `365 d`, relative factor `0.0`, lighting full-load hours `8760`) to WUFI-Passive XML
and METr JSON. The fourth is an unrelated pre-existing bug found in the same function.

Found while investigating a NON-RESIDENTIAL office project (`2616 {IA} 39 15th St`) that
exported `Occupant quantity = 0` for all five utilization zones in METr.

| # | Defect | State | Real-project exposure |
|---|---|---|---|
| 0 | ACH ventilation flow understated **3600x** | **Fixed — Phase 0** | **None** — 0 of 37 projects |
| 1 | Space occupancy load never populated | **Fixed — Phase 2** | Every model without explicit PH occupancy |
| 2 | No HB→PH fallback for occupancy/lighting schedules | **Fixed — Phase 3** | **Every** project |
| 3 | Lighting full-load hours are the window, not EFLH | Open — Phase 4 | **Every** project |

## Read order

1. [`PRD.md`](PRD.md) — the occupancy channels, all four defects, the **gating rule** and its
   derivation, the 2021 Phius protocol, the test corpus, requirements, and the resolved question.
2. [`PLAN.md`](PLAN.md) — the five-layer test strategy, then six phases with verification gates.
3. [`STATUS.md`](STATUS.md) — decisions made (D1-D10), readiness, limits, adjacent bugs.
4. [`plans/`](plans/) — **six self-contained, agent-ready phase plans.** Each states its own
   context, exact edits, guardrails, tests, verification commands, definition of done, and
   commit message. This is the handoff surface; `PLAN.md` is the overview it expands.

Background: [`phius-correspondance-background/`](phius-correspondance-background/) holds the
Sep-Oct 2021 email thread with Al Mitchell (Phius) that defines the utilization-pattern and EFLH
protocol — the sole authority for Defects 2 and 3. **Read order is 01 → 03 → 02**; the filenames
do not sort chronologically.

## The rule, in one line

> **Explicit PH occupancy wins, evaluated per dwelling group.** If any room in a Space's
> dwelling group states `number_people`, that dwelling is expressed at the zone level and every
> Space in the group exports `0`. Otherwise, derive from the Honeybee-Energy load.

The per-**group** part is load-bearing: a per-room gate leaks phantom occupants on three of our
six real test models, including the commonest shape we build (one dwelling, occupants entered on
the bedrooms only). See `PRD.md` → "The gating rule".

## Test corpus

Six purpose-built Grasshopper models — real component output, no cross-repo import.

- [`HBJSON/`](HBJSON/) — the exported models (the fixtures)
- [`grasshopper-model/`](grasshopper-model/) — the `.ghx` definition and per-case screenshots

The six HBJSONs are also copied to the durable test fixture tree at
`tests/reference_files/from_grasshopper_tests/hbjson/occupancy_scenarios/`; the Phase 1 tests
read that copy so archiving this planning packet cannot break the suite.

| file | shape | per-room gate | per-group gate |
|---|---|---|---|
| `01_no_dwelling_no_occupancy` | untagged, no occupancy | 22.60 | **22.60** ✓ |
| `02_single_dwelling_no_occupancy` | 1 dwelling, no occupancy | 22.60 | **22.60** ✓ |
| `03_single_dwelling_set_occupancy` | 1 dwelling, occupancy on subset | 2.43 ✗ | **0.00** ✓ |
| `04_no_dwelling_set_occupancy` | untagged, occupancy set | 0.00 | **0.00** ✓ |
| `05_multiple_dwelling_set_occupancy` | 2 dwellings | 0.69 ✗ | **0.00** ✓ |
| `06_res_with_hallway` | 2 dwellings + untagged non-res | 0.69 ✗ | **0.00** ✓ |

## A/B pairs — the resolved question

[`WUFI/`](WUFI/) and [`METr/`](METr/) hold the pairs that answered the last open question: does
the Phius utilization-pattern protocol apply to residential models?

**Answer: the fields are inert on residential** — all four WUFI variants returned identical
results (heating 153.66, cooling 12.22, source 604, site 5.28). Defects 2 and 3 therefore apply
to all models with no re-certification risk. Screenshots in `WUFI/*.png`; full write-up in
`PRD.md` → "Resolved question". The METr pair is ready but unrun (METr errors on this model over
an unrelated pre-existing foundations issue).

| target | A (as exported today) | B (protocol-corrected) |
|---|---|---|
| WUFI | `AB_case03_A_as_exported.xml` | `AB_case03_B_corrected.xml` |
| METr | `AB_case03_A_as_exported.json` | `AB_case03_B_corrected.json` |

| field | A | B | source |
|---|---|---|---|
| `RelativeAbsenteeism` / `relAbs` | `0.0` | `0.7208` | `hbph_sfh_Occupant_Presence` annual mean |
| `LightingFullLoadHours` / `lFLoadH` ×4 | `8760` | `2555` | `Generic Office Lighting` mean 0.2917 × 8760 |

`NumberOccupants` / `lPersZ[].nOcc` stay `0.0` in both — correct, since case 03 is residential
and the zone-level channel carries the occupancy (`7`). Defect 1 is not under test here.

> `03_single_dwelling_set_occupancy{,_EDITED}.xml` are a **superseded** first attempt — a WUFI
> re-save rather than PHX output, from which WUFI had already dropped the sections under test.
> See `PRD.md` → "Why the first A/B attempt could not work". **Always edit the raw PHX export.**
> The METr export was unaffected: it is clean PHX output with every field intact.

Supporting: [`scenario_harness.py`](scenario_harness.py) and
[`scenario_harness_sfh.py`](scenario_harness_sfh.py) are throwaway scripts that produced the
scenario matrix by loading the **real** `honeybee_grasshopper_ph` component logic by file path.
They make the matrix reproducible rather than asserted. Delete both when this packet is archived.

```
PYTHONPATH=. .venv/bin/python planning/bug-fix/hbjson-occupancy-and-schedules/scenario_harness.py
PYTHONPATH=. .venv/bin/python planning/bug-fix/hbjson-occupancy-and-schedules/scenario_harness_sfh.py
```

## Scope

**In:** populate `PhxSpace.occupancy.load.people_per_m2` wherever no explicit PH occupancy was
set; add the HB→PH-style fallback for occupancy and lighting schedules; report lighting
full-load hours as EFLH; fix the ACH double-conversion and resolve the pre-existing
`# TODO: Unweighted or weighted?` in the same function.

**Out:** the zone-level occupancy channel (`PhxZone.res_occupant_quantity`) — it works and must
stay byte-identical; the PHPP and PPP write paths (verified to consume neither Space occupancy
nor these schedules); `from_WUFI_XML` import; and the four adjacent upstream bugs listed in
`STATUS.md`, which are filed separately.
