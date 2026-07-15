# Perf Baselines

Committed Tier-0 deliverables, one file per run/machine:

- `bench_interop__<host>__<ts>.json` — T0.2 per-op latency tables (includes the T0.1 Excel-build check in `meta`).
- `profile__<label>__<ts>.json` — T0.3 export profiles: facade-method timing + (with `--deep`) low-level round-trip counts.
- `golden_readback__<label>.json` — T0.5 golden H2 extracts used for Tier-1 before/after equivalence checks.
