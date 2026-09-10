# PHPP writer zeroes the U-Values surface resistances

DATE: 2026-09-10
STATUS: Complete
AUTHOR: Claude (with Ed May)
ISSUE: https://github.com/PH-Tools/PHX/issues/118

Router for the fix. Read this file, then `PLAN.md`.

- **Defect + evidence + root cause + what was ruled out** — this file.
- **Phase-by-phase implementation sequence** — [`PLAN.md`](PLAN.md).
- **Current state / next step** — [`STATUS.md`](STATUS.md).

---

## 1. Defect

`ConstructorBlock.create_xl_items` (`PHX/PHPP/phpp_model/uvalues_constructor.py`)
writes `0.0` into both surface-resistance cells of every assembly block, and
`UValues.activate_variants` (`PHX/PHPP/sheet_io/io_u_values.py`) re-zeroes them
when the Variants links are made. Every assembly PHX writes to a PHPP therefore
publishes a **film-free** U-value: `U = 1 / sum(R_layers)`, with no `Rsi` and no
`Rse`.

That is not what a hand-built PHPP contains, and it is not what the WUFI/METr
targets produce for the same PHX model. WUFI applies films per component
exposure, so the same assembly resolves to the correct U there and to a high U
in PHPP.

Worked example, the declared-U case from #116/#117 (`U = 0.150 W/m2K`,
`Rsi 0.13`, `Rse 0.04`, so the stripped layer carries `R = 6.4967 m2K/W`):

| Target | Resolves to |
|---|---|
| WUFI / METr | `1/(6.4967 + Rsi + Rse)`, applied by the tool = **0.150** |
| PHPP today | `R25` = `1/6.4967` = **0.1539** (+2.6%) |

The error grows as the assembly gets worse. A `R = 1.0 m2K/W` assembly publishes
`1.000` instead of `0.855`: **+17%**.

Secondary defect, same two writers: the `r_si` field is written at
`rse_row_offset` and `r_se` at `rsi_row_offset`. Both are `0.0` in column `M`
today, so nothing is numerically wrong, but the write path contradicts the read
path (`get_constructor_r_si_type` / `get_constructor_r_se_type` use the offsets
the other way round, and they are right).

## 2. Evidence — what PHPP actually does with those two cells

Read from the archived blank workbook
(`plans/…/test_files/PHPP_EN_V10.6_Empty.xlsx`, gitignored) and cross-checked
against the `phi-rules` teardown `phpp-10-r1/calculators/phpp-u-values/rules.md`
and manual chapter `[[P15]]` §15.1.1.

For block `01ud`, `M10` is the **orientation** selector and `M11` the
**adjacency** selector:

```
M24 = IF(M10="","",IF(ISNUMBER(M10),M10,
        IF(VALUE(LEFT(M10,1))=1, INDEX(Data!$B$412:$B$414, 2-Climate!$AM$28),
        IF(VALUE(LEFT(M10,1))=3, INDEX(Data!$B$412:$B$414, 2+Climate!$AN$28),
                                 Data!$B$413))))                       <- Rsi
M25 = IF(M11="","",IF(ISNUMBER(M11),M11,
        IF(LEFT(M11,1)="3", M24,
           INDEX(Data!$D$412:$D$413, VALUE(LEFT(M11,1)), 0))))         <- Rse
AJ25 = $M24 + SUM(AJ13:AJ20) + $M25
R25  = IF(AND(ISNUMBER($M25),ISNUMBER($M24)), … 1/Y25 … + R11, "")     <- published U
```

Validation lists (`Data!$A$411:$A$414` / `Data!$C$411:$C$414`, exposed as the
defined names `PHPP_Daten_Ausrichtung_Bauteil` and `PHPP_Daten_Angrenzend_an`)
are blank plus:

| Orientation (`M10`) | Rsi | Adjacency (`M11`) | Rse |
|---|---|---|---|
| `1-Roof` | 0.10 | `1-Outdoor air` | 0.04 |
| `2-Wall` | 0.13 | `2-Ground` | 0.00 |
| `3-Floor` | 0.17 | `3-Ventilated` | `= Rsi` |

Three properties of those formulas decide the fix:

1. **Only the leading digit is read.** `VALUE(LEFT(M10,1))` / `LEFT(M11,1)`. The
   label text after the digit is cosmetic to the calculation, which makes a
   written selector string robust against label drift between PHPP editions.
