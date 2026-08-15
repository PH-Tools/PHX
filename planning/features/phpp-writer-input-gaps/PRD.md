# PRD — PHPP writer input gaps

**Status:** Requested (2026-08-15)

## Problem

PHX's PHPP write sequence overwrites what it writes and nothing else. That is
correct behaviour for a workbook a human has been curating. It is a trap for a
workbook produced from PHI's blank template, which is what a user starting a new
project actually does: every input PHX skips silently keeps the template's own
default.

Five such inputs are listed below. Each is present in the PHX model — this is
not a data-availability problem, it is a missing writer. Three produce no PHPP
error of any kind; the model computes, the workbook computes, and the two
describe different buildings.

## Why this matters more than the count suggests

These were found one at a time, over one session, by rebuilding a reference
workbook and chasing wrong numbers. Three of the five were found *after* the
first was fixed, each revealed only once the larger error above it was gone.
That is the signature of a class of defect rather than a list, and it is the
argument for a systematic check rather than five patches.

A PHX user has no way to notice any of them. PHPP does not flag three of them,
and the two it does flag are reported on the `Check` worksheet, which nothing in
the export path reads.

## The five gaps

### 1. Number of dwelling units → `Verification!F29`

**Model source:** the building's dwelling count (`PhxBuilding` /
`PhxPhBuildingData`).

**PHPP behaviour without it:** `F29` is a literal input with no template
default. `Verification!F30` derives the occupant count from it by the PHI
standard formula, `IHG!D6` reads `F30`, and the whole internal-heat-gain chain
resolves to `#VALUE!`. `Cooling!row_148` and the heating equivalent read
**0.000 kWh**.

**Measured:** 1909.680 kWh of internal gains missing from an 80 m² single-family
reference model — about 40 % of its total cooling-season gains.

**Flagged by PHPP:** yes, `Verification!B29` shows `!` and the `Check` worksheet
counts it.

### 2. Summer heat-recovery mode → `SummVent!R15:R18`

**Model source:**
`PhxPhBuildingData.summer_ventilation.summer_bypass_mode`
(`PhxSummerBypassMode`), which arrives from honeybee-ph's
`PhVentilationSummerBypassMode` on the building segment. Genuinely
user-selectable and it does vary — of four reference models on hand, three carry
`ALWAYS` and one carries `TEMP_CONTROLLED`.

**PHPP behaviour without it:** PHPP spells this as one `x` among `R15:R18`, and
a blank template ships with `R15` already ticked. The option labels are the trap:
they name what the *heat recovery* does, not what the bypass damper does.
`Cooling!T124` resolves them —

```
Cooling!O35 = IF(SummVent!R15="x","x","")          ' and O36:O38 likewise for R16:R18
Cooling!T124 = IF($O$35="x",FALSE,IF($O$36="x",T121<T116,IF($O$37="x",T123<T120,TRUE)))
Cooling!T125 = IF(T124,$D$34,$D$35)+$D$39
```

— so `R15` ("None") means **no summer heat recovery at all**, and `R18`
("Always") means it is never bypassed. `T125` then takes the exterior
ventilation conductance with recovery (`D34`) or without (`D35`).

**Measured:** 26.400 W/K against 9.213 W/K — a factor of 2.2 on the largest
cooling-season loss term, from a default nobody chose.

**Flagged by PHPP:** no. Silent.

**Mapping:** `NONE→R15`, `TEMP_CONTROLLED→R16`, `ENTHALPY_CONTROLLED→R17`,
`ALWAYS→R18`. Write one `x` and clear the other three — PHPP does not flag two
ticked boxes, it resolves to whichever its formula tests first.

### 3. Wind-protection class → `Ventilation!K19`

**Model source:** `PhxPhBuildingData.building_exposure_type`
(`WindExposureType`), and its derived `wind_coefficient_e`.

**PHPP behaviour without it:** PHPP reads the *class*, never the coefficient:

