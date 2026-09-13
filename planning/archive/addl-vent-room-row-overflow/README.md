# `Addl vent` room rows overflow the shipped 30-row block silently

- **Status:** Implemented on branch `bug-fix/phpp-writer-fix-batch` (2026-09-12). Decisions D1/D1a and the sibling audit are in [`../phpp-writer-fix-batch.md`](../../bug-fix/phpp-writer-fix-batch.md): rooms, units and ducts share one guard that locates each section's first and last entry rows before writing, warns, and truncates
- **Filed:** 2026-09-02 (Ed May / Claude)
- **Origin:** phx-phpp-bridge Phase 0a replay work (Gate G-A record,
  `phx-phpp-bridge/planning/phases/phase-0a-executor-runtime-spikes.md`,
  "Findings carried to 0b" item 2)
- **Kind:** missing guard/warning in the PHPP writer; the data loss is in
  the workbook's own aggregation ranges, not in what PHX writes

## Observed behavior

A recorded production export (44 ventilated spaces → blank
`PHPP_EN_V10.6_Empty.xlsx`) writes `Addl vent` room rows at **31:74** —
14 rows past the shipped block. Verified from the golden replay fixture
(2,934-cell recording, 2026-09-01) and reproduced identically through the
Bridge's Office.js replay. No warning is raised on either path.

The shipped 10.6 workbook has **30 room rows (31:60)**, and every
aggregation over them agrees with that bound (phi-rules `Addl vent`
teardown, verified against the blank 10.6 workbook):

```
Addl vent!AD70 = SUMIF($F$31:$F$60,$C70,AF$31:AF$60)   ← unit totals
Addl vent!F27  = IF(MAX(F31:F60)>C79,"Max. " &C79,"")  ← display checks
```

## Consequences of writing past row 60 on an unextended workbook

1. **Rooms 31+ are invisible to the unit `SUMIF`s and display totals** —
   their airflows silently vanish from the ventilation aggregation while
   the rows look fully populated. This is the reputational failure mode:
   quiet data loss in a certification workbook.
2. Row 61 (the workbook's own copy/insert instruction row with subtotals
   over `31:60`) and the unit-header labels in rows 62–69 are overwritten,
   including the merged label cells `R64:T64` / `U64:V64`
   ("Troom > / < Toutdoor").
3. Downstream interop asymmetry: xlwings writes into those merged label
   cells (redirected into the merged area); Office.js drops the non-anchor
   writes silently — so the two executors produce different stored bytes
   in exactly the overflow region and nowhere else.

PHPP's supported mechanism for more rows is the separate
`PHPP_V<version>_Tools.xlsm` macro workbook (referenced in-workbook at
`Windows!L179`) — and the phi-rules ventilation checklist records that
even a properly extended workbook can end up with inconsistent
aggregation ranges, so extension is a user/certifier action, not
something the writer should attempt.

## Proposed fix (Ed's direction, 2026-09-02)

**Raise an Excel-side warning when a section write would overflow the
allowed area** — the same pattern as the stale-rows warning shipped in
PR #100 (`xl.output` warn from the Components list-writers):

- The `Spaces` writer (`PHX/PHPP/sheet_io/io_addnl_vent.py`) already
  locates the section (`find_section_header_row` /
  `find_section_first_entry_row` / `find_section_last_entry_row`); it
  should determine the section's **capacity** (last allowed entry row on
  the actual workbook — which also handles user-extended workbooks
  correctly, per the teardown's "locate the row by header in the file you
  actually have" rule) and compare against the entry count before writing.
- On overflow: warn loudly via `xl.output` naming the sheet, the capacity,
  the entry count, and the PHPP Tools extension mechanism. Open decision
  for implementation time: warn-and-truncate vs warn-and-write-anyway vs
  refuse — leaning **warn loudly, do not write past the capacity** given
  consequence 1, but that changes validated output and needs Ed's call.
- Audit the sibling list-writers with the same shape (`Addl vent 2`,
  units rows 70:79, duct rows 97:129, and any other entry-block writer
  fed by a variable-length model list) for the same missing guard.
- Re-record the xl-replay golden fixture only if the chosen behavior
  legitimately changes the written cells (hard rule 4).

## Verification sketch

- Unit test against the fake xl framework: model with > capacity rooms →
  warning emitted, writes bounded per the chosen policy.
- Existing replay invariant stays green for models within capacity.