2. **Rsi is climate-dependent.** `Climate!$AM$28` / `$AN$28` shift the roof and
   floor lookups by the heating/cooling-dominance of the selected climate. A
   hardcoded `0.10` / `0.17` would be wrong in some climates.
3. **`3-Ventilated` sets `Rse = Rsi`**, so it too depends on the orientation
   already selected. It cannot be expressed as a constant.

`Components!K13` reads `'U-values'!R25` straight through, and `Areas` selects
from `Components`, so `R25` is the number the whole energy balance uses.

## 3. Root cause

The PHX model has no surface-film concept (verified: no surface-resistance field
anywhere in `PHX/model/`), which is correct for WUFI/METr — the tool applies
films per component exposure. The PHPP write path inherited that assumption and
wrote `0.0` rather than telling PHPP which films to apply. PHPP has no component
exposure of its own to fall back on: the selection is per **assembly block**.

The information PHPP needs is already in the PHX model, one level away from the
assembly: `PhxComponentOpaque.face_type` and `PhxComponentOpaque.exposure_exterior`.
`areas_surface.SurfaceRow.phpp_group_number_int` already maps exactly that pair
onto a PHPP concept (the Areas group number). The same pair maps onto the two
selectors.

So this is **a PHPP-write-path change only**. No PHX model change, no WUFI/METr
change, no source (honeybee-ph / PH-Navigator) change.

## 4. Ruled out

| Alternative | Why not |
|---|---|
| **Write numeric resistances** (`0.13` / `0.04` …). PHPP accepts a number and uses it verbatim ([[P15]] §15.1.1). | Loses the climate dependence in `M24` and the `Rse = Rsi` behaviour of `3-Ventilated` (evidence §2, items 2-3). It is also a user-defined override of a PHI standard value, which [[3.2.1.a]] puts under Certifier consultation, and it would need SI→IP unit conversion in the two IP shape files. A hand-built PHPP contains a selector, not a number. |
| **Add `r_si` / `r_se` fields to `PhxConstructionOpaque`.** | Puts a PHPP-only, exposure-derived concept on a target-agnostic model class that WUFI/METr would have to ignore, and it has no single correct value when one assembly is used at two exposures. The write path can derive it at write time from data the model already carries. |
| **Stop stripping films upstream** (issue #118 direction 2: hand PHX a PHPP-shaped R). | Breaks the WUFI/METr number, which is currently correct, and would require every producer to know which target the model is bound for. |
| **Split an assembly used at two exposures into two PHPP blocks.** | Correct in principle (that is what a modeller does by hand) but it changes assembly identity, the `Areas` assembly-ID references and the Variants layer list. Out of proportion to the defect. This packet picks the dominant exposure by area and warns; the split stays available as a follow-up. |

## 5. Correction

1. Write the PHPP **selector string** into both cells, chosen from the
   assembly's use in the model:
   - `M10` (Rsi) from `ComponentFaceType`: `WALL → "2-Wall"`,
     `ROOF_CEILING → "1-Roof"`, `FLOOR → "3-Floor"`.
   - `M11` (Rse) from `ComponentExposureExterior`: `EXTERIOR → "1-Outdoor air"`,
     `GROUND → "2-Ground"`, `SURFACE` or an attached-zone number →
     `"3-Ventilated"`.
   The strings live in the shape JSON so they stay localizable, like every other
   PHPP label PHX already carries (`locator_string_header`, …).
2. Resolve each assembly's `(face_type, exposure_exterior)` from the opaque
   components that reference it, weighted by area. Mixed use warns through
   `xl.output`; an assembly no component uses falls back to `2-Wall` /
   `1-Outdoor air`.
3. Fix the `r_si`/`r_se` row-offset cross-wiring in both writers.
4. `activate_variants` re-writes the resolved selectors instead of zeroing them.

## 6. Verification

- `python -m pytest tests/` — full suite.
- The `tests/test_xl_replay/` golden state changes in exactly six cells
  (`U-values!M10/M11`, `M31/M32`, `M52/M53`) for the `Single_Zone` fixture:
  `Generic Exterior Wall → 2-Wall / 1-Outdoor air`,
  `Generic Ground Slab → 3-Floor / 2-Ground`,
  `Generic Roof → 1-Roof / 1-Outdoor air`. Nothing else in the export reads
  those cells back, so no other golden write moves.
- New unit tests for the enum→selector mapping, the row offsets, the
  area-weighted resolver, and the mixed-use warning.
- Hand check: a declared-U assembly written through the new path must publish
  `R25 = 0.150`, not `0.1539`.
