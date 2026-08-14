# STATUS — project-scoped-identities

**Status:** In progress · 2026-08-14

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
- **Next step:** migrate project libraries/patterns and then the remaining
  entity families so the Phase 0 sequential test turns green.
- Blockers: none. Do not begin broad `_count` deletion or golden regeneration;
  both are explicitly outside the compatibility-first implementation.
- Planning verification: 107 existing facade, WUFI/METr reference, WUFI import,
  PHPP ventilator/duct, and xl-replay tests pass (`107 passed in 3.46s`).

## Phase evidence

| Phase | Status | Red/green evidence |
|---|---|---|
| 0 — baselines and red tests | Complete | `test_project_identity_isolation.py`: expected projection failure; identity-only drift reproduced |
| 1 — allocator and scope | Complete | allocator `8 passed`; protected model/WUFI/METr/xl-replay gate `448 passed` |
| 2 — project libraries and patterns | In progress | next |
| 3 — envelope and geometry | Pending | — |
| 4 — zones/HVAC/distribution | Pending | — |
| 5 — WUFI explicit identities | Pending | — |
| 6 — export validation | Pending | — |
| 7 — docs and closeout | Pending | — |

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
