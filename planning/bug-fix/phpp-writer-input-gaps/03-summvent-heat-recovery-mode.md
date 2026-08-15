# Summer heat-recovery mode is never written to `SummVent`

**Status:** Scoped — one mapping question must be settled before Phase 2
**Opened:** 2026-08-15
**Owner:** `PHX/PHPP/` — no owner today; `SUMM_VENT` is an unused stub
**Umbrella:** [`README.md`](README.md)
**Filed as:** "Summer heat-recovery mode → `SummVent!R15:R18`" (gap 2 of the incoming request)

## Confirmed as filed

There is no `SummVent` writer of any kind. The shape entry is a stub in all
seven localization files:

```json
"SUMM_VENT": { "name": "SummVent", "columns": {} }
```

backed by `class ColSummVent(BaseModel): ...` in `shape_model.py`. Nothing in
`phpp_app.py` or `sheet_io/` references it. The golden fixture writes nothing to
the sheet.

## What the blank 10.6 template contains

```
Q14 = 'HRV/ERV in summer (check only one field)'
Q15 = 'None'                                                    R15 = 'x'   <- template default
Q16 = 'Automatic bypass, controlled by temperature difference'  R16 = (empty)
Q17 = 'Automatic bypass, controlled by enthalpy difference'     R17 = (empty)
Q18 = 'Always'                                                  R18 = (empty)
```

`R15:R18` carry `PHPP_Daten_Ankreuzen` validation (`["", "x"]`). The blank
template ships `R15` ticked, so an export that writes nothing leaves the model
running with **no summer heat recovery at all**.

`Cooling` resolves the group (formulas from the `phi-rules` corpus,
`phpp-summvent/rules.md`):

```
Cooling!O35 = IF(SummVent!R15="x","x","")
Cooling!O36 = IF(SummVent!R16="x","x",IF(AND(SummVent!R17="x",NOT(ISNUMBER(Climate!$E$32))),"x",""))
Cooling!O37 = IF(AND(SummVent!R17="x",ISNUMBER(Climate!$E$32)),"x","")
Cooling!T124 = IF($O$35="x",FALSE,IF($O$36="x",T121<T116,IF($O$37="x",T123<T120,TRUE)))
Cooling!T125 = IF(T124,$D$34,$D$35)+$D$39
```

`T125` takes the exterior ventilation conductance **with** recovery (`D34`) or
**without** (`D35`). Measured in the source investigation: 26.400 W/K against
9.213 W/K — a factor of 2.2 on the largest cooling-season loss term, from a
default nobody chose.

Note the request's simplification of `O36` omits the `R17`/`Climate!E32` branch.
It does not change the mapping, but the writer's test should not assert against
the simplified form.

## The mapping — and the trap

`PhxSummerBypassMode` (`model/enums/hvac.py:306`) is
`NONE=1, TEMP_CONTROLLED=2, ENTHALPY_CONTROLLED=3, ALWAYS=4`. The proposed
mapping is ordinal:

| PHX | value | PHPP |
|---|---|---|
| `NONE` | 1 | `R15` |
| `TEMP_CONTROLLED` | 2 | `R16` |
| `ENTHALPY_CONTROLLED` | 3 | `R17` |
| `ALWAYS` | 4 | `R18` |

**This is not obviously right, because PHX's names describe the opposite
thing.** The class is called `PhxSummerBypassMode` and its docstring reads
`ALWAYS: Bypass always active in summer` — i.e. the damper. PHPP's `Q14` group
describes the **heat recovery**: `R15` "None" means no summer recovery, `R18`
"Always" means recovery is never bypassed. Read naively, a damper that is
"always open" is a recovery that is "none", and the ordinal mapping would be
inverted.

The evidence says the ordinal mapping is correct and the PHX **naming** is what
is wrong. The same attribute is serialized as:

- `to_WUFI_XML/xml_schemas.py:376` → `XML_Node("SummerHRVHumidityRecovery", …)`
- `to_METr_JSON/metr_schemas.py:1399` → `"sumHRec": …`

Both field names describe summer heat *recovery*, matching PHPP's group
semantics, and both carry the raw enum value. WUFI-Passive's data model mirrors
PHPP's, so ordinal position transfers directly. The source investigation's
measurement agrees: a reference model carrying `ALWAYS` produced the
*with-recovery* conductance (`D34` = 9.213 W/K).

That is two independent lines of evidence, but neither is a direct observation
of the WUFI UI. **Phase 1 exists to settle it before any cell is written.**

## Phases

### Phase 1 — settle the mapping (blocking)

