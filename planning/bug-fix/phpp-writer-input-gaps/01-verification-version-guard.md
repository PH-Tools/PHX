# A PHPP version mismatch silently drops the entire `Verification` worksheet

**Status:** Scoped — ready to implement
**Opened:** 2026-08-15
**Owner:** `PHX/PHPP/phpp_app.py` → `write_certification_config`
**Umbrella:** [`README.md`](README.md)
**Filed as:** "Number of dwelling units → `Verification!F29`" (gap 1 of the incoming request)

## The re-diagnosis

The request says `Verification!F29` has no writer. It has one —
`phpp_app.py:268-274`, `input_type="num_of_units"`, which the shape resolves to
column `F` on the row whose column `E` reads `"No. of dwelling units:"`. In the
blank 10.6 template that is `E29`, so the target is `F29`, exactly as filed.

It never runs. Eighty lines earlier:

```python
# phpp_app.py:184-196
for phx_variant in phx_project.variants:
    if not self.phpp_version_equals_phx_phi_cert_version(phx_variant):
        self.xl.output(msg)
        return          # <-- not `continue`, and before every write
```

`PhxPhiCertification.version` defaults to **9** (`model/certification.py:387`),
and honeybee-ph sets it from the building segment's `phi_certification`
attributes (`from_HBJSON/create_variant.py:265-270`). The replay fixture's
`Single_Zone.hbjson` carries `phpp_version: 9`; the template is 10.6. Guard
fires, `return` exits the method for **all** variants, and nothing on the
worksheet is written.

Confirmed by the golden fixture: `Verification` is in `sheet_names` and absent
from `golden_writes`.

## What is actually lost

Twelve writes, not one:

| Write | Kind | Shape key |
|---|---|---|
| Building category / use / IHG / occupancy type | enum | `phi_building_category_type`, `phi_building_use_type`, `phi_building_ihg_type`, `phi_building_occupancy_type` |
| Certification type / class / PE type / EnerPHit type / retrofit type | enum | `phi_certification_type`, `phi_certification_class`, `phi_pe_type`, `phi_enerphit_type`, `phi_retrofit_type` |
| **No. of dwelling units** | item | `num_of_units` |
| **Winter setpoint** | item | `setpoint_winter` |
| **Summer setpoint** | item | `setpoint_summer` |

## Why the guard exists (do not just delete it)

`VerificationInput.enum` (`phpp_model/verification_data.py:36-40`) is a raw dict
lookup keyed by the PHX enum's value:

```python
shape_data = getattr(shape, input_type).options
return cls(shape, input_type, shape_data[str(input_enum_value.value)])
```

PHX keeps two enum modules, `enums/phi_certification_phpp_9.py` and
`…_phpp_10.py`, and the values genuinely differ:

| Enum | v9 values | v10 shape option keys |
|---|---|---|
| `PhiCertType` | `1, 2, 3, 4` | `10, 21, 22, 30, 40` |
| `PhiCertClass` | `1, 2, 3` | `10, 11, 20, 30` |

A v9-authored model against a v10 workbook therefore hits `shape_data["1"]` →
**`KeyError`**. The guard is preventing a hard crash. The fix must preserve that
protection for the nine enum writes and lift it from the three that do not
consult `options` at all.

Verified safe: all seven localization files (`EN_9_6A`, `EN_9_7IP`, `EN_10_3`,
`EN_10_4A`, `EN_10_4IP`, `EN_10_6`, `EN_10_6IP`) carry `num_of_units`,
`setpoint_winter`, `setpoint_summer` and `mechanical_cooling`, none of which has
an `options` dict, and the same nine keys that do.

## Downstream cost of the missing `F29` — verified in the blank 10.6

```
Verification!AD30 = IF(F29>0,(1+1.9*(1-EXP(-0.00013*(I35/F29-7)^2))+0.001*I35/F29)*F29,"")
Verification!F30  = IF(ISNUMBER(R30),R30,IF(AD21=1,AD30,""))
IHG!D6            = Verification!F30
```

With `F29` blank, `AD30` → `""`, `F30` → `""`, and the internal-heat-gain chain
inherits a text empty string. PHPP does flag it:

```
Verification!W29 = IF(AND(AD21=1,OR(F29=0,F29="")),Data!$A$672,"")   ' "Data missing"
Verification!B29 = IF(W29="","",Data!$A$671)                        ' "!"
```

Nothing in the export path reads `B29` or the `Check` worksheet, so the flag
never reaches the user.

