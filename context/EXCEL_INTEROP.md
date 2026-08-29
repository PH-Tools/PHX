# PHPP Excel interop — constraints, ruled-out options, and hard-won gotchas

Why the PHPP write path looks the way it does. Read this **before** proposing a change to
how PHX talks to Excel, and before re-proposing a backend that was already ruled out.

Authoritative for *why*; `docs/dev/exporter-patterns.md` remains authoritative for *how*
the exporters are structured. The measured detail behind this summary lives in the
gitignored `plans/20260714/excel-interop-refactor/` packet (doc `06` is canonical there).

## 1. The non-negotiable constraint

**A live Excel calc engine is required.** The PHPP write path is interleaved: PHX writes,
Excel recalculates, PHX reads back PHPP-generated IDs and row numbers, then writes again.
Nothing that cannot recalculate can drive this path.

## 2. Ruled out — do not re-propose

| Option | Why it is dead |
|---|---|
| `openpyxl` | No calc engine; returns cached formula results only. (Fine for the *read-only* `from_PHPP` path, which is why that package exists — different job.) |
| `pycel` / `formulas` / `xlcalculator` | Partial Excel-function coverage; PHPP far exceeds it. Silently wrong numbers are worse than slow. OpenPH is the principled version of this idea. |
| LibreOffice headless (UNO / PyOO) | Drives LO Calc's engine, not Excel's. PHI documents functional limits for PHPP under LibreOffice; calc-fidelity risk would need its own validation harness. |
| Microsoft Graph API | No live interleaved recalculation for this workload. |
| Rolling our own appscript backend | Was proposed to escape xlwings overhead. Unnecessary — `raw_value` already reaches the OS floor (§3). |
| Tier 2 "Office.js localhost-WebSocket bridge add-in" | **NO-GO** at current numbers. |
| Tier 3 "shadow-PHPP" (predict all IDs, one bulk write, no mid-stream reads) | **Moot** — batching inside the existing architecture hit the target. Only revisit if the live path degrades badly again. |
| PR #47 async writes (never merged) | Races against interleaved read-back. Synchronous batching already beat its reported gains. |

## 3. What actually costs time (macOS)

Measured on Tahoe 26.5.1 / Excel 16.110.3, 2026-07-15:

- **AppleEvent floor: ~17 ms per round trip.** OS-level, not avoidable in-process. Track it
  with `scripts/perf/bench_interop.py` after OS/Excel updates.
- **The xlwings `.value` converter adds ~70–80 ms/op on top** — roughly 5× the floor.
  `raw_value` ≈ raw appscript ≈ the floor.
- **Block operations are nearly flat-cost.** A 1,000-cell block read costs about the same
  as a single-cell read. This is the whole basis of the batching strategy.

The 2026-07 slowdown ("Tahoe made xlwings unusable") was **mostly a PHX bug, not Tahoe**:
`XLConnection.get_sheet_by_name()` re-read all ~44 worksheet names live on every call —
94–97% of all round trips. Tahoe's higher per-event latency merely unmasked it. Net result
after caching + batching + raw writes: a real project went **3,524 s → 49.5 s (71×)**,
162,218 → 1,146 round trips.

**Lesson worth generalising:** the dominant cost hid inside a property, invisible to
method-level timing. Count round trips (`scripts/perf/profiling.py`), don't time methods.

## 4. Invariants any change to this path must hold

1. **Never pad block writes with `None`.** Writing `None` *clears* a cell, and untouched
   columns inside PHPP sections hold formulas. `xl_data.merge_xl_item_rows()` stacks only
   contiguous, actually-written column groups for exactly this reason.
2. **Keep the xlwings #1924 guard.** On macOS, block reads silently drop error-cells,
   shifting list positions. `get_row_num_of_value_in_column` guards with a length check and
   a per-cell fallback. Any new block-read code must keep that pattern.
3. **Reproduce the golden replay state.** `tests/test_xl_replay/` records exact cell writes
   and replays them without Excel. Re-record via `scripts/perf/record_replay_fixture.py`
   only when the output *legitimately* changes.
4. **Keep `tests/test_PHPP/` green** — it covers `XLConnection` via fakes, `XlItem` merge
   logic, shapes, and sheet IO.
5. **Windows stays on `.value`.** The `raw_value` write path is macOS-only; so are colored
   items, multi-cell block-clears, and empty lists.

## 5. Environment gotchas

- **macOS sandbox −1728:** a freshly launched Excel silently rejects automation-initiated
  `books.open()`, surfacing mid-export as "object does not exist". Open the file through
  LaunchServices first (`open -a`), then attach — see `scripts/perf/perf_paths.py`.
  An idle, book-less Excel can also wedge an AppleEvent indefinitely (0% CPU hang);
  force-quit and relaunch clears it.
- **Leading-apostrophe strings** (`"'Name"`) are stored by Excel as bare text — read-back
  never returns the apostrophe. The replay fake mirrors this.
- **honeybee-energy library materials are shared singletons.** A test that mutates one
  without restoring corrupts every model loaded later in the same pytest run. Restore in a
  `finally`.
- **Never run live-Excel scripts unattended**, or while an export is in progress. Target an
  explicit scratch copy, never `books.active`. Licensed PHPP workbooks stay in the
  gitignored `plans/` folder or a scratch dir — never committed.

## 6. Remaining levers (optional, none required)

Post-optimisation the residual profile is read-dominated (~25 s of 49.5 s, still on the
converter path). In rough priority: raw-value **read** paths (needs `k.missing_value`
cleaning without importing appscript into PHX); the ~120 legacy `.value` block-clear sets;
column-direction blocking for the U-values constructor writes; extending read memoization
to single-cell `get_data`. Full table with estimates: packet doc `06` §5.
