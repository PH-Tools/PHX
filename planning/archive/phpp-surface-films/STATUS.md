# Status — PHPP surface-resistance selectors

DATE: 2026-09-10
STATUS: Complete
ISSUE: https://github.com/PH-Tools/PHX/issues/118

| Phase | State |
|---|---|
| 1 — selector strings in the shape files | Complete |
| 2 — `ConstructorBlock` writes the selectors | Complete |
| 3 — resolve exposure from the components | Complete |
| 4 — `activate_variants` restores the selectors | Complete |
| 5 — golden state, suite, docs | Complete |

**Next step:** none. Merged to `main` 2026-09-10 via PR [#119](https://github.com/PH-Tools/PHX/pull/119) (squash), closing [#118](https://github.com/PH-Tools/PHX/issues/118). Packet archived.

**Blockers:** none.

## Verification (2026-09-10)

- `python -m pytest tests/` — 1125 passed, 3 skipped, 1 deselected.
- `python -m black --check .` — 442 files unchanged.
- `tests/test_xl_replay/` golden state moved in exactly the six cells listed in
  `PLAN.md` Phase 5; the replay invariant passes, which is what proves no other
  written cell moved.
- Hand check of the worked example, driven through the real writer: a declared-U
  assembly (`R_layer = 6.4967`) writes `2-Wall` / `1-Outdoor air`, so PHPP's
  `AJ25 = 0.13 + 6.4967 + 0.04` resolves `R25` to `0.1500 W/m2K` — the declared
  value, and what WUFI/METr already produced. It was `0.1539` before.

## Phase 3 note

`_rank_assembly_exposures` landed as a pure `@staticmethod` returning every
`(face-type, exposure)` pair ranked by area, rather than the resolved single pair
the plan described. The caller takes `[0]` and emits the mixed-use warning, which
keeps the resolver unit-testable without an Excel connection — the same shape as
the neighbouring `_collect_custom_groups`.

## Follow-ups (not this packet)

- **Verify the selector strings against a 9.x and an IP workbook.** Phase 1
  ships the 10.6 EN strings in all seven shape files. Only the leading digit is
  read by PHPP 10, so label drift is harmless there; a different digit order in
  another edition would not be. No archived 9.x or IP workbook exists to check
  against.
- **A live re-record of the replay fixture.** Phase 5 edits six golden entries
  in place. A full re-record needs Excel + the licensed template, same
  precondition as the open fixture follow-up, issue
  [#102](https://github.com/PH-Tools/PHX/issues/102).
- **One assembly at two exposures.** The writer picks the dominant exposure by
  area and warns. Splitting such an assembly into two PHPP blocks (which is the
  manual fix) would touch assembly identity, the `Areas` assembly-ID references
  and the Variants layer list. File separately if a real model hits it.
- **`get_constructor_r_si_type` / `get_constructor_r_se_type` docstrings** say
  the cells return `"Wall"` / `"Outdoor air"`; the workbook returns the
  digit-prefixed `"2-Wall"` / `"1-Outdoor air"`. Cosmetic, in the read path.
- **`clear_single_constructor_data`** hardcodes `+4` / `+5` instead of using
  `rsi_row_offset` / `rse_row_offset`. Same values today.
- **Licensing.** `tests/test_xl_replay/fixtures/single_zone_replay.json` is
  tracked in the public repo and its `seed` block holds first-read cell values
  from the blank PHPP template. Worth a separate look against the
  licensed-documents rule; pre-existing, unrelated to this fix.
