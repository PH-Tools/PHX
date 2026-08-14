# Phase handoff index

Each phase is a self-contained implementation brief. Read `../AUDIT.md`,
`../PRD.md`, and `../PLAN.md` before starting. Execute in order; do not combine
phases merely because adjacent files overlap.

| phase | brief | principal green gate |
|---|---|---|
| 0 | `PHASE-0-baselines-and-red-tests.md` | current clean goldens pinned; leakage tests red |
| 1 | `PHASE-1-allocator-and-scope.md` | allocator/context unit suite green |
| 2 | `PHASE-2-project-libraries-and-patterns.md` | top-level/library/pattern identities isolated |
| 3 | `PHASE-3-envelope-and-geometry.md` | envelope/geometry identity projection isolated |
| 4 | `PHASE-4-zones-hvac-and-distribution.md` | HBJSON sequential + parallel conversion green |
| 5 | `PHASE-5-wufi-explicit-identities.md` | sparse explicit IDs preserved/reserved |
| 6 | `PHASE-6-validation-and-export-gates.md` | duplicate/dangling reference tests green |
| 7 | `PHASE-7-cleanup-docs-and-closeout.md` | full suite + docs + status complete |

Every phase uses red-green-refactor and records exact commands/results in
`../STATUS.md`. A phase is not complete because its production edits are present;
its definition of done and regression gates must also pass.
