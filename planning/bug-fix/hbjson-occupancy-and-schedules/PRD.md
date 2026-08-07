# PRD — HBJSON Space load and utilization-schedule defects

**Status:** In progress — Phase 0 complete; Phase 1 next
**Last updated:** 2026-08-06

## Problem

A NON-RESIDENTIAL office project (`2616 {IA} 39 15th St`, 5 floors, 1,456.6 m² iCFA)
exported to METr JSON with `Occupant quantity = 0` on every one of its five utilization
zones, and a single utilization pattern reading `Begin 0 / End 24 / 365 days / Relative
absence 0`.

The source HBJSON is correct. The defects are all in `PHX/from_HBJSON/`.

```
ZONE Office  res_occ=0.0
  -FLOOR_01_default_space  fa=266.2  ppl/m2=0.0  peak_occ=0.0 | OfficeSmall BLDG_OCC_SCH  0 24 365.0 0.0
  ... (all five spaces identical)

HB source:  people_per_area = 0.05651055401870768   ← present and correct
            occupancy schedule ph.daily_operating_periods = 0 entries
```

Investigating it surfaced four defects in total — three in scope for the reported symptom,
plus one pre-existing, unrelated bug in the same function.

| # | Defect | Location | Real-project exposure |
|---|---|---|---|
| 0 | ACH ventilation flow understated 3600x | `create_rooms.py:63` | **None** — 0 of 37 projects |
| 1 | Space occupancy load never populated | `create_rooms.py:140-143` | Every model without explicit PH occupancy |
| 2 | No HB→PH fallback for occupancy/lighting schedules | `create_schedules.py:179-258` | **Every** project |
| 3 | Lighting full-load hours ignore the utilization factor | `model/schedules/lighting.py:117-119` | **Every** project |

---

# Background — the occupancy channels

PHX carries occupancy through two independent paths.

### Channel A — explicit PH occupancy, zone-level (working, must not change)

```
GH "HBPH - Set Occupancy"                 honeybee_grasshopper_ph/.../set_res_occupancy.py
  └─ People.properties.ph.number_people        explicit user input: PH *average* occupancy
     People.properties.ph.number_bedrooms
     PhDwellings.num_dwellings                 via "HBPH - Set Dwelling"
        ├─ cleanup.merge_occupancies()          cleanup.py:236-237, 259-261
        └─ create_building.set_zone_occupancy() create_building.py:305-319
              PhxZone.res_occupant_quantity / res_number_bedrooms
                 ├─ WUFI  <OccupantQuantityUserDef>   xml_schemas.py:257
                 └─ METr  loadsZ.nOcc                 metr_schemas.py:839
```

### Channel B — derived occupancy, per-space (Defect 1)

```
HB People.people_per_area   →  ✗ MISSING LINK ✗  →  PhxSpace.occupancy.load.people_per_m2
                                                    PhxSpace.peak_occupancy
   ├─ WUFI  <LoadPerson><NumberOccupants>   xml_schemas.py:1855
   └─ METr  loadsZ.lPersZ[].nOcc            metr_schemas.py:1205
```

### Channel C — the shared utilization schedule (Defects 2 and 3)

```
HB ScheduleRuleset.properties.ph.daily_operating_periods
   │  (empty for stock HB programs AND for the honeybee-ph residential standards)
   ├─ operating_days_year                → annual_utilization_days
   ├─ annual_average_operating_fraction  → relative_utilization_factor   ← 0.0 when empty
   └─ first_operating_period             → start_hour / end_hour         ← None → 0 / 24
```

### The core invariant

> **A and B are mutually exclusive.** For any dwelling, occupancy is expressed *either* as an
> explicit PH average at the zone level *or* as a derived density at the space level — never
> both. Emitting both double-counts the same occupants.

---

# Defect 0 — ACH ventilation understated by 3600x

**Independent of the reported symptom. Pre-existing. Ships as its own commit.**

