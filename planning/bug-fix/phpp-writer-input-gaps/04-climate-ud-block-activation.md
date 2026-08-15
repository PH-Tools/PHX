# The user-defined climate block is filled in, never named, never selected — and one cell is corrupted

**Status:** Scoped — gate decided 2026-08-15 (library codes when valid, UD
otherwise); ready to implement
**Opened:** 2026-08-15
**Owner:** `PHX/PHPP/phpp_model/climate_entry.py`; `PHX/PHPP/sheet_io/io_climate.py`
**Umbrella:** [`README.md`](README.md)
**Filed as:** "User-defined climate block name → `Climate!D67`" (gap 5 of the incoming request)

## The verified layout of the UD block

Blank 10.6, first user-defined block at row 67 (blocks repeat every 10 rows at
67, 77, 87, 97, 107 — names `Example`, `2`, `3`, `4`, `5`):

| Cell | Role | Blank-template value |
|---|---|---|
| `C67` | row label `Name of location` | — |
| **`D67`** | **the block's name — its key** | `'Example'` |
| `E67` | label, mirrors `E$25` (`Latitude °`) | formula |
| `F67` | latitude | `50.2` |
| `G67` | label (`Longitude °`) | formula |
| `H67` | longitude | `8.3` |
| `I67` | label (`Altitude [m]`) | formula |
| `J67` | elevation | `112` |
| `K67`, `L67` | **unused** | empty |
| `M67` | label (`ΔTSummer [K]`) | — |
| `N67` | summer ΔT | `5.7` |
| `O67` | label (`T Comfort criterion [°C]`) | — |
| **`P67`** | **T comfort criterion — a numeric input** | `-1` |
| `E68:P75` | the eight monthly data rows | populated |
| **`E76`** | **the data-set comment / source string** | `'Exemplary data set by PHI'` |

## Three defects in `ClimateDataBlock.create_xl_items`

`phpp_model/climate_entry.py:103-120` writes, per the shape's
`ud_block.input_columns`:

```python
XLItemClimate(create_range("latitude", 0),      phx_site.latitude)        # F67  correct
XLItemClimate(create_range("longitude", 0),     phx_site.longitude)       # H67  correct
XLItemClimate(create_range("elevation", 0),     …station_elevation)       # J67  correct
XLItemClimate(create_range("display_name", 0),  self.phx_site.display_name)   # L67
XLItemClimate(create_range("summer_delta_t",0), …daily_temp_swing)        # N67  correct
XLItemClimate(create_range("source", 0),        self.phx_site.source)     # P67
```

1. **`D67` is never written.** The block keeps the template's name, `Example`.
2. **`display_name` goes to `L67`**, which nothing reads. The name belongs in
   `D67`.
3. **`source` goes to `P67`**, which is the `T Comfort criterion [°C]` numeric
   input. PHX writes a *string* there on every export — the golden fixture shows
   `P67: '__unknown__'`, PHX's `PhxSite.source` default. This is not an omission;
   it is an active corruption of a climate parameter. The comment cell is `E76`
   (`start_row + 9`, column `E`).

(`elevation_unit` and `summer_delta_t_unit` in the same `input_columns` dict are
unit codes, not column letters — `"M"` for metres, `"DELTA-C"`. Confusing, but
used correctly by the writer. Leave them; do not "fix" `elevation_unit` into a
column.)

## The fourth defect: the block is never selected

Filling a UD block does nothing on its own. The three selectors keep pointing at
whatever library set was active. Golden fixture, `Climate` column D:

```
D9: 'US-United States of America'   D10: 'New York'   D12: 'US0055c-New York'   D18: '=D17'
```

Those are `PhxPHPPCodes` library codes, written by `ClimateSettings`
(`climate_entry.py:32-36`). So PHX writes a synthetic climate into the UD block
*and* tells PHPP to use a built-in New York data set. Nothing errors; the demand
stays plausible. The source investigation caught it only by comparing monthly
temperatures cell by cell.

All three selectors must be set. Verified against the blank 10.6:

| Cell | Required value | Provenance |
|---|---|---|
| `D9` | `ud-User-defined data` | `Climate!AE69 = "ud-"&Data!$A$257`; `Data!A257 = 'User-defined data'` |
| `D10` | `All` | `Climate!AJ69 = Data!$A$261`; `Data!A261 = 'All'` |
| `D12` | `ud---NN-<name>` | see below |

The data-set literal is composed in the hidden lookup table at rows 256+, one
row per UD block:

```
Climate!P256 = '=D67'        (the block name)
Climate!N256 = 'ud'   M256 = '---00'
Climate!E256 = '=IF(M256<>"",I256,N256&"-----")&"-"&P256'
```

