# Phase 5 — WUFI explicit identity claims

## Goal

Make WUFI → PHX conversion use the same project allocator while preserving every
source `IdentNr` and preventing later collisions.

## Red tests

Build compact WUFI schema fixtures with sparse/high explicit IDs for:

- variant and zone;
- vertex/polygon/component;
- material/assembly/window/shade;
- ventilation and occupancy patterns;
- PH-building data and mechanical system;
- ventilator plus Space/duct references.

Require WUFI → PHX → WUFI identity equality. Then add a new auto object within the
imported project's mutation scope and require it to skip all claimed values.

Add duplicate-claim cases in each reference-bearing namespace. Error assertions
must include namespace, conflicting value, and useful source/object context.

Add a legal-reuse case proving the same integer in material and variant namespaces
does not fail.

## Green implementation

- Enter a fresh identity scope in `convert_WUFI_XML_to_PHX_project`.
- Replace unchecked `id_num = IdentNr` assignments with allocator claim helpers.
- Preserve constructor compatibility burns if needed for clean round-trip output.
- Claim IDs before any later automatic object can collide.
- Cover every mechanical device type consistently; do not preserve only the
  ventilator source ID.
- Remove/disable library `max(...) + 1` repair inside an active allocator scope;
  conflicts must be explicit rather than silently rewriting imported identity.

## Guardrails

- do not change non-identity WUFI parsing;
- do not normalize sparse IDs;
- do not treat `-1`/format sentinels as allocated IDs;
- do not reject legal cross-namespace reuse.

## Verification

- new explicit-ID tests
- full `tests/test_from_WUFI/`
- WUFI occupancy round-trip tests
- WUFI and METr reference cases sourced from WUFI
- HBJSON identity suite remains green

## Definition of done

Explicit IDs are preserved and reserved, duplicates are deterministic errors, and
new post-import allocations cannot collide.

## Commit

`feat(from-wufi): preserve and reserve project identities`