```python
(flow_per_person, flow_per_area, air_changes_per_hour, flow_per_zone) = hb_room_vent_flowrates(host)
...
m3s_by_ach = (air_changes_per_hour * space_percent_of_total) / 3_600   # create_rooms.py:63
```

`hb_room_vent_flowrates()` returns its third element **already in m³/s** —
`vent_program.air_changes_per_hour * _hb_room.volume / 3600` — and its docstring says
`"[2] (m3s)"`. PHX unpacks it into a local named `air_changes_per_hour` and divides by 3600
again.

Measured, 100 m² / 300 m³ room at 0.5 ACH:

```
correct                 0.04166667 m3/s  = 150.000 m3/hr
create_rooms.py gives   0.00001157 m3/s  =   0.042 m3/hr      understated 3600x
```

### Real-project exposure: none

The bug manifests only when a room uses ACH-based ventilation **and** its Spaces carry no
`_v_sup` override — because `create_rooms.py:126-133` discards the computed flow whenever
`_v_sup`/`_v_eta` is set. Survey of all 56 project folders (37 readable):

```
2531_Old_Ghost_Road     3/3 ACH-vent rooms   21/21 spaces w/ _v_sup   → not exposed
2613 Ayers Home         6/6 ACH-vent rooms   22/22 spaces w/ _v_sup   → not exposed
all others              0   ACH-vent rooms                            → not exposed

PROJECTS EXPOSED: 0
```

Only `tests/reference_files/.../Multi_Room_Complete.hbjson` is exposed (0.4 ACH, no
`_v_sup`), so this is a fixture-only golden change. No re-export or re-certification concern.

*(8 project HBJSONs fail to load with `KeyError: 'divisions'` in `honeybee_energy_ph` material
deserialization — old files against the current package. Unrelated; noted only.)*

---

# Defect 1 — Space occupancy load never populated

`create_rooms.py:140-143` wires the **schedule** but not the **load**:

```python
if hbe_occ:
    occ_sched_id = hbe_occ.occupancy_schedule.identifier
    new_room.occupancy.schedule = _occ_sched_collection[occ_sched_id]
```

`people_per_m2` keeps its `0.0` default, so `peak_occupancy` is always `0`. Contrast the
lighting branch immediately below (`:146-149`), which *does* set `load.installed_w_per_m2` —
this is an omission, not a design decision. Every golden reference file records
`NumberOccupants=0.0`; invisible on residential work because that uses Channel A.

## The gating rule (decided)

> **Explicit PH occupancy wins, evaluated per dwelling group.**
>
> If **any** room in a Space's dwelling group carries an explicit `number_people`, every Space
> in that group exports `NumberOccupants = 0`. Otherwise, derive from the Honeybee-Energy
> `People` load. An untagged room is its own group of one.

### Why per-**group**, not per-**room**

`set_res_occupancy.set_people_per_m2()` normalizes a dwelling's occupants across the **whole
group**:

```python
total_peak_ppl  = total_average_ph_ppl / _get_avg_occ_rate(hb_room)   # group total
people_per_area = total_peak_ppl / total_floor_area_m2                # group total area
```

Every room in the group receives the **same** density regardless of its own `number_people`.
A per-room gate therefore reads a per-group quantity and inverts the intent — it skips the
room holding the explicit number and falls through on the rooms holding `0`.

This is the standard single-family workflow: tag the house as one dwelling, enter occupants on
the bedrooms, leave living spaces at `0`.

### Why `None` is not needed

`number_people` cannot be `None` today (`people.py:93` default `0.0`; `:158` `from_dict` reads
a float), so "never set" and "explicitly 0" are indistinguishable in the data. It doesn't
matter: an explicit `0` is recorded by `people_per_area` instead — running *Set Occupancy* on
a group totalling zero people also sets that room's `people_per_area` to `0.0`.

Making it nullable was considered and rejected — it needs None-guards at `phius_mf.py:119` and
`set_res_program.py:121`, a `from_dict` default, and a GH change, **and every existing HBJSON
already serializes `0.0`**, so the distinction would only exist for models re-exported
afterwards.

