# Phase 6 — WUFI-authored occupancy round-trip stabilization

**Status:** Complete — 3 focused tests, 47 WUFI tests, and 853-test full gate green.
**Depends on:** Phases 0-4; completed before the Phase 5 archive closeout.

## Goal

Make the WUFI-authored `_ridgeway.xml` fixture import and round-trip its Space- and zone-level
occupancy fields without preprocessing or record loss. Preserve the already-passing `_la_mora.xml`
behavior.

## Confirmed failures

1. Raw `_ridgeway.xml` validation raises `TypeError: float() argument must be a string or a real
   number, not 'NoneType'` on an empty numeric XML value.
2. If empty values are diagnostically replaced with zero, the round-trip emits 148 of the source's
   206 `NumberOccupants` / `FloorAreaUtilizationZone` records.

## Guardrails

- Diagnose the exact empty field and the exact 58 dropped records before changing code.
- Do not normalize every empty XML tag globally unless the schema contract proves that is correct.
- Do not collapse distinct WUFI variants, zones, or Spaces to make counts match.
- Keep `OccupantQuantityUserDef` and `NumberBedrooms` byte-equivalent numerically.
- Keep the change within `from_WUFI_XML`, the corresponding WUFI exporter only if evidence requires
  it, focused tests, and this planning packet.

## Verification

- `_ridgeway.xml` imports without preprocessing.
- `_ridgeway.xml` source and regenerated output contain 206 matching values for
  `NumberOccupants` and `FloorAreaUtilizationZone`.
- `_ridgeway.xml` source and regenerated output retain matching `OccupantQuantityUserDef` and
  `NumberBedrooms` values.
- `_la_mora.xml` retains its existing matching 4 Space-load and 6 zone-level values.
- Existing WUFI importer tests and the full PHX suite pass.

## Commit

Use a separate conventional commit from Phase 5, scoped to the demonstrated importer/exporter
defect.
