# Status — WUFI import: Space-list reconciliation

_Last updated: 2026-08-15_

**Scope decision (2026-08-15):** `from_WUFI_XML` is a **general-purpose WUFI → PHX converter**,
intended to handle any WUFI file — not a round-trip path for PHX-authored output. Full fidelity
may not be reachable; some data does not survive the write.

| Item | Status | Note |
|------|--------|------|
| 1 · Orphan Occupancy Pattern → dangling export reference | **Implemented** | Shared project-registered `Unoccupied` pattern |
| 2 · Name-matching heuristic (2a–2e) | **Implemented** | Option 1: consume-once, normalized join key, area fallback, reconciliation warning |
| 3 · Model the ventilation-room and utilization-zone tables separately | **Open** | Option 2 — the structural follow-up the scope decision makes live. Not yet planned |

977 tests pass, 3 skipped. Every new test confirmed to fail on the pre-fix code.

## Where it landed

| File | Change |
|------|--------|
| `PHX/from_WUFI_XML/phx_schemas.py:148` | module `logger`; `_UNOCCUPIED_PATTERN_IDENTIFIER` collection key |
| `PHX/from_WUFI_XML/phx_schemas.py` · `_space_list_join_key()` | whitespace-normalized join key (case deliberately not folded) |
| `PHX/from_WUFI_XML/phx_schemas.py` · `_report_space_list_reconciliation()` | one `logger.warning` per Zone naming every un-paired record |
| `PHX/from_WUFI_XML/phx_schemas.py` · `_get_unoccupied_pattern()` | shared registered `Unoccupied` occupancy pattern |
| `PHX/from_WUFI_XML/phx_schemas.py` · `_PhxZone` | lighting records bucketed into per-name `deque`s and popped; leftover-room loop no longer re-reads person-loads |
| `PHX/from_WUFI_XML/phx_schemas.py` · `_add_occupancy_data_to_space` | blank `AreaRoom` falls back to `FloorAreaUtilizationZone`; assigns the `Unoccupied` pattern when there is no person-load |
| `tests/test_from_WUFI/test_project/test_space_list_reconciliation.py` | new — five tests covering 2a–2e |
| `tests/test_from_WUFI/test_patterns/test_new_xml_util_patterns_occupancy.py` | new — every Space's occupancy-schedule ID is a member of the project collection |

Not yet committed. Also regenerated: `tests/reference_files/from_WUFI/wufi_xml/{School,_la_mora,_ridgeway}.xml`.
These **are** test inputs (`test_from_WUFI/test_project/test_occupancy_roundtrip.py` reads them),
and the committed copies are stale from PR #77 — they still carry the item-1 dangling references
and pre-identity-refactor geometry IDs. The suite passes either way; regenerating leaves the
fixtures internally consistent.

## Next step

Option 2 — plan the `PhxSpace` split. Under the importer scope, a `PhxSpace` that is
simultaneously a ventilation room and a utilization zone cannot represent a WUFI file where
those tables have unrelated lengths; the reconciliation is a guess no matter how careful. Scope:
the model, both writers, the PHPP `Additional Vent` writer, and `from_HBJSON`.

## Open questions

1. Does the `FloorAreaUtilizationZone` contract (item 2d — when a room area *and* a
   utilization-zone area are both present and disagree, the room currently wins) resolve the
   same way as the open exporter-side question in
   [`../floor-area-utilization-zone.md`](../floor-area-utilization-zone.md)? They are the import
   and export halves of one field.
2. Should the join key be case-folded as well as whitespace-normalized? Currently not, on the
   grounds that a false merge is worse than a missed one and missed pairings are now reported.
   Revisit if real files show case drift.
3. Is a `LoadsPersonsPH` record with a blank `FloorAreaUtilizationZone` meaningful in WUFI, or
   does WUFI itself treat it as zero occupancy? `School.xml` declares 19 occupants across two
   zones with every area field blank, and PHX imports 0 of them because `PhxSpace` stores
   occupancy as a density. Carrying an absolute occupant count alongside the density would fix
   it; that is a model change, most naturally taken with Option 2.
4. Should an orphan `LoadsLightingsPH` record (matching neither a person-load nor a ventilation
   room) produce a Space? Currently reported and dropped.
