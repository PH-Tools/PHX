# WUFI import: reconciling the three per-Space lists

**Status:** Item 1 **Implemented** · Item 2 **Implemented** (Option 1; Option 2 is the open follow-up)
**Scope decision:** `from_WUFI_XML` is a general-purpose importer for any WUFI file — taken 2026-08-15
**Opened:** 2026-08-15
**Owners:** `PHX/from_WUFI_XML/phx_schemas.py` (`_PhxZone`, `_add_occupancy_data_to_space`, `_add_lighting_data_to_space`)
**Related:** [`../floor-area-utilization-zone.md`](../floor-area-utilization-zone.md) · [`../../archive/project-scoped-identities/`](../../archive/project-scoped-identities/README.md)

## Context — the format carries three independent Space-shaped lists

A WUFI `Zone` (and its METr equivalent) holds three sibling lists that PHX collapses into a
single `PhxSpace`:

| WUFI XML | METr JSON | PHPP origin | Carries |
|---|---|---|---|
| `RoomsVentilation` → `Room` | `lRoom` | `Additional Vent` worksheet | design airflows, `AreaRoom`, ventilation pattern + unit refs |
| `LoadsPersonsPH` → `LoadPerson` | `loadsZ.lPersZ` | `Use non-res` worksheet | `NumberOccupants`, `FloorAreaUtilizationZone`, occupancy pattern ref |
| `LoadsLightingsPH` → `LoadsLighting` | `loadsZ.lLight` | `Use non-res` worksheet | `InstalledLightingPower`, full-load hours |

**Verified in both formats: none of the three entry types carries an `IdentNr`.** Each entry has
only a free-text `Name` and its list index. There is no cross-list foreign key — `Room` and
`LoadPerson` do not reference each other, and their pattern refs point at different namespaces
(ventilation patterns vs. occupancy patterns). The successor format keeps this shape:

```jsonc
// METr Multi_Room_Complete.json — lZone[0]
"lRoom":            [{ "n": "101-Room_3", "idUPatV": 1, "idVUnit": 1, "area": 10.89, ... }]
"loadsZ.lPersZ":    [{ "n": "101-Room_3", "idUPat": 1, "nOcc": 0.0, "flAUZone": 10.89 }]
"loadsZ.lLight":    [{ "n": "101-Room_3", "idUPat": 1, "instLP": 13.91, "lFLoadH": 365.0 }]
```

So `Name` is the **only** join key the format offers. That is what `_PhxZone` uses
(`phx_schemas.py:1366-1402`), and the tables are only reliably 1:1 because *PHX itself wrote
them that way* — one `PhxSpace` fans out to one entry in each list, same name, same order.

Files authored in WUFI-Passive carry no such guarantee. In PHPP, `Additional Vent` and
`Use non-res` are separate tables with independent row counts: a utilization zone can span
several ventilation rooms and vice versa. `School.xml` is exactly that case:

| List | Entries |
|---|---|
| `RoomsVentilation` | `a`, `b` |
| `LoadsPersonsPH` | `Office` (2 occ.), `Workshop` (17 occ.) |
| `LoadsLightingsPH` | *(absent)* |

Nothing pairs. `_PhxZone` produces the union — 4 Spaces — two with airflow and no occupancy,
two with occupancy and no airflow.

---

## Item 1 — orphan Occupancy Pattern → dangling export reference · **Implemented**

### Defect

`_add_occupancy_data_to_space` returned early for any Space with no matching `LoadPerson`
record, leaving the Space holding the throwaway `PhxScheduleOccupancy` that `PhxSpace`'s
default factory builds. That object takes an ID from the occupancy namespace but is **never
added to `project.utilization_patterns_occupancy`**.

Both writers emit a person-load node for *every* Space and reference that ID:

| Writer | Node | Source |
|---|---|---|
| WUFI | `LoadPerson.IdentNrUtilizationPattern` | `xml_schemas.py:1853` |
| WUFI | `LoadsLighting.RoomCategory` | `xml_schemas.py:1865` |
| METr | `lPersZ.idUPat`, `lLight.idUPat` | `metr_schemas.py:1180`, `:1203` |

So the export wrote references to patterns absent from `UtilizationPatternsPH`.

### Evidence — this predates the identity work

The bug is visible in the sandbox output committed at PR #77, well before project-scoped
identities existed:

```
tests/reference_files/from_WUFI/wufi_xml/_la_mora.xml  @ 4933ba6
  <UtilizationPatternsPH count="0"/>
  ...
  LoadPerson 'ERU1 (M701 schedule)' → IdentNrUtilizationPattern 7
  LoadPerson 'ERU2 (M701 schedule)' → IdentNrUtilizationPattern 8
  LoadPerson 'ERU1 (M701 schedule)' → IdentNrUtilizationPattern 9
  LoadPerson 'ERU2 (M701 schedule)' → IdentNrUtilizationPattern 10
```

Zero patterns declared, four dangling references. It surfaced now only because
`validate_project_export_readiness` began checking it (`identity_validation.py:262-267`):

```
PHX.model.identity_validation.IdentityValidationError: wufi identity validation failed with 2 issue(s):
- dangling-reference: variants[0].zones[0].spaces[2].occupancy.schedule.id_num -> 'project.patterns.occupancy' ID 3 (no matching object)
- dangling-reference: variants[0].zones[0].spaces[3].occupancy.schedule.id_num -> 'project.patterns.occupancy' ID 4 (no matching object)
```

### Fix

`phx_schemas.py:148, 1424-1451` — a single shared, project-registered `Unoccupied` pattern,
created lazily under key `__phx_unoccupied__` and reused by every Space with no person-load
record. Values are the zeros the orphan schedule already carried (start 0, end 1, 0 days,
factor 0), so no model value moves; the schedule simply becomes a real member of the
collection. Covers WUFI and METr in one place, since both writers read
`occupancy.schedule.id_num`.

```
School.xml round-trip, after:
  UtilizationPatternsPH:  1→'Office ', 2→'Workshop', 7→'Unoccupied'
  LoadsPersonsPH:         Office→1, Workshop→2, a→7, b→7
```

### Verification

- `tests/test_from_WUFI/test_patterns/test_new_xml_util_patterns_occupancy.py::test_spaces_without_person_loads_reference_a_real_occupancy_pattern` — asserts every Space's occupancy-schedule ID is a member of the project collection. Confirmed **fails** on the pre-fix code, passes after.
- `python -m pytest tests/` → 972 passed, 3 skipped.
- All three `_testing_WUFI_to_PHX.py` fixtures (`School`, `_la_mora`, `_ridgeway`) round-trip clean.

---

## Item 2 — the name-matching heuristic · **Filed**

`_PhxZone` walks `LoadsPersonsPH` in order, pairing each record against a `deque` of
ventilation Spaces bucketed by `Name`, then sweeps up unpaired ventilation Spaces in a second
loop that re-reads the person/lighting records out of a plain `dict` keyed by name
(`phx_schemas.py:1376-1402`). Five distinct failures follow.

All evidence below is from `School.xml`, minimally patched to give the entries real areas
(`FloorAreaUtilizationZone` = 50 m², `AreaRoom` = 30 m²) so the effects are visible rather than
masked by zeros. Source totals: **19 occupants** (2 + 17).

### 2a — non-matching names silently inflate the Space list

Unpatched `School.xml` yields 4 Spaces from 2 ventilation rooms and 2 utilization zones. Each
one is half-populated. The count matters: `PHX/PHPP/phpp_model/vent_space.py:88` writes one
`Additional Vent` row per `PhxSpace`, so a PHPP export of this model gets two rows of zero-flow
padding.

### 2b — duplicate names let one person-load be consumed twice

The second loop reads `occupancy_load_data.get(space.display_name)` — a plain dict with no
consumption tracking — so a `LoadPerson` already paired in loop 1 is applied again to every
leftover ventilation room of the same name.

Two rooms named `Office` (30 m² each), person-loads `Office` (2 occ.) and `Workshop` (17 occ.):

```
'Office'     peak_occ= 2.00  floor_area=30.0
'Workshop'   peak_occ=17.00  floor_area=50.0
'Office'     peak_occ= 2.00  floor_area=30.0     ← re-consumed
TOTAL OCCUPANTS = 21.0   (source = 19.0)
```

`_add_lighting_data_to_space` has the identical exposure via `lighting_load_data.get(...)`;
`installed_w_per_m2` is intensive, so the duplication inflates total installed lighting power
by the extra Space's floor area.

### 2c — the join key is a raw exact string