### The group key must be `num_dwellings >= 1`, not `get_dwelling_obj()`

`honeybee_energy_ph.dwellings.get_dwelling_obj()` **does not survive an HBJSON round-trip**.
`PhDwellings.default()` mints a fresh `uuid4` per process; the Grasshopper session's default
identifier is serialized into the file, and on re-import `_is_default_dwelling` compares it
against *this* process's default and misses:

```
this process PhDwellings.default().identifier = e7400953-d220-4651-88dd-bb55195c290e
Room_1: identifier=b745ad47-c131-45a7-8eb5-ade01e727928  num_dwellings=0
    _is_default_dwelling() -> False    get_dwelling_obj() -> True     ← wrong
```

Every untagged room then shares one identifier and pools into a single group — so one untagged
room with explicit occupancy would suppress every other untagged room in the model.

Use `num_dwellings >= 1`: serialization-stable, and already the codebase's definition of "not a
dwelling" (`PeoplePhProperties.is_residential`). Verified across the six test models —
untagged files report `num_dwellings=0`, tagged files report `1`.

*(This is a genuine honeybee-ph bug affecting any GH workflow that opens a saved HBJSON before
running Set Dwelling / Set Occupancy. Separate issue; see "Adjacent bugs".)*

## Distributing occupants across Spaces — Option B

`people_per_area` is defined per m² of **HB Room** floor, but `peak_occupancy` multiplies it by
**Space** floor area. Spaces need not tile the room:

| model | room fa | Σ space fa | ratio |
|---|---|---|---|
| 39 15th St | 1456.61 | 1456.61 | 1.000 |
| `Multi_Room_Complete` | 48.40 | 21.78 | **0.450** |

- **Option A** — density × space area. A 24.2 m² room at 0.1 ppl/m² (2.42 occupants) with one
  10.89 m² Space yields 1.09. **1.33 occupants deleted.**
- **Option B** — distribute the room total by Space floor-area fraction. Yields 2.42.

**Option B, because it strictly dominates.** When Spaces tile the room the two are
algebraically identical:

```
B = (ppl/m² × room.fa) × (space.fa / Σ space.fa)
  = ppl/m² × space.fa  =  A          when Σ space.fa == room.fa
```

They diverge only where A is provably losing occupants, and WUFI computes internal gains from
`NumberOccupants` — an under-count is an under-count of people gains, which matters most for
cooling on exactly the non-residential projects this fix targets.

`host_room_prop_ph.total_space_floor_area` is already imported and used four lines away, so
Option B costs no new plumbing.

## Resolving the pre-existing ventilation TODO

`create_rooms.py:50-64` carries `# TODO: Unweighted or weighted? Which is right?` and already
mixes both options **in one function** — flow-by-person and flow-by-area use Option A;
flow-by-ACH and flow-by-zone use Option B. Defect 1 forces a choice, so resolve it uniformly:

```python
frac = _space.floor_area / host_room_prop_ph.total_space_floor_area

room_peak_occupancy = hb_room_ppl_per_area(host) * host.floor_area

m3s_by_occupancy = flow_per_person * room_peak_occupancy   * frac
m3s_by_area      = flow_per_area   * host.floor_area       * frac
m3s_by_ach       = flow_by_ach_m3s                         * frac   # already m3/s — do NOT divide
m3s_by_zone      = flow_per_zone                           * frac

return (m3s_by_occupancy + m3s_by_area + m3s_by_zone + m3s_by_ach) * 3_600
```

Three results at once: Defect 0 is fixed, the TODO is answered uniformly, and
**Σ over Spaces == the room total exactly** — a clean invariant, testable against the existing
`hb_room_peak_ventilation_airflow_total()` helper.

---

# Defects 2 and 3 — the Phius protocol, half-implemented

