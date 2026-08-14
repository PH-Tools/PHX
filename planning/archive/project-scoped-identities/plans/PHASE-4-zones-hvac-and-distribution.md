# Phase 4 — Zones, Spaces, HVAC, and distribution

**Status:** Complete · 2026-08-14

## Goal

Migrate all remaining HBJSON conversion identities and make sequential/parallel
public conversions independent of global counters.

## Entity families

- `PhxZone`, `PhxSpace`
- mechanical system and device families
- ventilator, exhaust, supportive, renewable, and electrical compatibility IDs
- duct, pipe element, branch, and trunk IDs
- collection compatibility counters
- Space/duct → ventilator and HVAC → zone references

## Red tests

- dirty globals do not affect scoped zone/system graphs;
- `PhxZoneCoverage.zone_num` resolves;
- every non-sentinel Space ventilator ID resolves to a ventilator, not merely any
  mechanical device;
- every assigned duct ventilator ID resolves in the owning collection;
- same typed mechanical ID reused in a legal independent namespace stays accepted;
- duplicate ventilator IDs in one reference scope are diagnosed;
- sequential no-reset and executor tests from Phase 0 become green.

## Green implementation

- Migrate each remaining constructor through the allocator helper.
- Own the HB scope in `create_project.convert_hb_model_to_PhxProject()` so the
  public `PHX.conversion.from_honeybee()` facade and legacy callers cannot diverge.
- Preserve current typed mechanical leaf namespaces unless a target reference
  proves a shared namespace is required.
- Make ventilator lookup typed; do not rely on insertion order of a generic
  `get_mech_device_by_id` result.
- Replace HB `_count` reads with allocated instance IDs.
- Preserve first-release HB source-property writebacks.
- Ensure all `__add__`/merge-created devices allocate in the owning scope.
- Attach the completed allocator to `PhxProject` and provide an explicit project
  mutation scope for post-conversion additions.

## Compatibility gate

Mechanical fixtures currently reuse values such as `1` across device types. Do
not globally renumber them. The goal is deterministic ownership and unambiguous
typed references, not a single project-wide integer sequence.

## Verification

- all model HVAC/Space/zone tests
- HBJSON HVAC/room/variant tests
- PHPP ventilator and duct tests
- WUFI/METr HVAC and distribution tests
- sequential and parallel identity suite
- WUFI + METr references, PPP, xl-replay

## Definition of done

No entity built through the public HBJSON conversion path depends on a global
counter. Sequential, parallel, and failed-then-valid tests are green with unchanged
protected output.

## Commit

`feat(identity): isolate zone and mechanical identities per project`
