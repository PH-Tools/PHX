# Phase 0 — Baselines and deterministic red tests

**Status:** Complete · 2026-08-14

## Goal

Protect current clean-process output and add reliable tests that reproduce global
identity leakage before any allocator code exists.

## Production changes

None.

## Tests

Create a cross-cutting identity test module (prefer
`tests/test_from_HBJSON/test_project_identity_isolation.py`) with helpers that:

1. load a fresh Honeybee model for every conversion;
2. collect a typed identity projection from the resulting `PhxProject`;
3. verify every projected integer reference resolves;
4. serialize WUFI and METr without invoking the reset fixture.

The projection must include variants, zones, components, vertices, polygons,
materials, assemblies, windows, shades, utilization patterns, mechanical systems,
mechanical devices, ducts, piping, PH-building data, and all stored refs listed in
`../AUDIT.md`.

Add red tests for:

- two sequential conversions through `PHX.conversion.from_honeybee()` without
  resets, plus one parity case through the legacy core converter;
- at least eight executor tasks using independently loaded copies of two fixtures;
- a conversion that raises after identities have been allocated, followed by a
  valid conversion;
- constructing a second `PhxPhBuildingData` must not change the first object's
  WUFI XML.

Before leaving red, prove each failure is identity-only and save the concise
failure/diff summary in `../STATUS.md`. Do not commit `xfail` or inverted assertions.

## Passing characterization gates

- The first clean conversion still equals the committed WUFI/METr reference.
- `tests/test_xl_replay/` is green and unchanged.
- `tests/test_to_PPP/` is green.
- Existing unit tests documenting direct constructor increments remain green.

## Definition of done

- Reproduction tests fail for the expected IDs, not UUIDs, timestamps, ordering,
  or floating-point fields.
- Clean-process baselines are protected before implementation begins.
- No production or golden file changed.

## Commit

Do not commit a permanently red branch. Carry the red tests into the phase that
makes each contract green, or commit only passing baseline/helper scaffolding as:

`test(identity): pin clean-process identity baselines`
