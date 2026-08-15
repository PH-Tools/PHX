# Wind protection is written to two cells PHPP never reads

**Status:** Scoped — ready to implement
**Opened:** 2026-08-15
**Owner:** `PHX/PHPP/phpp_app.py` → `write_project_airtightness`; `PHX/PHPP/phpp_localization/*.json` → `VENTILATION`
**Umbrella:** [`README.md`](README.md)
**Filed as:** "Wind-protection class → `Ventilation!K19`" (gap 3 of the incoming request)

## What the blank 10.6 template actually contains

```
I19 = 'Wind protection coefficient, e'   K19 = '2-Moderate protection'
M19 = '=IF(K19="",Z18,INDEX(Z18:Z20,LEFT(K19,1)))'    N19 = '=M19*2.5'
I20 = 'Wind protection coefficient, f'   M20 = 15      N20 = '=M20'
Z18:Z20 = 0.1 / 0.07 / 0.04
Data!K331:K333 = '1-No protection' / '2-Moderate protection' / '3-High protection'
```

`M19` decodes the **leading digit of the `K19` drop-down**. `J19` holds nothing
and is read by nothing. `M20` is a plain literal input; `J20` is likewise read
by nothing.

## What PHX writes

```json
"wind_coeff_e": { "locator_col": "I", "locator_string": "Wind protection coefficient, e", "input_column": "J" },
"wind_coeff_f": { "locator_col": "I", "locator_string": "Wind protection coefficient, f", "input_column": "J" }
```

Golden fixture, `Ventilation` sheet — the complete set of writes:

```
{K12: '1-Balanced PH ventilation with HR', K15: 'x', J19: 0.1, J20: 15.0, M23: 1.0, M22: 0.0}
```

Both coefficients land in column `J`. `K19` keeps the template's
`2-Moderate protection` (e = 0.07) and `M20` keeps 15, whatever the model said.
`K12`, `K15`, `M22`, `M23` are all correct and must not change.

## Two defects, not one

**(a) `e` — the filed defect.** The class is never written; PHPP computes
infiltration at 0.07 regardless of exposure. The intended value is visible one
cell to the left, which is why the workbook survives inspection. Measured
downstream in the source investigation: `Cooling!T128` off by +42.86 % on a
building with no window or extract summer ventilation to dilute it — exactly the
0.07 / 0.10 ratio.

**(b) `f` — not filed, same root cause.** `PhxPhBuildingData.wind_coefficient_f`
is a settable float (`model/certification.py:149`) defaulting to `15`. PHPP's
`M20` also defaults to `15`. The two coincide, so nobody has seen this fail —
but any model with a non-default `f` silently keeps 15.

## Mapping: key by the coefficient

`wind_coefficient_e` is a derived read-only property
(`model/certification.py:201-212`) that collapses seven `WindExposureType`
members onto three values, with `case _: return 0.1` catching the
`ONE_SIDE_EXPOSED_*` and `USER_DEFINED` members. PHPP 10 offers exactly three
classes, one per coefficient, so the mapping is 1:1 and lossless:

| `wind_coefficient_e` | `K19` literal |
|---|---|
| `0.1` | `1-No protection` |
| `0.07` | `2-Moderate protection` |
| `0.04` | `3-High protection` |

Keying by the coefficient rather than the enum keeps `wind_coefficient_e` as the
single source of truth instead of restating its fall-through. One consequence
worth stating plainly: **the "fail loudly on an unrecognised coefficient"
acceptance criterion is unreachable today** — the property can only ever return
one of those three floats. Keep the guard as a structural invariant, but do not
claim it as behaviour under test.

(PHPP 9 split "one side exposed" from "several sides exposed" with separate
coefficient tables; PHPP 10 does not. The 9.x shapes must be checked separately
before this change is applied to them — see Phase 4.)

## Phases

### Phase 0 — failing test

`tests/test_PHPP/test_sheet_io/test_io_ventilation_wind.py` (new), against the
fake XL framework:

