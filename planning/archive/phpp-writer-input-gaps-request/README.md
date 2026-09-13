# phpp-writer-input-gaps

**Status:** Requested (2026-08-15)

Five inputs the PHX model carries and the PHPP writer does not write. Each one
leaves PHPP computing from a **blank-template default** — a value that describes
some other building — and none of them raises anything. Two are flagged by
PHPP's own `Check` worksheet; three are silent.

Filed from outside PHX. All five were found while producing a machine-written
PHPP reference workbook for OpenPH, and every one was found the same way: by
noticing a demand number that was wrong by a factor, then tracing back. That
detection method does not scale, and a PHX user exporting to PHPP has no
equivalent of the audit that caught these.

## Read order

1. [`PRD.md`](PRD.md) — the five gaps, one section each: model source, PHPP
   target cell, what PHPP does without it, and the measured cost.
2. [`STATUS.md`](STATUS.md) — current state, evidence, open questions.

## Scope in one line

Give `phpp_app.py`'s canonical write sequence a writer for each of
`Verification!F29`, `SummVent!R15:R18`, `Ventilation!K19`, the `Ground`
worksheet, and `Climate!D67` — all sourced from the PHX model, none hardcoded.

## The five

| # | Input | PHPP target | Silent? | Measured cost |
|---|---|---|---|---|
| 1 | Number of dwelling units | `Verification!F29` | flagged | internal heat gains → **0 kWh** |
| 2 | Summer heat-recovery mode | `SummVent!R15:R18` | **silent** | vent conductance 26.400 W/K vs 9.213 |
| 3 | Wind-protection class | `Ventilation!K19` | **silent** | infiltration at e=0.070 vs authored 0.100 |
| 4 | Ground / floor-slab type | `Ground` (whole sheet) | flagged | no slab type selected; sheet computes nothing |
| 5 | User-defined climate name | `Climate!D67` | **silent** | active-climate selector points at nothing |

No. 3 is the sharpest: PHX **does** write the wind coefficient, into
`Ventilation!J19` — a cell PHPP ignores. The intended value sits one cell to the
left of the one that matters, which makes the workbook look correct on
inspection.

## Not in scope

The ventilator-registration defect from the same investigation. That is
[`archive/phpp-ventilator-id-lookup/`](../../archive/phpp-ventilator-id-lookup/README.md),
already complete. See `STATUS.md` for one loose end that packet may not have
covered.