These are **one protocol**, not two independent judgment calls. The authority is a
September-October 2021 email thread between Ed May and Al Mitchell (Phius), subject
*"PHIUS Non-Res Loads, Schedules ?"*, filed in
[`phius-correspondance-background/`](phius-correspondance-background/).

> **The filenames do not sort chronologically.** Read order is **01 → 03 → 02**:
>
> | file | date | content |
> |---|---|---|
> | `PHIUS NonRes Loads Schedules - 01.pdf` | Sep 24, 2021 | Ed's opening proposal — separate OCC/LGHT/EQUIP patterns, and the `0/24/365` + annual-average-factor conversion |
> | `PHIUS NonRes Loads Schedules - 03.pdf` | Sep 28, 2021 | Al's reply — simplify to one pattern + EFLH; the `Utilization hours per year` field circled in red |
> | `PHIUS NonRes Loads Schedules - 02.pdf` | Oct 7, 2021 | Al's confirmation — *"the EFLH overrides the lighting"*; contains the full thread |
>
> This is the only record of why the lighting pattern references the occupancy pattern rather
> than having its own. Phase 4's entire justification rests on the Oct 7 line.

| date | who | substance |
|---|---|---|
| Sep 24 | Ed → Al | *"set the start / end to 0 and 24 respectively, and 365 days, then calc the annual util factor based on the OpenStudio hourly values, and input that as the use-factor"* |
| Sep 28 | Al → Ed | *"one pattern for the space covering occupancy, and then use the **utilization full hours, EFLH in LEED speak**, to cover the electrical and lighting loads"* |
| Sep 29 | Ed → Al | *"makes the occupancy schedule (Utilization Pattern) and then use that EFLH input for the lighting and equipment"* |
| Oct 7 | Al → Ed | *"the **EFLH overrides the lighting**, which is to our advantage for simplicity"* |

That thread is what `xml_schemas.py:1863-1864` records. `RoomCategory` pointing at the
occupancy pattern is correct and stays.

## Defect 2 — no HB→PH fallback converter

`build_ventilation_schedule_from_hb_room()` (`create_schedules.py:139-176`) branches on
`_room_has_ph_style_ventilation()` and falls back to
`calc_four_part_vent_sched_values_from_hb_room()`. The occupancy (`:179-217`) and lighting
(`:220-258`) builders have **no equivalent**, so when `daily_operating_periods` is empty:

| property | value | why |
|---|---|---|
| `first_operating_period` | `None` | → start/end forced to `0`/`24` |
| `annual_average_operating_fraction` | `0.0` | empty loop ÷ 8760 (`ruleset.py:214-227`) |
| `operating_days_year` | `365.0` | `52.1429 × 7` default |

**Not non-residential-only.** The honeybee-ph residential standards ship with no PH properties
(`hbph_sfh_occupancy.json` → `hbph_sfh_Occupant_Presence -> {}`), so `Multi_Room_Complete`
exports `RelativeAbsenteeism=0.0` / `LightingFullLoadHours=8760` too.

Recoverable values:

| model | schedule | annual mean | implied EFLH |
|---|---|---|---|
| 39 15th St | `OfficeSmall BLDG_OCC_SCH` | 0.2867 | — |
| 39 15th St | `OfficeSmall BLDG_LIGHT_SCH_2013` | 0.3436 | 3,010 |
| `Default_Model_Single_Zone` | `Generic Office Lighting` | 0.2917 | 2,555 |
| `Multi_Room_Complete` | `hbph_sfh_Occupant_Presence` | 0.7208 | — |
| `Multi_Room_Complete` | `hbph_sfh_Lighting` | 0.0417 | 365 |

### `RelativeAbsenteeism` is a UTILIZATION factor — confirmed

WUFI's column is labelled *"Relative absence"*, and the 2021 email says *"use-factor (or
absence factor)"* as if interchangeable. Getting the polarity backwards would invert every
non-res result. The Phius standards library PHX already ships settles it:

| Phius program | window | days | `relative_utilization_factor` |
|---|---|---|---|
| Office Workspace Open | 7-18 | 250 | 1.0 |
| Office Workspace Semiopen/Closed | 7-18 | 250 | 0.7 |
| Office Meeting Room | 7-18 | 250 | 0.5 |
| Restroom Public | 7-18 | 250 | 0.1 |
| Indoor Corridor | 0-24 | 365 | 1.0 |

As *absence*, an open office is 100% absent and a public restroom 90% occupied — absurd. As
*utilization*, every row reads correctly. **PHX's existing mapping is right; no change.**

Cross-check: `from_WUFI/wufi_xml/_ridgeway.xml` (WUFI-authored, 206 spaces) carries
`7.5-16.5 / 1.0` and `11.2-12.8 / 1.0` — literally `Common Office` and `Central Restroom` from
this library.

### Both schedule shapes must coexist and agree

The Phius library uses **real** windows (7-18, 250 days), not the `0/24/365` fallback shape.
They are equivalent in `annual_utilization_factor`:

```
PH-style  Office Workspace Open: (11 × 250 / 8760) × 1.0  = 0.313927
HB-style  equivalent (0/24/365, factor 0.3139)            = 0.313927
```

That equivalence is exactly what Ed proposed and Al accepted, and it is a better test than
asserting magic numbers — it tests the property the protocol cares about.

## Defect 3 — full-load hours ignore the utilization factor

```python
return max(0, min(8760, self.annual_operating_hours))   # lighting.py:117-119
```

`annual_operating_hours` is the *window*, not the *load*. With the degenerate `0/24/365`
schedule every space reports `8760` — lights at full rated power every hour of the year.

`LightingFullLoadHours` is **EFLH**: Σ(hourly load fraction) = `8760 × mean`. And per Al, EFLH
*overrides* the lighting pattern, so the wrong number is the governing one.

Defects 2 and 3 together produce exactly EFLH:

```
Defect 2:  start=0, end=24, days=365, factor = mean(schedule.values())
Defect 3:  FLH = annual_operating_hours × factor = 8760 × mean = EFLH
```

**Ordering constraint:** Defect 3 before Defect 2 collapses FLH from 8760 to 0, since the
factor is `0.0` today.

*(WUFI's own files write `LightingFullLoadHours = 0` — that is what you get when nobody sets
it, consistent with the Phius approach deliberately diverging.)*

---

# Test corpus

Six purpose-built Grasshopper models in [`HBJSON/`](HBJSON/), with their GH definitions in
[`grasshopper-model/`](grasshopper-model/). Real component output, no cross-repo import.

| file | shape | dwellings | zone (A) | per-room gate | **per-group gate** |
|---|---|---|---|---|---|
| `01_no_dwelling_no_occupancy` | untagged, no occupancy | 0 | 0.0 | 22.60 | **22.60** ✓ |
| `02_single_dwelling_no_occupancy` | 1 dwelling, no occupancy | 1 | 0.0 | 22.60 | **22.60** ✓ |
| `03_single_dwelling_set_occupancy` | 1 dwelling, occupancy on subset | 1 | 7.0 | 2.43 ✗ | **0.00** ✓ |
| `04_no_dwelling_set_occupancy` | untagged, occupancy set | 0 | 7.0 | 0.00 | **0.00** ✓ |
| `05_multiple_dwelling_set_occupancy` | **2 dwellings** | 2 | 7.0 | 0.69 ✗ | **0.00** ✓ |
| `06_res_with_hallway` | 2 dwellings + untagged non-res | 2+1 | 7.0 | 0.69 ✗ | **0.00** ✓ |

Three of six leak under a per-room gate.

**`03` is the anchor for the group-uniform density invariant**, confirmed to 8 decimals:

```
Room_9  n_ppl=0   ppl/m2=0.02428      group total 7 people, 400 m², sched mean 0.720833
Room_10 n_ppl=1   ppl/m2=0.02428      predicted 7 / 0.720833 / 400 = 0.02427746
Room_11 n_ppl=2   ppl/m2=0.02428      actual                        = 0.02427746
Room_12 n_ppl=4   ppl/m2=0.02428      MATCH
```