Read back with cached values, `E256` evaluates to **`ud---00-Example`**, and
`E257` (block 2, `P257 = '=D77'`) to `ud---01-2`. So the literal for the first
block is exactly `f"ud---{index:02d}-{name}"` with `index = 0` for `start_row =
67`. The name in `D67` and the name inside the selector string must agree — which
is precisely why defect 1 and defect 4 have to be fixed together.

## An adjacent model bug

`PhxPHPPCodes.dataset_name` (`model/phx_site.py:430`) is missing its type
annotation, so it is a **class attribute, not a dataclass field**:

```
>>> [f.name for f in dataclasses.fields(PhxPHPPCodes)]
['country_code', 'region_code']
>>> PhxPHPPCodes(country_code='a', region_code='b', dataset_name='c')
TypeError: PhxPHPPCodes.__init__() got an unexpected keyword argument 'dataset_name'
```

It works today only because `from_HBJSON/create_variant.py:430` assigns it by
attribute. One-character fix (`dataset_name: str = "US0055b-New York"`), and it
is in this packet's blast radius.

## The decision — settled 2026-08-15

**Gate on the codes.** If the model supplies a *valid* PHPP library data-set
name, select it and leave the library path alone. If it does not, fall back to
the user-defined block, populated from the model.

Rejected: gating on `PhxSite.selection` / `PhxClimate.selection` — both default
to `USER_DEFINED` (`model/enums/phx_site.py:18`, `:33`), so that gate would flip
every export onto the UD path. Rejected: always-UD — it discards a
deliberate library-code choice.

### "Valid" is a cascading, recalc-dependent check

This is the part that makes the rule non-trivial, and it has to be built as
described or the gate is a lie. The `D12` drop-down is **not** a static list. Its
data validation is `Climate!$AU$69:$AU$175`, and that range is computed from the
current `D9` / `D10` selection:

```
Climate!AU69 = IF($AU$68=1,AR69,AO69)      ' AU68 = 1*MID(D11,1,1)  (the sort order)
D9  validation = $AE$69:$AE$175
D10 validation = $AJ$69:$AJ$122
D12 validation = $AU$69:$AU$175
```

So a data-set name is only meaningful *relative to* a country and region.
Validation must cascade, with a recalculation between each step:

1. write `D9` = `phpp_codes.country_code`; recalc; read `AE69:AE175` — country
   must be a member
2. write `D10` = `phpp_codes.region_code`; recalc; read `AJ69:AJ122` — region
   must be a member
3. recalc; read `AU69:AU175` — `phpp_codes.dataset_name` must be a member
4. all three hit → write `D12`, library path, **skip the UD block entirely**
5. any miss → revert `D9`/`D10`, take the UD path

`xl.calculate()` already exists (`xl_app.py:729`, surfaced as
`PHPPConnection.calculate`), as do `get_single_column_data` and the
`read_active_country` / `read_active_region` / `read_active_data_set` readers in
`io_climate.py`. Nothing new is needed at the interop layer.

Step 5's revert matters: if the country is valid but the data set is not, leaving
`D9`/`D10` on the library values while the UD block is what actually carries the
data would reproduce the exact bug this packet is closing.

Note this costs three extra recalculations on the library path. The write
sequence already recalculates once after `Climate` for locator safety
(`hbjson_to_phpp.py:40-41`), and `plans/20260714/` tracks Excel-interop
performance — if that proves too slow, the fallback is to read all three
validation ranges once up front rather than re-reading after each write. Measure
before optimising.

### Consequence: stop writing the UD block unconditionally

Today PHX writes the UD block on *every* export, including library-path ones.
That is what puts `'__unknown__'` into `P67` on projects that never wanted a
user-defined climate. Under this decision the UD block is written only on the
fallback path.

## Phases

### Phase 0 — failing test

`tests/test_PHPP/test_sheet_io/test_io_climate_ud_block.py` (new):

- `D67` receives `phx_site.display_name` — fails today
- `E76` receives `phx_site.source` — fails today
- `P67` is **not** written — fails today (currently gets `'__unknown__'`)
- `L67` is not written
- `F67`/`H67`/`J67`/`N67` and the monthly block `E68:P75` unchanged

**Verify:** the four new assertions fail; the unchanged-cell assertions pass.

### Phase 1 — fix the block writer

In `shape_model.ClimateUDBlockCol` and all seven JSONs: add `name: "D"` and
`comment: "E"`; keep `display_name` and `source` for one release or delete them
outright — they have no correct target and no reader. In
`ClimateDataBlock.create_xl_items`: write the name at offset 0 column `D`, the
comment at offset **9** column `E`, and remove the `L67`/`P67` writes.