Do not write code first. Take one WUFI-Passive model with a known, non-default
summer setting, export its XML, and read `SummerHRVHumidityRecovery`. Confirm
that the integer matches the position of the option selected in the WUFI UI and
that the UI's option labels read as heat-recovery modes, not damper modes.
`tests/test_from_WUFI/` fixtures may already contain a usable model — check
there before building one.

**Verify:** the four WUFI option labels are recorded verbatim in this file next
to the PHPP labels, and the ordinal correspondence is stated as observed, not
inferred. If it turns out inverted, the mapping table above is wrong and Phase 3
changes accordingly — everything else in this packet stands.

### Phase 2 — a shared radio-group write helper

`SummVent!R15:R18` and `Ground!C24/C30/C33/C40` (packet [05](05-ground-worksheet-writer.md))
are the same shape of problem: a set of mutually exclusive `x` cells where
exactly one must be set and the siblings cleared. PHPP does not flag two ticked
boxes — it resolves to whichever its formula tests first — so clearing siblings
is mandatory, not hygiene.

Add one helper (suggested: `PHX/PHPP/phpp_model/xl_checkbox_group.py`) that
takes a sheet name, an ordered list of cell addresses and the index to select,
and returns the `XlItem` list: `"x"` at the chosen index, `""` at every other.
Never `None` — `PHPP_Daten_Ankreuzen` is `["", "x"]` and `None` is not a member
of the validation list.

**Verify:** unit tests for select-first, select-last, and select-middle, each
asserting all four addresses appear in the output.

### Phase 3 — shape and writer

- Replace `ColSummVent` with a real model: a `hrv_summer_mode` entry holding
  `locator_col: "Q"`, `locator_string: "HRV/ERV in summer"`, an
  `input_column: "R"`, and the four row offsets (`+1`…`+4` from the located
  header row). Locate by header string, not a hardcoded row — consistent with
  every other `sheet_io` module and resilient to row drift between 10.x
  releases.
- New `PHX/PHPP/sheet_io/io_summ_vent.py` following the `io_ventilation.py`
  pattern: a `*InputLocation` for the header, a `write_summer_hrv_mode` method.
- New `PHX/PHPP/phpp_model/summ_vent_data.py` mapping
  `PhxSummerBypassMode` → offset via the shape, raising on an unmapped member.
- `PHPPConnection.__init__`: instantiate the new controller.
- `phpp_app.write_project_summer_ventilation` (new), reading
  `variant.phius_cert.ph_building_data.summer_ventilation.summer_bypass_mode`,
  guarded by `if self.easyPh: return` and the standard `ph_building_data` check.
- `hbjson_to_phpp.write_phx_project_to_phpp`: add the call. Place it next to
  `write_project_ventilation_type` — order is not load-bearing here (no locator
  depends on prior writes), but grouping the ventilation writes keeps the
  sequence readable.

**Verify:** new `tests/test_PHPP/test_sheet_io/test_io_summ_vent.py` asserts, for
each of the four enum members, one `"x"` and three `""`.

### Phase 4 — correct the misleading docstring

Do **not** rename `PhxSummerBypassMode` — it is public API and is round-tripped
through WUFI XML and METr JSON. Instead correct the class docstring to say what
the field actually controls (summer heat recovery, per its WUFI/METr field
names) and note the PHPP `R15:R18` correspondence, including that PHPP's labels
describe the recovery rather than the damper. This is the single cheapest thing
in the packet that prevents the next inversion bug.

**Verify:** docstring names both the WUFI field and the PHPP cells.

### Phase 5 — re-record the replay fixture

Live Excel required. Expected diff: a new `SummVent` sheet in `golden_writes`
with exactly four cells. `Single_Zone.hbjson` should produce `R18: 'x'` and
`R15/R16/R17: ''` if it carries the `ALWAYS` default — confirm against the
fixture's actual value rather than assuming.

**Verify:** `python -m pytest tests/test_xl_replay/` green; `SummVent` is the
only new sheet.

### Phase 6 — closeout

`python -m pytest tests/`. Record the Phase 1 observation in the `phi-rules`
corpus (`phpp-summvent/rules.md` already carries the inverted-label correction;
add the WUFI-side field names so the next reader can check the mapping without
re-deriving it). Update [`README.md`](README.md) and `planning/STATUS.md`.

## Related

- `phi-rules` → `rulesets/phpp-10-r1/calculators/phpp-summvent/rules.md`
- [`05`](05-ground-worksheet-writer.md) — reuses the Phase 2 helper
