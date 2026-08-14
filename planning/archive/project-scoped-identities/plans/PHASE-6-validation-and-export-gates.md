# Phase 6 — Identity validation and exporter gates

## Goal

Validate the actual project graph—not only allocator bookkeeping—before an
exporter consumes numeric identities.

## Red tests

Mutate otherwise valid projects to create:

- duplicate IDs in component, material, assembly, window, pattern, zone,
  ventilator, duct, and piping namespaces;
- dangling component assembly/window/shade refs;
- dangling component polygon and polygon vertex/child refs;
- dangling Space schedule/ventilator refs;
- dangling duct ventilator and zone-coverage refs;
- legal same-number reuse across independent namespaces.

Require a typed aggregate error with object path, namespace, value, and problem
kind. Assert validation occurs before serialization or Excel writes begin.

## Green implementation

- Add a read-only project identity validator with per-target profiles.
- Derive namespace membership from actual graph traversal.
- Validate both uniqueness and referential integrity.
- Call the relevant profile at WUFI and METr exporter entry points.
- Call the PHPP profile before identity-dependent polygon/ventilator writes.
- Do not add an identity gate to PPP unless a concrete PPP ID consumer is found.
- Keep format sentinels (`-1`, currently accepted ventilation `0`) distinct from
  allocated identities; coordinate with the separate ventilation-assignment
  feature rather than changing sentinel semantics here.

## Guardrails

- validator is read-only and never repairs/renumbers;
- error ordering is deterministic;
- no whole-model serialization is introduced;
- target profiles validate only what that exporter consumes.

## Verification

- validation unit suite
- WUFI/METr reference tests
- PHPP focused identity tests and xl-replay
- WUFI import round trips
- PPP negative regression
- parallel conversion suite

## Definition of done

Every affected exporter fails early and diagnostically on duplicate/dangling
identity, accepts legal namespace reuse, and leaves valid protected outputs
unchanged.

## Commit

`feat(identity): validate project references before export`