- parametrize the three `WindExposureType` members that produce distinct
  coefficients; assert `K19` receives the matching literal — **fails today**
- assert a non-default `wind_coefficient_f` reaches `M20` — **fails today**
- assert `K12`, `K15`, `M22`, `M23` are unchanged

**Verify:** all new assertions fail; the four unchanged-cell assertions pass.

### Phase 1 — shape: add `wind_protection_class`, fix `wind_coeff_f`

In all seven localization JSONs and `shape_model.Ventilation`:

- add `wind_protection_class`: `locator_col: "I"`,
  `locator_string: "Wind protection coefficient, e"`, `input_column: "K"`,
  plus an `options` dict keyed by the coefficient as a string
  (`"0.1"`, `"0.07"`, `"0.04"`) — mirroring how `Verification` carries its
  option literals, so the strings stay per-localization data rather than Python
  constants
- change `wind_coeff_f.input_column` from `"J"` to `"M"`
- leave `wind_coeff_e` alone (see Phase 3)

`shape_model.VentilationInputItem` already has an optional `unit`; it needs an
optional `options: dict | None = None` to match `VerificationInputItem`.

**Verify:** `tests/test_PHPP/test_shape_file.py` passes for all seven files.

### Phase 2 — writer

`ventilation_data.VentilationInputItem`: add a `wind_protection_class`
classmethod that resolves the coefficient through the shape's `options`, raising
on a miss rather than falling back. `io_ventilation.Ventilation`: add the
`VentilationInputLocation` and a `write_wind_protection_class` method, following
the existing constructor/`_write_input` pattern exactly.

`phpp_app.write_project_airtightness`: add the class write and drop the stale
`# TODO: Get the actual values from the Model somehow` comment above it — the
values do come from the model.

**Verify:** Phase 0 passes.

### Phase 3 — decide the fate of `J19`

The incoming request's acceptance criterion 4 says `J19` keeps whatever it does
today. Recommend honouring that: `J19` is a visible yellow input cell, the value
is correct and human-meaningful, and removing it is a behaviour change with no
upside. Add a one-line comment at the write site recording that `J19` is
decorative and `K19` is load-bearing, so the next reader does not "fix" it back.

`J20` is different — it is now wrong *and* redundant, because `M20` carries the
same number. Recommend dropping the `J20` write with the `input_column` change
rather than writing `f` to both.

**Verify:** golden diff in Phase 5 shows `J19` retained, `J20` gone, `K19` and
`M20` added.

### Phase 4 — check the 9.x shapes before shipping

`EN_9_6A` and `EN_9_7IP` are in scope for the shape change and PHPP 9's wind
protection UI is **not** the same as PHPP 10's. Open a 9.x workbook, read the
row that `"Wind protection coefficient, e"` locates, and confirm whether a class
drop-down exists and what its literals are. If it does not, gate the new writer
on the shape entry being present rather than guessing a mapping.

**Verify:** either the 9.x shapes get correct `options`, or they get no
`wind_protection_class` entry and the writer skips cleanly.

### Phase 5 — re-record the replay fixture

Live Excel required. Expected `Ventilation` diff: `K19` added
(`1-No protection`, since `Single_Zone` uses the default
`SEVERAL_SIDES_EXPOSED_NO_SCREENING` → e = 0.1), `M20` added (`15.0`), `J20`
removed, `J19` unchanged at `0.1`.

**Verify:** `python -m pytest tests/test_xl_replay/` green; the diff is exactly
those four changes.

### Phase 6 — closeout

`python -m pytest tests/`. Fold the `M20`/`J20` finding back into the
`phi-rules` corpus — `rulesets/phpp-10-r1/calculators/phpp-ventilation/rules.md`
documents the `K19`/`J19` trap but not the `f` half, and the corpus feedback
loop is mandatory. Update [`README.md`](README.md) and `planning/STATUS.md`.

## Related

- `phi-rules` → `rulesets/phpp-10-r1/calculators/phpp-ventilation/rules.md`
- [`01`](01-verification-version-guard.md) — the other "written, but nowhere useful" case