`ventilation_spaces_by_name` buckets on the unnormalized `Name`. One trailing space defeats it.
Same file, room renamed `'Office '`:

```
names match exactly            → 2 spaces
room named 'Office ' instead   → 3 spaces
     'Office'     occ= 2.00 area=50.0 vent=  0.0
     'Workshop'   occ=17.00 area=30.0 vent=849.5
     'Office '    occ= 0.00 area=30.0 vent= 68.0
```

These names are hand-typed in the WUFI/PHPP UI. `School.xml` already ships one such string:
its occupancy pattern is named `'Office '`, the person-load `'Office'`.

### 2d — a matched Space discards `FloorAreaUtilizationZone`

`_add_occupancy_data_to_space` sets only `peak_occupancy`; it never touches `floor_area`, so a
paired Space keeps the room's `AreaRoom` and drops the utilization zone's area. In the
exact-match run above, `Office` carries `area=30.0` (the room) although the source
`FloorAreaUtilizationZone` was 50.0. On re-export, `_LoadPerson` writes `floor_area` back out
(`xml_schemas.py:1856`), so the round-trip silently rewrites the utilization-zone area.
Occupant *count* survives only because `PhxSpace.peak_occupancy` divides and re-multiplies by
the same `floor_area` (`spaces.py:114-124`). This is the same field the open
[`floor-area-utilization-zone.md`](../floor-area-utilization-zone.md) item is about, reached
from the import side.

### 2e — a blank `AreaRoom` on a matched room zeroes the occupancy

`peak_occupancy`'s setter is `people_per_m2 = value / floor_area` with a `ZeroDivisionError`
guard that falls back to `0.0`. Pair a person-load against a ventilation room whose `AreaRoom`
is blank (as it is throughout `School.xml`) and the occupants vanish:

```
rooms named 'Office'/'Office', AreaRoom blank:
'Office'     peak_occ= 0.00  ← 2 occupants lost
'Workshop'   peak_occ=17.00
'Office'     peak_occ= 0.00
TOTAL OCCUPANTS = 17.0   (source = 19.0)
```

Unpatched `School.xml` is the extreme case — every `FloorAreaUtilizationZone` and `AreaRoom` is
blank, so **PHX imports 0 of its 19 occupants** with no diagnostic.

### Reproduction

```python
# from the repo root; writes patched copies to a scratch dir
import re, pathlib
src = pathlib.Path("tests/reference_files/from_grasshopper_tests/wufi_xml/School.xml").read_text()
src = src.replace('<FloorAreaUtilizationZone unit="m²" />', '<FloorAreaUtilizationZone unit="m²">50.0</FloorAreaUtilizationZone>')
src = src.replace('<AreaRoom unit="m²" />', '<AreaRoom unit="m²">30.0</AreaRoom>')
m = re.search(r"<RoomsVentilation.*?</RoomsVentilation>", src, re.S)
blk = m.group(0).replace("<Name>a</Name>", "<Name>Office</Name>").replace("<Name>b</Name>", "<Name>Office</Name>")
pathlib.Path("School_dup_area.xml").write_text(src[: m.start()] + blk + src[m.end() :])
# then convert and sum `space.peak_occupancy` across the zone
```

---

## Decision — taken 2026-08-15

**`from_WUFI_XML` is a general-purpose WUFI → PHX converter, intended to handle any WUFI file.**
Not a round-trip path for PHX-authored output. Confirmed by Ed, with the caveat that full
fidelity may not be reachable — some data does not survive the write.

Consequences:

- **Option 3 is rejected.** Refusing files whose lists do not align would close the door on the
  stated purpose.
- **Option 1 is implemented** (see below). It is a strict correctness win under this scope.
- **Option 2 becomes the structural follow-up.** `PhxSpace` conflates a ventilation room with a
  utilization zone; WUFI/METr/PHPP keep them separate because they genuinely are. Under an
  importer scope this is the only way to represent an arbitrary file without guessing. Not yet
  planned.

`_PhxZone`'s comment stated the old assumption outright — *"the ventilation-room list is an
ordered subset of it"* — true only of files PHX wrote. It now records the guess as a guess.

### Option 1 — make the current heuristic consumption-correct and honest · **Implemented**

Keep name matching (it is the only join key the format offers) but:

