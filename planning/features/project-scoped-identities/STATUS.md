# STATUS — project-scoped-identities

**Status:** Requested · 2026-08-14

- No concurrent-output defect is currently claimed; this packet records a
  concrete architecture risk and a production-readiness verification gap.
- Current reference tests reset `_count` ClassVars and reload model modules to
  regain deterministic identities.
- **Next step:** complete the counter/reference audit, write a parallel
  conversion test against sequential baselines, and use any reproduced drift to
  guide the smallest allocator design.
- Blockers: none for audit/tests. Preserve imported-ID and PHPP xl-replay
  contracts during architecture design.

