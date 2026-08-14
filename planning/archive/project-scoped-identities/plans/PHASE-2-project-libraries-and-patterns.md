# Phase 2 — Project libraries, patterns, variants, and certification

**Status:** Complete · 2026-08-14

## Goal

Migrate the first project-owned identity namespaces and remove direct class-state
reads from their builders/exporters.

## Entity families

- `PhxVariant`
- `PhxMaterial`
- `PhxConstructionOpaque`
- `PhxConstructionWindow`
- `PhxWindowShade`
- ventilation and occupancy schedules
- lighting schedule compatibility sequence
- `PhxPhBuildingData`

## Red tests

For each exported family, construct equivalent scoped graphs with deliberately
dirty legacy counters and assert identical instance IDs and reference projections.
Add the load-bearing test:

1. construct `bd_a`;
2. capture its WUFI XML;
3. construct `bd_b`;
4. re-export `bd_a`;
5. require identical XML and `IdentNr == bd_a.id_num`.

Add tests that the project `add_*` library methods preserve unique allocated IDs
without ad-hoc `max(...) + 1` renumbering inside an active scope.

## Green implementation

- Replace constructor increments with `allocate_identity(...)` for these families.
- Define explicit project namespace constants/keys.
- In HB builders, replace every second read of `Class._count` with the constructed
  object's `id_num`.
- Preserve HB property writebacks and assert they equal the PHX object.
- Change WUFI PH-building export from `bd._count` to `bd.id_num`.
- Retain legacy fallback outside a scope.

Do not migrate components/geometry/HVAC here.

## Compatibility gate

The first clean HBJSON conversion must remain byte-identical even though a subset
of families now uses the allocator. Any material/assembly/schedule number movement
means a historical allocation burn was missed.

## Verification

- focused construction/schedule/project/certification tests
- HBJSON assembly and schedule tests
- WUFI + METr reference cases
- WUFI certification exporter tests
- xl-replay

## Definition of done

All named families are isolated inside a project scope, direct constructors retain
legacy behavior, class-state export is gone, and protected outputs are unchanged.

## Commit

`feat(identity): scope project library and pattern identities`
