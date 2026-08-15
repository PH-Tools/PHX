# PHPP export: ventilator ID resolves to `None-<name>`, silently zeroing heat recovery

**Status:** Filed — reproduced against PHPP 10.4a, root cause not fully pinned
**Opened:** 2026-08-15
**Owners:** `PHX/PHPP/sheet_io/io_components.py`, `PHX/PHPP/phpp_app.py`
**Found by:** OpenPH `native_reference` golden fixture
(`openph-workspace`, `planning/archive/dated/2026-08-15/native-pipeline-reference-case/`)

## Defect

After a full `write_phx_project_to_phpp` run, the `Addl vent` ventilation-unit
selection reads `None-REF-HRV` instead of `01ud-REF-HRV`.

PHPP cannot resolve that name against `Components!LQ13:MF914`, so `Addl vent`
reports `#N/A` for the unit's application range and specific electric power, and
**`Ventilation!L32` (effective heat recovery efficiency) falls to `0`**.

The workbook then models a balanced HRV with **no heat recovery at all**.
Nothing raises, no cell shows an error on the `Ventilation` sheet, and the
resulting demand stays entirely plausible. In the case that found it, annual
heating demand read **47.5 kWh/(m²a)** against the reference engine's 28.4 —
a 67% error produced by one unresolved string.

## Reproduction

Export any project with a single ventilator into a copy of
`PHPP_EN_V10.4a_Example.xlsx` and compare `Components` rows 11-13 before and
after. Observed:

| Row | Column | Pristine | After export |
|---|---|---|---|
| 11 | LQ:LW | `ID` / `Description` / … (header labels) | unchanged |
| 12 | LQ | *(empty)* | *(empty)* |
| 12 | LR | *(empty)* | `REF-HRV` |
| 12 | LS / LT / LW | `%` / `%` / `Wh/m³` (unit labels) | `0.75` / `0.6` / `0.45` |
| 13 | LQ | `01ud` | `01ud` |
| 13 | LR:LW | `Heat recovery unit` / `0.83` / … | `REF-HRV` / `0.75` / `0.6` / `0.45` |

So the ventilator's four fields were written **twice**: once into the units
*label* row (12) and once into the first entry row (13). Row 12 keeps an empty
ID cell because `LQ12` is not part of the write.

`get_ventilator_phpp_id_by_name` then scans column `LR` from row 1 and takes the
**first** match — row 12 — and reads the prefix from one column left (`LQ12`,
empty), producing `f"{None}-{name}"`.

## Why it stays silent

Three independent things have to line up for this to be visible, and none of
them is:

1. `f"{prefix}-{_name}"` formats `None` into the string rather than failing on
   it, so the lookup "succeeds".
2. PHPP resolves an unknown unit name to `#N/A` on `Addl vent` — a sheet most
   users never open — while `Ventilation!L32` shows a clean `0`.
3. A zero-heat-recovery balanced system still produces a believable heating
   demand. Only a comparison against an independently-computed expectation
   catches it.

## Root cause — partly identified

The double write is not explained by reading `write_ventilators`, which writes a
single row per ventilator starting at `section_first_entry_row`. Two candidates,
neither confirmed:

- `_iter_project_ventilators` yielding the same ventilator twice (giving rows
  `start` and `start + 1`), combined with a `start` of 12 rather than 13.
- A row-index off-by-one in the section locators.

**One concrete, independently-verifiable bug was found while looking**, in
`io_components.py::Ventilators.find_section_header_row`:

```python
xl_data = self.xl.get_single_column_data(..., _row_start=_row_start, ...)
for i, val in enumerate(xl_data):        # 0-based, but data starts at _row_start
    if self.shape.ventilators.locator_string_header == val:
        return i
```

`enumerate(xl_data)` yields 0-based indices while the data begins at
`_row_start` (default `1`), so the returned value is an index, not a row
number — a header on row 8 returns `7`. Compare
`find_section_first_entry_row`, which does it correctly with
`enumerate(xl_data, start=self.section_header_row)`. The error currently
cancels inside `find_section_first_entry_row` (its enumerate start and its data
start shift together), so it may not be the cause here — but any other consumer
of `section_header_row` gets a row number one too low.

## Suggested fixes

Independent of which candidate is the cause:

1. **Fix `find_section_header_row`** to `enumerate(xl_data, start=_row_start)`.
2. **Make the lookup fail loudly.** `get_ventilator_phpp_id_by_name` should
   raise when the prefix cell is empty rather than formatting `None` into the
   ID. An unresolvable component ID is never a valid export.
3. **Anchor the name search to the entry section.** The scan starts at row 1,
   so it can match a label row or any other cell in column `LR`. Bounding it to
   `section_first_entry_row .. section_last_entry_row` removes the whole class
   of problem. `get_ventilator_phpp_id_by_row_num` already reads both cells from
   one row and does not have this failure mode.
4. **Assert after writing.** A post-write check that every `Addl vent` unit
   selection matches `^\d+ud-` would have caught this at export time.

## Workaround in place downstream

`openph-workspace/tools/write_native_reference_phpp.py::_repair_ventilator_registration`
restores the `Components` label row and rewrites the `Addl vent` selection. It
is documented as a workaround for this defect and should be deleted once this
is fixed.

## Scope

Affects PHPP export only — WUFI XML and METr JSON do not use this lookup. Any
project whose ventilator lands the same way is affected, and the failure is
silent, so previously exported PHPP files are worth spot-checking:
`Ventilation!L32` reading `0` with a balanced HRV assigned is the signature.