**`04` is the contrast case**: untagged rooms normalize *per room*
(`0`, `0.01387`, `0.02775`, `0.05549`), tagged rooms normalize *per group* (uniform `0.02428`).

**`05` proves group separation** — two dwellings on identical geometry get different densities
(`1/0.7208/200 = 0.00694` and `6/0.7208/200 = 0.04162`).

## Known coverage gap

No file discriminates `get_dwelling_obj` from `num_dwellings >= 1`, because every untagged
zero-people room here also has `people_per_area = 0.0` (Set Occupancy zeroes it, and
`Phius_Hallway` is 0.0 by design). Triggering it needs an untagged room with nonzero *program*
occupancy that never went through Set Occupancy, beside an untagged room that did — a narrow
shape, awkward in Grasshopper, cheap as a synthetic unit test.

---

# Requirements

| # | Requirement | Verification |
|---|---|---|
| R0 | ACH-based ventilation flow is not divided by 3600 twice | 0.5 ACH / 300 m³ → 150 m³/hr |
| R0b | Σ Space ventilation flow == the HB-Room total | vs `hb_room_peak_ventilation_airflow_total()` |
| R1 | Non-res Spaces export `people_per_area × space.floor_area` | 39 15th St → 15.04 / 13.91 / 29.25 / 22.23 / 1.88 (82.3) |
| R2 | A Space whose dwelling group states explicit occupancy exports `0.0` | cases 03-06 |
| R3 | A Space whose group states none derives from the HB load | cases 01, 02 |
| R4 | The gate evaluates the **dwelling-group total**, not the room | cases 03, 05, 06 — where the answers differ |
| R5 | The gate reads **pre-merge** state | guard test on a merged non-res model |
| R6 | Untagged rooms are each their own group | synthetic test (see coverage gap) |
| R7 | Occupants are distributed so Σ Spaces preserves the room total | non-tiling fixture |
| R8 | `res_occupant_quantity` / `res_number_bedrooms` unchanged for every model | golden diff |
| R9 | A schedule with no PH periods yields a pattern derived from raw HB values | `relAbs` == annual mean |
| R10 | A schedule **with** PH periods keeps today's behavior exactly | byte-identical output |
| R11 | PH-style → HB-style conversion preserves `annual_utilization_factor` | 0.313927 both ways |
| R12 | `full_load_lighting_hours` == EFLH, clamped 0-8760 | boundary tests |
| R13 | PHPP and PPP exports bit-identical | `test_xl_replay` unchanged; `test_to_PPP` green |
| R14 | WUFI-XML round-trip stable | `_ridgeway` / `_la_mora` |
| R15 | Channels A and B never both nonzero for one dwelling | invariant test over all fixtures |

---

# Adjacent bugs (found here, fixed elsewhere)

1. **`get_dwelling_obj()` breaks across HBJSON round-trip** (`honeybee_ph`) — see above. Worked
   around here by keying on `num_dwellings >= 1`; deserves an upstream fix.
2. **`_num_people` list padding** (`honeybee_grasshopper_ph`, `set_res_occupancy.py:231-236`) —
   pads a short list by repeating the **last** value rather than zero-filling, so `[2, 1, 1]`
   against 6 rooms gives 7 occupants, not 4. Also adds `max_input_length - 1` items rather than
   `max_input_length - len(...)`.
3. **`Infiltration from ACH` 50Pa output unit mismatch** (`honeybee_grasshopper_ph_plus`) —
   returns a total m³/s on a socket declared per-exterior-area. Written up at
   `honeybee_grasshopper_ph_plus/planning/bug-fixes/infiltration-from-ach-units.md`.