## Two more defects found in the same method

Both are real, both are cheap, both belong here rather than in a separate item.

**(a) `PhiCertType.OTHER` cannot be written even when versions match.**
`enums/phi_certification_phpp_10.py` defines `OTHER = 44`; the v10 shape's
`phi_certification_type.options` keys are `{"10","21","22","30","40"}`. A v10
model set to `OTHER` raises `KeyError: '44'`. Either the enum value or the shape
key is wrong — the workbook's dropdown is the tiebreaker and must be checked
before changing either.

**(b) `set_phx_phpp10_settings` leaves three attributes on v9 enums.**
`from_HBJSON/create_variant.py:219-244` sets six of the nine;
`phi_building_category_type`, `phi_building_occupancy_type` and
`phi_enerphit_type` keep their dataclass defaults, which are
`phi_certification_phpp_9.*` members. This works today only because the v10
shape's option dicts happen to accept the v9 keys (`{1,2,11,12}`, `{1,2}`,
`{1,2,3}`). That is load-bearing coincidence and should be written down.

Noted, not fixed here: `mechanical_cooling` exists in every shape file and is
written by nothing; `phi_building_occupancy_type`'s v10 options map both keys to
`null`, so the write clears `R30` regardless of whether the model asked for a
custom occupancy.

## Phases

### Phase 0 — lock the behaviour in a failing test

`tests/test_PHPP/test_phpp_app_verification.py` (new). Using the fake XL
framework from `tests/test_xl_replay/fake_xl_framework.py` and a
`PhxProject` whose `phi_cert.version = 9`, against a 10.6 shape:

- assert `Verification!F29`, `K28`, `N28` are written — **fails today**
- assert none of the nine enum cells are written (the guard still holds)
- a second case with `version = 10` asserts all twelve are written

**Verify:** the first case fails for the right reason (no write at all, not a
`KeyError`).

### Phase 1 — narrow the guard

Restructure `write_certification_config` so the version check gates only the
enum block:

- keep `phpp_version_equals_phx_phi_cert_version` as-is
- when it returns `False`: emit the existing warning **once** (not per variant),
  skip the nine enum writes, continue to the three item writes
- when it returns `True`: unchanged behaviour
- replace the bare `return` with `continue` so a mismatch on one variant cannot
  suppress a later one

Keep the `if not phx_variant.phius_cert.ph_building_data: continue` guard where
it is.

**Verify:** Phase 0 passes; `python -m pytest tests/` green except the replay
invariant (expected — see Phase 4).

### Phase 2 — resolve the `OTHER = 44` mismatch

Read the `Verification` "Planned energy standard" dropdown in the blank 10.6
(`T` column, validation list) and take the workbook's literal as authority. Fix
whichever side is wrong — the enum value in
`enums/phi_certification_phpp_10.py` or the `"40"` key in all five v10 shape
files. Add a test that round-trips every member of every v10 certification enum
through `VerificationInput.enum` against every v10 shape, asserting no
`KeyError`. That test is the real deliverable; it makes this class of drift
impossible to reintroduce.

**Verify:** the new parametrized test passes for all v9 and v10 enums against
their matching shapes.

### Phase 3 — make the skip legible

The current message says "Ignoring all writes to the 'Verification' worksheet",
which will no longer be true. Reword to name what is skipped (the certification
selections) and what is still written (dwelling units, setpoints), and state
both versions. Document in `context/CODING_STANDARDS.md` or
`docs/dev/exporter-patterns.md` that PHX carries version-specific PHI enums and
that `set_phx_phpp10_settings` deliberately leaves three attributes on v9
members — finding (b) above.

**Verify:** the message appears once per export, not once per variant.

### Phase 4 — re-record the replay fixture

Needs live Excel + the licensed template. Expected diff for `Single_Zone.hbjson`
(a v9 model against 10.6): exactly three new cells — `Verification!F29`, `K28`,
`N28` — and no enum cells. If any enum cell appears, Phase 1 is wrong.

**Verify:** `python -m pytest tests/test_xl_replay/` green; diff the fixture and
confirm it is those three cells and nothing else.

### Phase 5 — closeout

`python -m pytest tests/`; update [`README.md`](README.md) and
`planning/STATUS.md`.

## Related

- `docs/dev/exporter-patterns.md` → shape-driven enum options
- [`02`](02-ventilation-wind-protection.md) — the other "written, but nowhere useful" case