```
Ventilation!M19 = IF(K19="",Z18,INDEX(Z18:Z20,LEFT(K19,1)))
Ventilation!N19 = M19*2.5
```

`Z18:Z20` = `0.1` / `0.07` / `0.04`, labelled in `AA18:AA20` as
`1-No protection` / `2-Moderate protection` / `3-High protection`. A blank
template ships `K19` at `2-Moderate protection`.

**This one is not a plain omission.** PHX *does* write the coefficient — into
`Ventilation!J19`, which nothing reads. So the intended value is visible in the
workbook, one cell to the left of the one that decides, and the export looks
correct to anyone checking it.

**Measured:** infiltration computed at e = 0.070 against an authored 0.100 —
exactly 7/10. On a building with no window or extract summer ventilation to
dilute it, that ratio appeared undiluted in `Cooling!T128` at +42.86 %.

**Flagged by PHPP:** no. Silent.

**Mapping:** key by the coefficient, not the enum. `WindExposureType` has seven
members and `wind_coefficient_e` collapses them onto three values (the
`ONE_SIDE_EXPOSED_*` members fall through to 0.1); PHPP has exactly three
classes, one per coefficient. Keying by the coefficient keeps
`wind_coefficient_e` as the single source of truth rather than restating its
fall-through. An unrecognised coefficient should fail loudly — PHPP cannot
express it.

### 4. Ground / floor-slab type → `Ground` worksheet

**Model source:** `PhxVariant`'s foundations
(`PhxHeatedBasement` / `PhxSlabOnGrade` / `PhxUnHeatedBasement` /
`PhxVentedCrawlspace`), with their geometry.

**PHPP behaviour without it:** the write sequence has **no `Ground` writer at
all**. `C24`/`C30`/`C33`/`C40` are the four mutually exclusive floor-slab
selectors; a blank template has none of them ticked, so the sheet computes
nothing. `H18` (area) and `P18` (U-value) are formulas reading `Areas` and
follow the building already, but every literal below them — exposed perimeter
`H19`, below-grade wall area and U-value `H31`/`P31`, and the type-specific
blocks — stays empty.

Worse on a *populated* starting workbook, where the example's "Unheated
basement" with a 59.75 m² below-grade wall and 120 m³ basement volume survives
and computes ground heat loss for a different building.

**Flagged by PHPP:** yes, on the `Check` worksheet.

**Note:** this is the largest of the five and probably deserves its own packet.
See `phpp-ground` in the `phi-rules` corpus for the full cell map before
starting.

### 5. User-defined climate block name → `Climate!D67`

**Model source:** the climate dataset's display name.

**PHPP behaviour without it:** PHX writes the climate *values* into PHPP's
user-defined block but not the block's *name*. The active-climate selector has
to name the dataset it selects, so the two must agree; unnamed, the selector has
nothing to point at and the workbook silently computes with whatever built-in
dataset was already selected.

**Measured elsewhere:** a reference model computed a full year on New York
weather while carrying a synthetic climate, with nothing erroring.

**Flagged by PHPP:** no. Silent.

## Acceptance criteria

1. Each of the five is written from the PHX model by the canonical write
   sequence — no hardcoded constants, no per-project scripting.
2. Radio-style selections (`SummVent!R15:R18`, `Ground!C24/C30/C33/C40`) write
   one `x` and clear the siblings.
3. Where PHPP cannot express a model value (an exposure coefficient outside
   `{0.1, 0.07, 0.04}`, an unsupported foundation type), the writer fails loudly
   rather than picking a nearest option.
4. `Ventilation!J19` keeps whatever it does today; `K19` is what must change.
5. A round-trip test per gap: write into a **blank** PHPP template, read back,
   assert the model's value — not the template's default. Blank, not the example
   workbook; a populated starting workbook can mask an omission by already
   holding a plausible value.

## Non-goals

- Reading these back out of PHPP (import path).
- The `Check` worksheet integration. Reporting PHPP's own error count after a
  write would be a good separate feature, and would have caught two of these
  five, but it is not this packet.