1. Consume person-load and lighting-load records **exactly once** — bucket them into `deque`s
   the way the ventilation side already is, so a leftover room cannot re-apply a used record. Fixes 2b.
2. Normalize the join key (`.strip()`; decide on case-folding). Fixes 2c.
3. When a paired room's `AreaRoom` is blank or zero, fall back to the person-load's
   `FloorAreaUtilizationZone` rather than letting the zero swallow the occupancy. Fixes 2e, and
   forces the 2d contract question to be answered explicitly.
4. Emit a diagnostic when the three lists do not reconcile 1:1, so a lossy import is visible
   rather than silent. Fixes 2a's silence, not its shape.

Bounded, no model change, no export-format change.

**As built** (`phx_schemas.py`):

| Change | Fixes |
|---|---|
| `_space_list_join_key()` — normalizes surrounding and repeated whitespace. Case deliberately **not** folded: a false pairing silently merges two genuinely different rooms, a missed pairing only leaves two half-populated Spaces, and the latter is now reported | 2c |
| `LoadsLightingsPH` bucketed into per-name `deque`s and popped, like the ventilation side. The leftover-room loop no longer re-reads person-loads at all — every record in `LoadsPersonsPH` is consumed by the first loop by construction | 2b |
| `_add_occupancy_data_to_space` fills a blank/zero `floor_area` from the person-load's own `FloorAreaUtilizationZone` before setting `peak_occupancy`. Only when the room area is absent — when both are present and disagree, the room still wins, which is the open contract question (2d), left untouched | 2e |
| `_report_space_list_reconciliation()` — one `logger.warning` per Zone naming the un-paired ventilation rooms, person-loads, and lighting-loads | 2a's silence |

Deliberately **not** done: orphan `LoadsLightingsPH` records (matching neither a person-load nor
a ventilation room) still do not produce a Space. They are now named in the warning rather than
dropped silently. Inventing an area-less, occupant-less Space for them is speculative; revisit
under Option 2.

### Option 2 — model the two tables separately *(the structural follow-up)*

`PhxSpace` conflates a ventilation room and a utilization zone. WUFI/METr/PHPP keep them
separate because they genuinely are. Splitting them (or letting a `PhxSpace` carry an explicit
many-to-many link to utilization-zone data) is the only way to represent an arbitrary WUFI file
without guessing. Large: touches the model, both writers, the PHPP `Additional Vent` writer,
and `from_HBJSON`. **Now the live follow-up**, given the importer scope.

### Option 3 — declare the scope and fail loudly outside it · *rejected*

Validating that the three lists are equal-length and name-aligned, and raising otherwise, was
the cheap option under a round-trip-only scope. Incompatible with the decision taken.

## Verification for Item 2

`tests/test_from_WUFI/test_project/test_space_list_reconciliation.py` — five tests, each
confirmed to **fail** on the pre-fix code:

| Test | Asserts |
|---|---|
| `test_duplicate_room_names_consume_each_person_load_only_once` | 2 rooms named `Office` → 3 Spaces, Σ occupants 19.0 (was 21.0) |
| `test_join_key_ignores_surrounding_whitespace` | room `'Office '` pairs with load `'Office'` → 2 Spaces (was 3) |
| `test_blank_room_area_falls_back_to_the_utilization_zone_area` | blank `AreaRoom` → area 50.0, Σ occupants 19.0 (was 17.0) |
| `test_matched_lists_do_not_warn` | an aligned file reconciles silently |
| `test_unreconciled_lists_are_reported` | un-patched `School.xml` → 4 Spaces **and** one warning naming `a`, `b`, `Office`, `Workshop` |

Full suite: **977 passed, 3 skipped**. PHX-authored fixtures (`Multi_Room_Complete`,
`Non_Residential_Office`) are unchanged — the aligned case does not move.

### Known remaining loss — not an Option 1 defect

Un-patched `School.xml` still imports **0 of its 19 occupants**. Every `AreaRoom` *and* every
`FloorAreaUtilizationZone` in that file is blank, so there is no area anywhere to fall back to.
`PhxSpace` stores occupancy as a density (`people_per_m2`, `spaces.py:114-124`), so it
structurally cannot hold "2 occupants in a zero-area zone" — the count is lost on assignment.
The import is now at least loud about the un-paired lists. Carrying an absolute occupant count
alongside the density is a model change; folded into open question 3 in [`STATUS.md`](STATUS.md).
