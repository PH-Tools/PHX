# PHPP writer fix batch: `01` + `02` + `04` + `Addl vent` capacity

- **DATE:** 2026-09-12
- **STATUS:** Scoped (plan only; no implementation authorized)
- **AUTHOR:** Ed May / Claude
- **ISSUE:** [#103](https://github.com/PH-Tools/PHX/issues/103) items 01, 02, 04 (refs, not closes: 03 stays open); [#115](https://github.com/PH-Tools/PHX/issues/115) (closes)

One branch, one PR, one xl-replay golden-fixture re-record. This file sequences
the batch, records the decisions, and carries the `Addl vent` sibling audit. It
does **not** restate the per-item phases; each item doc is the spec its builder
executes:

| Item | Spec | Size |
|---|---|---|
| `01` Verification version guard | [`phpp-writer-input-gaps/01-verification-version-guard.md`](phpp-writer-input-gaps/01-verification-version-guard.md) | S |
| `02` Ventilation wind protection | [`phpp-writer-input-gaps/02-ventilation-wind-protection.md`](phpp-writer-input-gaps/02-ventilation-wind-protection.md) | S |
| `04` Climate UD block activation | [`phpp-writer-input-gaps/04-climate-ud-block-activation.md`](phpp-writer-input-gaps/04-climate-ud-block-activation.md) | **M** |
| `#115` `Addl vent` capacity (rooms + units) | [`addl-vent-room-row-overflow/README.md`](addl-vent-room-row-overflow/README.md) + the audit below | S |

`04` was first triaged as small. Its Phase 1 is; its Phase 2 gate (cascading,
recalc-dependent membership check across three selectors, with a revert path) is
the largest piece of the batch.

## Why batch them

All four land in the PHPP write path and all but `#115` move the golden state
(hard rule 4). Re-recording needs live Excel and the licensed template, so one
re-record for the batch instead of three. Code touched is disjoint:
`write_certification_config`, the `VENTILATION` shape + `io_ventilation`,
`climate_entry` + `io_climate`, `io_addnl_vent` + the two `phpp_app` callers. Only
the localization JSONs are shared (`02` and `04`, different keys).

## Decisions

| # | Decision | Status |
|---|---|---|
| D1 | `#115` detection: locate the section's first **and** last entry row from the workbook's own locators as a single up-front operation, **before any write**, and derive capacity from those. Never assume a row count: users insert rows. | **Settled** (Ed, 2026-09-12) |
| D1a | `#115` over-capacity policy: warn and truncate at capacity, matching the existing duct writer (`phpp_app.write_project_vent_ducting`, `PHPPVentDuctWarning` then `rows[:row_capacity]`) | **Settled** (Ed, 2026-09-12). Writing past the block adds nothing (rows past the block are outside the workbook's `SUMIF`s) and overwrites the rows below it |
| D2 | `04` scope: all phases (1-3) | **Settled** (Ed, 2026-09-12) |
| D3 | `02` on PHPP 9: no change | **Settled by inspection**, see below |
| D4 | `02` on PHPP 10.x: drop **both** the `J19` and `J20` writes; write the class to `K19`; do **not** write f (`M20`), and warn when the model's f is not 15 | **Settled** (Ed, 2026-09-12), see below. **Overrides the `02` item doc's Phases 1, 3 and 5** |
| D5 | Sibling audit of the other `Addl vent` list-writers, code only where a gap is confirmed | **Settled** (Ed, 2026-09-12); done below |

### D3: PHPP 9.6a wind protection (read 2026-09-12)

Read from a PHPP 9.6a EN example workbook (private corpus, structure only). PHPP 9
has **no** wind-protection class drop-down. The coefficient table sits at
`Ventilation!N17:O23` (several-sides / one-side exposed columns), and the inputs
are two numeric cells on the `"Wind protection coefficient, e"` / `", f"` rows:
`N25` (e, validated against the `PHPP_Daten_Windschutzkoeff` list) and `N26`
(f, validated against `$N$23:$O$23`). `EN_9_6A.json` and `EN_9_7IP.json` already
point `wind_coeff_e` / `wind_coeff_f` at `input_column: "N"` on those locator
rows, so PHPP 9 receives both coefficients correctly today.

Consequence for `02`: the shape and writer change applies to the **five 10.x
shapes only** (`EN_10_3`, `EN_10_4A`, `EN_10_4IP`, `EN_10_6`, `EN_10_6IP`). The
9.x shapes get no `wind_protection_class` entry and the writer skips when the
entry is absent. Update the `02` doc's Phase 4 with this result instead of
re-running it. The 9.x check is `EN_9_7IP` by analogy with `EN_9_6A`; confirm on
a 9.7 IP workbook if one is in the corpus.

### D4: PHPP 10.6 wind-protection cells (read 2026-09-12)

Formatting and protection read from the blank EN 10.6 template (`Ventilation` is a
protected sheet):

| Cell | Content | Protection / format |
|---|---|---|
| `K19` (merged `K19:L19`) | class drop-down, validation list `$AA$17:$AA$20` | **unlocked**, input fill |
| `M19` | `=IF(K19="",Z18,INDEX(Z18:Z20,LEFT(K19,1)))`, displays e | locked |
| `J19`, `J20` | empty, read by nothing | locked, no fill, no validation |
| `M20` | literal f = 15 | **locked**, no validation |

- **`J19`:** the item doc called it "a visible yellow input cell". It is not: it is
  empty, locked and unformatted. Once `K19` carries the class, `M19` already
  displays e, and a number left in `J19` goes stale the moment a user changes the
  drop-down. Drop the write.
- **f / `M20`:** PHPP 10 ships f as a locked constant (PHPP 9 offered 15 or 20 through
  a validated input; 10.x removed the choice). PHX unprotects sheets before writing,
  so it *could* overwrite `M20`, but that would override a value PHI locked on
  purpose. Do not write f on 10.x. When `PhxPhBuildingData.wind_coefficient_f != 15`,
  emit one `xl.output` warning that PHPP 10 fixes f at 15 and the model value was not
  written. Remove the `wind_coeff_f` entry from the five 10.x shapes (or leave it
  unused and say so in the shape); keep it in the 9.x shapes, where `N26` is a real
  input.

Noted, not in scope: PHPP 9's one-side-exposed coefficients and f's second
option have no PHX source. `PhxPhBuildingData.wind_coefficient_e` folds the
`ONE_SIDE_EXPOSED_*` members into the several-sides value. A model gap, not a
writer defect.

## `Addl vent` sibling audit (2026-09-12)

Code read of `PHX/PHPP/sheet_io/io_addnl_vent.py` and its `phpp_app` callers,
checked against the blank EN 10.6 template (structure only):

| Section | First entry locator | End locator | Blank 10.6 block | Capacity guard today |
|---|---|---|---|---|
| Rooms (`Spaces`) | `"Room"` header in `C`, then `1` in `C` | first empty `C` cell below first entry | rows 31-60 (30); `C61` empty, instruction text in `D61` | **None.** `write_spaces` only finds the first row; `find_section_last_entry_row` is used by the reader alone |
| Units (`VentUnits`) | `"Venti-"` header in `C`, then `1` in `C` | first empty `C` cell, minus 1 | rows 70-79 (10); `C80` empty, duct section title at `C82` | **None.** `write_vent_units` writes from the first row with no bound; unit 11+ lands in rows 80-82 |
| Ducts (`VentDucts`) | `"Round"` header in `E`, then a **hard-coded** `header + 9` | `"Additional"` instruction text in `D`, minus 1 | rows 95-114 (20); header `E86`, instruction `D115` | **Present**: capacity check + warn + truncate in `phpp_app` |

Findings to fix in this batch:

1. **Rooms and units need the D1 guard.** Both sections get the duct pattern:
   locate first and last entry once, compute capacity, warn with sheet, section,
   entry count, and capacity, and name the PHPP Tools workbook as the supported
   way to extend. Units overflow is less likely (10 slots) but corrupts the duct
   section title when it happens.
2. **The three `find_section_last_entry_row` methods disagree on what they
   return.** `Spaces` returns the first **empty** row (61, one past the block);
   `VentUnits` and `VentDucts` return the last **entry** row (79, 114). A
   capacity computed as `last - first + 1` is off by one for rooms. Normalize
   `Spaces` to return the last entry row, and move `read_space_data` (its only
   caller, which reads `first - 3 : last`) to the new meaning. The reader
   currently includes the instruction row in its range; confirm nothing depends
   on that.
3. **Put the guard in `AddnlVent`, not in each `phpp_app` caller.** The duct
   guard lives in `phpp_app.write_project_vent_ducting`. One helper on
   `AddnlVent` (or on the section classes) that returns the bounded row list and
   emits the warning serves all three; move the duct check onto it so the three
   sections share one message format. The duct warning text changes wording only.
4. **Each section's first `find_section_shape()` call must precede its write.**
   Today `Spaces.find_section_last_entry_row` lazily finds the first row inside
   itself, and the section classes cache on `None` checks (`if not
   self.section_first_entry_row`). The guard reads both rows before writing so an
   earlier overflow export cannot move the detected end.

Fragilities recorded, not fixed here (each is its own issue if it bites):

- `VentDucts.find_section_first_entry_row` uses the hard-coded `header + 9`
  offset. Correct on blank 10.6 (header 86, first formula row 95).
- `VentUnits.find_section_last_entry_row` scans 50 rows and `VentDucts` 100 rows
  with no extension, so a user-extended units block over 50 rows or duct block
  over 100 rows raises instead of being measured. `Spaces` already extends its
  scan.
- Shrinking exports leave stale rows in all three sections (the Components
  stale-rows problem from PR #100, not yet applied to `Addl vent`).

Out of this audit: the `Areas`, `Windows`, and `U-Values` constructor sections
(#23) and the `Variants` window block (#16).

## Build order

Each step is its own commit on branch `bug-fix/phpp-writer-fix-batch`, following
its item doc's phases (failing test first, then fix). The replay invariant test
(`tests/test_xl_replay/test_replay_invariant.py`) is **expected red** from step 1
until step 5; everything else stays green. Do not push until step 5.

1. **`01`**: narrow the guard (`return` becomes a skip of the nine enum writes;
   warn once, not per variant); resolve `PhiCertType.OTHER = 44` against the blank
   10.6 `Verification` drop-down; parametrized enum-vs-shape test for every v9/v10
   enum. PR #113 added `mechanical_cooling` below the same guard, so the expected
   fixture diff gains `Verification!N30` alongside `F29`/`K28`/`N28` (confirm
   whether an empty-string write is recorded).
2. **`02`**: follow the item doc's Phases 0 and 2, with D3 and D4 overriding
   Phases 1, 3 and 5. On the five 10.x shapes: add `wind_protection_class`
   (`options` keyed by coefficient, input column `K`), stop writing `J19` and
   `J20`, never write `M20`, warn once when the model's f is not 15. On 9.x: no
   class entry, `N25`/`N26` writes unchanged. Tests: the three coefficients reach
   `K19` as the matching literal; no write to `J19`, `J20` or `M20` on 10.x; the
   f warning fires for f = 20 and not for f = 15; a 9.x shape still writes
   `N25`/`N26` and no class; `K12`, `K15`, `M22`, `M23` unchanged.
3. **`#115` + audit**: fake-XL tests first. Rooms with capacity + 1 entries and
   units with capacity + 1 entries: warning emitted, no write past the last entry
   row. A user-extended rooms block (e.g. 40 numbered rows): capacity 40, no
   warning for 35 rooms. Then findings 1-4 above. No golden change expected
   (`Single_Zone` fits all three sections).
4. **`04`**: Phases 1-3 of the item doc, including the `PhxPHPPCodes.dataset_name`
   annotation fix and the non-empty `display_name` readiness check.
5. **Re-record** with `scripts/perf/record_replay_fixture.py --yes` (Claude-driven;
   probe `osascript -e 'tell application "Microsoft Excel" to get version'` first,
   one attempt, then hand Ed the command). Diff old and new fixture and confirm the
   change is exactly:
   - `Verification`: `F29`, `K28`, `N28` (+ `N30` per step 1); **no** enum cells
   - `Ventilation`: `K19` added (`1-No protection` for `Single_Zone`'s default
     exposure), `J19` and `J20` removed, `M20` not written
   - `Climate`: one of the two branches in `04` Phase 4 (library path: UD block
     cells vanish; UD path: `D9`/`D10`/`D12` switch to `ud-` literals, `D67`/`E76`
     added, `L67`/`P67` removed). Record which branch fired in the `04` doc
   - `Addl vent`: unchanged

   Any other cell in the diff is a defect in steps 1-4, not a fixture update.
6. **Closeout**: `python -m pytest tests/`; tick 01/02/04 on #103; PR body
   `Closes #115`, `Refs #103`; `planning/STATUS.md` rows; fold the `M20`/`J20`
   finding and the 10.6 `P67`/`E76` column roles into the `phi-rules` corpus (per
   the `02` and `04` closeout steps, plus the D4 finding that 10.6 locks f at
   `M20`); file issues for any audit fragility we
   decide to track.

## Execution model

Claude holds the specs (the item docs plus this file) and reviews; codex
(`gpt-5.6-sol`, `codex-implementation` skill) builds steps 1-4, one bounded run
per item so each diff is reviewed before the next starts. Claude runs step 5
(live Excel) and step 6.

## Out of scope

- `03` SummVent heat-recovery mode: gated on reading one WUFI-Passive model's summer setting in the UI
- Capacity pre-checks for `Areas`, windows, constructors (#23) and the caller-readable warning channel (#62)
- Multi-variant semantics (last variant wins, per the #103 README)