Add `dataset_name: str` to `PhxPHPPCodes`.

**Prefer the named ranges over row arithmetic.** The workbook names both cells
this packet cares about:

```
Klimadaten_Muster            -> Climate!$D$67    (the first UD block's name)
Klimadaten_Muster_Quelle     -> Climate!$E$76    (its source / comment)
Klimadaten_Muster_Alle_Monate-> Climate!$E$68:$T$75
```

These independently confirm the cell identification above and are stable across
10.x row drift in a way that `start_row + 9` is not. `io_climate` already reads
through `shape.named_ranges`, so the pattern exists. Use the named ranges for the
name and comment; the monthly block can stay on the existing offset walk.

**Verify:** Phase 0 passes.

### Phase 2 — implement the gate

Restructure `write_climate_data` into an explicit two-branch flow rather than the
current unconditional "write block, then write settings":

```
try_library_codes(variant.site)      # the cascading validation above
  -> hit:  write D9/D10/D12; do NOT write the UD block
  -> miss: revert D9/D10; write the UD block (Phase 1);
           write D9 = "ud-User-defined data", D10 = "All",
                 D12 = f"ud---{block_index:02d}-{name}"
```

`block_index` derives from `shape.ud_block.start_row` rather than being
hardcoded. PHX writes only the first block today (`io_climate.get_start_rows`
returns a single-element list), so it is `0` — but the derivation should be
explicit so a second block cannot silently mis-select.

The `ud-User-defined data` / `All` literals belong in the shape files as data,
not in Python — they are localization strings, sourced from
`Data!A257` / `Data!A261`.

Also fix `io_climate.write_active_climate`'s hardcoded `start_row = 9`. The
shape's `active_dataset.locator_col_header` / `locator_string_header` are empty
strings, so there is nothing to locate by — either populate them or move the
addresses into `defined_ranges` alongside the existing `Klima_*` entries.

**Verify:** three tests — a valid library triple takes the library path and
writes no UD cells; an invalid data-set name with a valid country/region falls
back and leaves no library codes behind; an invalid country falls back cleanly.
The fake XL framework will need the three validation ranges seeded, since it
resolves reads against cell-state.

### Phase 3 — fail loudly on the one unrecoverable case

The gate makes an invalid library name recoverable, so it must **not** raise.
One case is still unrecoverable: falling back to the UD path with an empty
`display_name` produces the selector literal `ud---00-`, which matches nothing
and silently reverts PHPP to whatever was selected before — the exact failure
this packet closes.

Add that check to `validate_project_export_readiness`
(`model/identity_validation.py`), which already runs first in
`write_phx_project_to_phpp`. It cannot see the workbook, so it cannot know
whether the fallback will be taken; require a non-empty `display_name`
unconditionally. That is a cheap, always-true precondition rather than a
conditional one.

**Verify:** a new test alongside the existing
`tests/test_from_HBJSON/test_create_variant/test_climate_readiness.py`, which
already exercises the empty-`dataset_name` case and should now assert it is
*tolerated* rather than fatal.

### Phase 4 — re-record the replay fixture

Live Excel required. `Single_Zone.hbjson` carries
`phpp_codes.dataset_name = 'US0055c-New York'` (the fixture's `D12`), so the
first question is whether that name is actually a member of `AU69:AU175` under
`US-United States of America` / `New York`. **The two plausible outcomes have
opposite diffs, and which one occurs is itself the interesting result:**

- **valid** → library path. `D9`/`D10`/`D12` unchanged; the entire UD block
  (`F67`…`P75`, 138 cells) *disappears* from `golden_writes`. A large diff, but
  the right one.
- **invalid** → UD path. `D9`/`D10`/`D12` switch to the `ud-` literals, `D67`
  and `E76` appear, `L67`/`P67` vanish, monthly block unchanged.

Note `PhxPHPPCodes.dataset_name` defaults to `US0055b-New York` while the fixture
shows `US0055c` — the `b`/`c` suffix distinguishes real PHPP library entries, so
this is a genuine lookup, not a placeholder. Confirm membership before assuming
either branch.

**Verify:** `python -m pytest tests/test_xl_replay/` green; `P67` is gone from
`golden_writes` either way. Record which branch fired, in this file.

### Phase 5 — closeout

`python -m pytest tests/`. The `phi-rules` corpus
(`phpp-climate/rules.md`) documents the three-selector activation from a 10.4a
example; add the 10.6 confirmation and the `P67` / `E76` column roles, which it
does not currently carry. Update [`README.md`](README.md) and
`planning/STATUS.md`.

## Related

- `phi-rules` → `rulesets/phpp-10-r1/calculators/phpp-climate/rules.md`
