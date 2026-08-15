# WUFI import: Space-list reconciliation

A WUFI/METr `Zone` carries three independent, name-keyed lists — ventilation rooms, person
loads, lighting loads — and `_PhxZone` collapses them into one `PhxSpace` per name. Two defects
live in that collapse.

**Read order:**

1. [`PRD.md`](PRD.md) — the format context, both defects, and the reproductions.
2. [`STATUS.md`](STATUS.md) — current state, next step, open questions.

## Scope

**Decided 2026-08-15:** `from_WUFI_XML` is a general-purpose importer meant to handle any WUFI
file, not a round-trip path for PHX-authored output.

| Item | Status |
|------|--------|
| **1** · Spaces with no person-load record hold an unregistered Occupancy Pattern, so the WUFI/METr writers emit a dangling `IdentNrUtilizationPattern` / `idUPat` | **Implemented** |
| **2** · The `Name`-matching heuristic that pairs the three lists: five failures — inflated Space counts, double-consumed load records, exact-string joins, discarded `FloorAreaUtilizationZone`, and occupancy silently zeroed by a blank `AreaRoom` | **Implemented** (Option 1) |
| **3** · Model the ventilation-room and utilization-zone tables separately | **Open** — the structural follow-up |

Item 1 was surfaced by `_testing_WUFI_to_PHX.py` after the new export-readiness validation
landed, but predates it — the broken output is visible in fixtures committed at PR #77.
Item 2 is the root cause both items share: `Name` is the only join key either file format
offers, and PHX's own writers are what make it reliable. Item 3 exists because no amount of
care makes that guess correct for a file PHX did not write.

## Owners

`PHX/from_WUFI_XML/phx_schemas.py` — `_PhxZone`, `_add_occupancy_data_to_space`,
`_add_lighting_data_to_space`.

## Related

- [`../floor-area-utilization-zone.md`](../floor-area-utilization-zone.md) — the export-side half of item 2d.
- [`../../archive/project-scoped-identities/`](../../archive/project-scoped-identities/README.md) — the validation that surfaced item 1.
