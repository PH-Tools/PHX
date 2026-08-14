# STATUS — project-scoped-identities

**Status:** Complete · 2026-08-14

- The counter/reference audit is complete in `AUDIT.md`: 27 explicit `_count`
  declarations, inherited counter families, 16 WUFI importer overwrites, HBJSON
  source-property writebacks, exporter consumers, and fixture/reset behavior.
- Current drift is reproduced: two fresh loads of
  `Default_Model_Single_Zone.hbjson`, converted sequentially in one process with
  no test reset, produce non-identical WUFI XML (324 unified-diff lines).
- Instance instability is separately reproduced: one existing
  `PhxPhiusCertification` changes WUFI PH-building `IdentNr` from `1` to `2`
  after an unrelated certification object is constructed.
- The current test harness resets counters; it does not currently reload model
  modules. The public model-reference documentation is stale on that point.
- The recommended implementation is a fresh `IdentityAllocator` per public
  conversion, exposed to nested constructors through a token-reset context and
  retained on `PhxProject` for explicit later mutation scopes. Direct standalone
  construction keeps the legacy fallback during this release.
- Phase 0 characterization is complete. The sequential public-conversion test
  fails only on numeric identities: assemblies `1..3 → 13..15`, components
  `5,6,9 → 14,15,18`, and vertices beginning `27 → 63`.
- Phase 1 is complete. `IdentityAllocator` provides isolated namespaces,
  explicit claims, deterministic duplicate diagnostics, exception-safe
  `ContextVar` scopes, nested reuse, and legacy direct-constructor fallback.
- Phase 2 is complete. Variants, libraries, patterns, and PH-building data use
  scoped namespaces; HB builders retain allocated instance IDs and the WUFI
  PH-building writer no longer reads class state.
- Phase 3 is complete. Components retain one shared compatibility namespace;
  polygons and vertices are isolated, including the historical 2D-to-3D vertex
  burn. Automatic claims use a compact high-water mark so transient geometry
  does not accumulate per-ID allocator entries.
- Phase 4 is complete. The core HB converter owns a fresh allocator, every
  remaining model counter family uses scoped allocation, and the project retains
  its allocator for explicit later mutation. Eight threaded conversions across
  two independently loaded fixtures match sequential WUFI/METr baselines.
- Phase 5 is complete. WUFI import now owns a fresh allocator, preserves and
  reserves explicit source identities, scopes variant-owned namespaces, skips
  sparse claims for later automatic allocations, and reports duplicate claims
  with both source paths. Project construction and allocator retention use one
  shared lifecycle helper for both public importers.
- Phase 6 is complete. A read-only, target-profiled validator aggregates
  deterministically ordered duplicate and dangling-reference issues before
  WUFI/METr serialization or the first PHPP Excel write. It reuses the existing
  ventilation-readiness contract, snapshots variant graph accessors once, and
  does not add a PPP dependency.
- Phase 7 is complete. Public reference fixtures no longer reset global
  counters; the remaining reset fixture is documented as standalone fallback
  coverage. Canonical architecture, exporter, model-reference, coding-standard,
  and model-index docs describe the scoped identity contract.
- Full verification: `933 passed, 3 skipped, 1 deselected`; reference-file diff
  is empty. Black and isort pass for all branch Python changes. Ruff reports only
  three pre-existing, unchanged simplification findings in `model/building.py`.
- **Next step:** merge/release through the normal repository workflow.
- Blockers: none. Do not begin broad `_count` deletion or golden regeneration;
  both are explicitly outside the compatibility-first implementation.
- Planning verification: 107 existing facade, WUFI/METr reference, WUFI import,
  PHPP ventilator/duct, and xl-replay tests pass (`107 passed in 3.46s`).

## Phase evidence

| Phase | Status | Red/green evidence |
|---|---|---|
| 0 — baselines and red tests | Complete | `test_project_identity_isolation.py`: expected projection failure; identity-only drift reproduced |
| 1 — allocator and scope | Complete | allocator `8 passed`; protected model/WUFI/METr/xl-replay gate `448 passed` |
| 2 — project libraries and patterns | Complete | focused `2 passed`; protected Phase 2 gate `466 passed` |
| 3 — envelope and geometry | Complete | focused/protected geometry + PHPP gate `312 passed` |
| 4 — zones/HVAC/distribution | Complete | isolation `5 passed` (parallel repeated 3x); broad gate `485 passed, 3 skipped` |
| 5 — WUFI explicit identities | Complete | focused/import/export gate `221 passed, 3 skipped`; no reference-file diff |
| 6 — export validation | Complete | validation/export/PHPP/xl-replay/PPP gate `386 passed, 3 skipped`; no reference-file diff |
| 7 — docs and closeout | Complete | no-reset reference/isolation `14 passed`; full suite `933 passed, 3 skipped, 1 deselected`; goldens unchanged |

## Decisions

1. Preserve clean-process golden bytes, including historical ID gaps.
2. Namespace identity by the consuming target/reference contract.
3. Use a conversion-local allocator; never reset globals inside conversion.
4. Preserve and reserve explicit WUFI IDs.
5. Keep HBJSON source-property ID writebacks compatible in the first release.
6. Keep legacy global fallback for direct standalone constructors initially.
7. Validate duplicate and dangling IDs at the affected exporter boundary.
8. Permit legal numeric reuse across independent namespaces.
9. Same-project and same-mutable-source concurrent mutation remain out of scope.
10. Retire unused counters only in a later explicitly approved normalization.
