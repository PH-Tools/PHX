# PHPP writer input gaps — six defects

**Status:** Scoped — 2026-08-15. No PHX code changed yet. Item `06` added
2026-08-15 (a sixth input, found by OpenPH the same day); `05` now depends on
the upstream foundation-shape packet.
**Source:** [`features/phpp-writer-input-gaps/`](../../features/phpp-writer-input-gaps/README.md) (the incoming request, filed from OpenPH)

Five inputs that the PHX model carries and that PHPP ends up computing without —
plus a sixth (`06`) that the model does not carry at all yet.
Every claim below was re-verified against the code and against the blank
`PHPP_EN_V10.6_Empty.xlsx` before this folder was written; the incoming request
was **not** taken at face value, and three of its five diagnoses changed.

## Read order

1. This file — what changed from the request, the shared constraints, sequencing.
2. One file per defect, `01`…`06`.

## The six, as verified

| # | Defect | Target | Silent? | Verdict vs. the request |
|---|---|---|---|---|
| [01](01-verification-version-guard.md) | Version guard drops the whole `Verification` sheet | `Verification` (12 writes) | flagged | **Re-diagnosed** — a writer for `F29` already exists |
| [02](02-ventilation-wind-protection.md) | Wind protection written to two dead cells | `Ventilation!K19`, `M20` | **silent** | **Confirmed and enlarged** — `f` is broken the same way |
| [03](03-summvent-heat-recovery-mode.md) | Summer heat-recovery mode never written | `SummVent!R15:R18` | **silent** | Confirmed |
| [04](04-climate-ud-block-activation.md) | User-defined climate block never named or selected | `Climate` D67 / D9 / D10 / D12 / E76 | **silent** | **Confirmed and enlarged** — plus a cell PHX actively corrupts |
| [05](05-ground-worksheet-writer.md) | No `Ground` writer at all | `Ground` (whole sheet) | flagged | Confirmed — **now depends on** [`features/foundation-phpp10-shape/`](../../features/foundation-phpp10-shape/README.md) for the model fields it was going to leave at template defaults |
| [06](06-verification-mechanical-cooling.md) | `Verification!N30` mechanical cooling never written; no model field | `Verification!N30` → `Ground!N122`, `I39/I40`, `Windows!AJ10:AJ14`, `SummVent!L66/R66` | **silent** | New 2026-08-15 — needs a honeybee-ph field first |

### What changed from the incoming request

- **#1 is not a missing writer.** `phpp_app.py:268` already writes `num_of_units`
  to `Verification!F29`. It never runs because a version-match guard 80 lines
  above `return`s out of the entire method. The blank `F29` is collateral; the
  real defect drops **12** inputs, not one. See [01](01-verification-version-guard.md).
- **#3 is two cells, not one.** `Ventilation!J19` is ignored — as filed — but so
  is `J20`, where PHX writes the `f` coefficient. PHPP reads `f` from `M20`.
  Nobody has noticed because PHX's default `f` (15) equals the template's.
  See [02](02-ventilation-wind-protection.md).
- **#5 is three defects, not one.** Beyond the unwritten block name, PHX writes
  `display_name` into `L67` (a cell nothing reads) and `source` into `P67` —
  which is the **`T Comfort criterion [°C]`** numeric input. PHX puts a string
  there on every export. See [04](04-climate-ud-block-activation.md).

### What held up exactly as filed

`SummVent!R15:R18` and the missing `Ground` writer. `GROUND` and `SUMM_VENT` are
name-only stubs (`{"name": ..., "columns": {}}`) in all seven localization files
and are referenced by no writer.

## Evidence base

Two independent sources agree, which is why these are filed as defects rather
than investigations:

1. **`tests/test_xl_replay/fixtures/single_zone_replay.json`** — the repo's own
   recording of `write_phx_project_to_phpp` against `PHPP_EN_V10.6_Empty.xlsx`.
   Clean run: 0 conflicts, 0 skipped reads. Sheets that received any write:
   `Climate`, `U-values`, `Areas`, `Ventilation`, `Electricity`. `Verification`,
   `Ground` and `SummVent` are present in the workbook and got **zero** writes.
2. **The blank 10.6 template itself**, read with `openpyxl` (formulas and cached
   values). Every cell address, default and formula quoted in these five files
   was read out of that workbook, not inferred.

## Shared constraints

**The replay invariant will break on every one of these.**
`tests/test_xl_replay/test_replay_invariant.py` asserts the written cell-state
matches the golden fixture *exactly* — it reports `EXTRA write` as a failure.
Any new cell fails it by design (CLAUDE.md hard rule 4). Re-recording needs
live Excel + `xlwings` + the licensed template
(`scripts/perf/record_replay_fixture.py`, gated by `confirm_live_excel_run`),
so it cannot happen in CI. Each packet therefore ends with an explicit
re-record step, and each packet's own unit tests must stand on their own until
that happens.

**The `x`-cell vocabulary is fixed.** `PHPP_Daten_Ankreuzen` resolves to
`Data!A376:A377` = `["", "x"]`. Selecting is `"x"`; clearing a sibling is `""`,
not `None`. Formulas test `="x"` exactly — lowercase, no whitespace.

**One variant wins.** Every existing writer loops `for variant in
phx_project.variants` with a standing `# TODO: how to handle multiple
variants?`; last-variant-wins. None of these packets should try to solve that —
match the convention, leave the TODO. (This settles open question 1 in the
incoming request.)

## Decisions taken

| Date | Item | Decision |
|---|---|---|
| 2026-08-15 | [04](04-climate-ud-block-activation.md) climate activation | **Gate on the codes.** Valid library country/region/data-set → library path, UD block not written. Anything invalid → fall back to the UD block from model data. "Valid" is a cascading, recalc-dependent membership check, because `D12`'s validation list is derived from `D9`/`D10` |
| 2026-08-15 | [05](05-ground-worksheet-writer.md) ground scope | **Single foundation, building section 1 only.** `len(foundations) > 1` raises. Multi-section needs the `Areas` group-`B` total split per foundation — an `Areas`-writer change, deferred until a real model needs it |

## Sequencing

`01` first and alone: it is the cheapest, it restores the most inputs, and it
touches nothing the others touch. `02` is independent. `03` introduces a
radio-group write helper that `05` reuses, so `03` before `05`. `04` is
independent. `05` is its own PR, needs a corpus pass before any code, and its
model layer (Phase 2) waits for the upstream foundation-shape release. `06` is
one `write_item` once honeybee-ph carries the flag; it lands in the same method
`01` narrows, so `01` before `06`.

```
01 ──┬──────────────────────────────────▶  (independent, do first)
     └──▶ 06 ─────────────────────────▶    (same method; needs hb-ph flag)
02 ─────────────────────────────────────▶  (independent)
03 ──┬──────────────────────────────────▶  (radio-group helper)
     └──▶ 05 ─────────────────────────▶    (reuses the helper; model layer
             ▲                              waits for foundation-phpp10-shape)
foundation-phpp10-shape (hb-ph → PHX) ──┘
04 ─────────────────────────────────────▶  (independent)
```

`01`–`04` are small enough to ship as one PR or four; `05` should not be
bundled with them; `06` ships with `01` if the honeybee-ph release is out by
then, otherwise on its own.

## Out of scope for all six

- The PHPP **read** path. These are write-side defects only.
- **`Check` worksheet integration.** Reporting PHPP's own error count after a
  write would have caught `01` and `05`, and is worth doing — as its own item.
- **Multi-variant semantics** (see above).
