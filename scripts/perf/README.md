# scripts/perf — Tier-0 Excel Interop Harnesses

Triage/benchmarking tooling for the xlwings-on-macOS-Tahoe slowdown. See the
working plan: `plans/20260714/excel-interop-refactor/04_tier0-tier1-plan.md`.

**These scripts are NOT shipped with the PHX package** (packaging includes
`PHX*` only) and are excluded from the default pytest run where they touch
live Excel.

## ⚠️ Ground rules

1. **Manual invocation only.** Never run any of these while a production PHPP
   export is in progress — every script prompts before touching Excel
   (`--yes` skips the prompt; only use it when you are certain).
2. **Never open the PHPP template for a write-run.** `profile_export.py`
   always copies the template into the scratch dir first. Keep PHPP copies
   under `plans/` (gitignored) — never under `tests/` or `scripts/`.
3. Nothing here ever attaches to `books.active` unattended — workbooks are
   always targeted by explicit path, or are brand-new scratch books.

## Scripts

| Script | Plan task | What it does |
|---|---|---|
| `bench_interop.py` | T0.2 | Per-op latency: xlwings vs xlwings `raw_value` vs raw appscript, on a scratch workbook. Also records the Excel build check (T0.1). |
| `profile_export.py` | T0.3 / T0.5 | Full HBJSON→PHPP export on a scratch copy of the template, instrumented with the H1 profiler. `--deep` adds low-level round-trip counting; `--golden` saves + captures the H2 golden read-back. |
| `readback_verify.py` | H2 | Extract key PHPP result cells → JSON (`extract`), and diff two extracts with tolerance (`compare`). Default backend is openpyxl on a *saved* file — no live Excel needed. |
| `profiling.py` | H1 | Library: `ProfiledXLConnection` (facade-method timing) + `CountingFrameworkProxy` (low-level event counts). |
| `perf_paths.py` | — | Path/config resolution, scratch-copy helper, environment metadata (T0.1). |

## Typical Tier-0 session

```bash
source .venv/bin/activate

# T0.1 + T0.2 — microbenchmark (records Excel build in the baseline):
python scripts/perf/bench_interop.py

# T0.3 quick pass, then the real baseline:
python scripts/perf/profile_export.py --label smoke
python scripts/perf/profile_export.py --hbjson plans/20260714/excel-interop-refactor/test_files/Linde_Home.hbjson \
    --deep --golden --label linde

# Later: verify a Tier-1 refactor run against the golden capture:
python scripts/perf/readback_verify.py compare \
    scripts/perf/baselines/golden_readback__linde.json  new_extract.json
```

## Configuration

Inputs default to the packet's `test_files/`. Override per-file via CLI args,
env vars (`PHX_TEST_PHPP`, `PHX_TEST_HBJSON`, `PHX_PERF_SCRATCH`), or a
gitignored `scripts/perf/config.local.json`:

```json
{ "phpp": "/path/to/PHPP_DE_V10.6.xlsx", "hbjson": "/path/to/model.hbjson" }
```

## Outputs

Timing/count baselines and golden read-backs land in `scripts/perf/baselines/`
(committed — they are the Tier-0 deliverables). The read-back cell set is
`readback_spec_en_v10.6.json`; block-count entries are heuristics to be
validated during the first golden capture (T0.5).

## Offline tests

`tests/test_scripts_perf/` unit-tests the H1 profiler and the H2 spec engine
against the in-memory `xl_typing` doubles — CI-safe, no Excel required.