4. **`FloorAreaUtilizationZone` inconsistency** — WUFI writes `_sp.floor_area`
   (`xml_schemas.py:1856`), METr writes `_sp.weighted_floor_area` (`metr_schemas.py:1206`).
   Same concept, two values. Matters because WUFI derives *"Average occupancy [m²/Person]"*
   from `NumberOccupants ÷ FloorAreaUtilizationZone`. Invisible on current fixtures (the two
   areas are equal); would surface on a Space with a TFA weighting below 100%.

### A shared root cause worth noting

Defect 0 and adjacent bug 3 are the same failure: **a function returning bare floats whose
units live only in a docstring, unpacked into a local whose name contradicts them.** A flow
becomes `air_changes_per_hour` and is divided by 3600 again; a total becomes
`infiltration_rate_at_50Pa` and reaches a socket named `per_exterior`. `NamedTuple` returns
with unit-bearing field names (`flow_by_ach_m3s`, `q50_total_m3s`) would make this class of bug
unwritable. Suggested, not scheduled.

---

# Resolved question — do Defects 2 and 3 apply to residential models?

**Answer: they are inert on residential. Apply the fix uniformly; there is no risk to
certified residential WUFI results.**

Tested 2026-08-06 in WUFI Plus Free 3.6.0.1 against case 03 (WUFI reports the case as
*"Passive house: Residential"*). Four variants, isolating each field. Screenshots in
[`WUFI/`](WUFI/).

| variant | `relAbs` | EFLH | Heating | Cooling | Heat load | Cool load | Source | Site |
|---|---|---|---|---|---|---|---|---|
| `A_as_exported` | 0.0 | 8760 | 153.66 | 12.22 | 76.54 | 5 | 604 | 5.28 |
| `B1_lighting_only` | 0.0 | **2555** | 153.66 | 12.22 | 76.54 | 5 | 604 | 5.28 |
| `B2_absenteeism_only` | **0.7208** | 8760 | 153.66 | 12.22 | 76.54 | 5 | 604 | 5.28 |
| `B_corrected` | **0.7208** | **2555** | 153.66 | 12.22 | 76.54 | 5 | 604 | 5.28 |

Identical to the last digit.

### Two independent confirmations, not just matching numbers

1. **Site energy is 5.28 kWh/m²a.** Were the lighting load in the balance, variant A alone
   would carry `10.55 W/m² × 400 m² × 8760 h = 36,967 kWh ÷ 400 m² = 92.4 kWh/m²a`. It is not
   being counted at all.
2. **WUFI strips the blocks on save.** All four files were written back at `DataVersion 49` /
   130 KB with `LightingFullLoadHours` and `NumberOccupants` removed entirely — and `A` and
   `B1` came back **byte-identical**. WUFI reads a residential model, discards the non-res
   person and lighting load blocks, and re-emits them empty.

### Why B2's null result was expected, and B1's was not

`RelativeAbsenteeism` scales the **person** load, and `NumberOccupants` is `0.0` because
Channel A carries the occupancy — zero scaled by anything is zero. That was predicted
structurally. **B1 is the new information:** EFLH is also ignored, despite acting directly
rather than through the person load.

### Consequences

- **Phases 3 and 4 are unblocked and apply to all models uniformly.** No gating by building
  category, no re-certification concern.
- Golden XML/JSON fields will change; WUFI *results* for residential will not.
- This establishes **safety**, not **efficacy**. That these fields matter on non-residential
  models rests on the 2021 Phius protocol and on `_ridgeway.xml` carrying real varied values —
  not on this test.

### Limits of the test

1. **One synthetic model** — four windowless boxes, ideal air system, WUFI Plus *Free*. Note
   that having no windows means internal gains are a *larger* share of the balance than in a
   real building, so if the effect were going to surface anywhere it would surface here.
2. **WUFI only.** The matching METr pair (`METr/AB_case03_*.json`) was **not run** — METr
   currently errors on this model owing to a pre-existing, unrelated foundations issue. Worth
   re-running once that is fixed, since METr is the target that surfaced the original symptom
   and may consume these fields differently.
3. **Says nothing about non-residential**, which is where these fields are supposed to matter.
