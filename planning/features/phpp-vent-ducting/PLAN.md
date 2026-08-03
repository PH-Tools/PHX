# PLAN — Implementation sequence

Read `PRD.md` first — it contains the verified PHPP column map and the two shape-file
bugs. Follow `context/CODING_STANDARDS.md`; conventional commit: `feat(phpp): write
ventilation ducting to the 'Addl vent' worksheet`.

## Step 1 — Fix + clarify the shape files (Complete)

Files: all 7 `PHX/PHPP/phpp_localization/EN_*.json`, `shape_model.py:566-586`.

1. In every `EN_*.json` → `ADDNL_VENT.ducts.inputs`:
   - `diameter.column`: `"F"` → `"E"`
   - `duct_assign_9.column`: `"Z"` → `"Y"`
2. Rename the three misleading length/flag fields in both the JSONs and
   `AddnlVentInputsDucts` (they are unused anywhere else — grep first to confirm):
   - `sup_air_duct_len` → `duct_length` (col L, unit M)
   - `oda_air_duct_len` → `is_supply_flag` (col M, unit null)
   - `exh_air_duct_len` → `is_exhaust_flag` (col N, unit null)
   If the rename turns out to touch anything beyond the shape model + JSONs + the new
   row model, skip it and instead document the real semantics in docstrings.
3. `tests/test_PHPP/test_shape_file.py` validates every JSON against the pydantic shape
   model — run it.

Verification gate: the PHPP-9 shape files (`EN_9_6A`, `EN_9_7IP`) were only assumed to
share the v10 duct columns — no PHPP-9 workbook was available. Flag this in the PR;
Ed can spot-check a PHPP 9.6 file. Do not block on it.

## Step 2 — Row model: `PHX/PHPP/phpp_model/vent_ducts.py` (Complete)

The file exists and is empty. Model it directly on `vent_units.py` (`VentUnitRow`):

```python
@dataclass
class VentDuctRow:
    __slots__ = ("shape", "phx_duct", "phpp_vent_unit_number")
    shape: shape_model.AddnlVent
    phx_duct: hvac.PhxDuctElement
    phpp_vent_unit_number: int  # 1-based ordinal of the assigned vent unit (1-10)

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> list[xl_data.XlItem]: ...
```

`create_xl_items` writes (see PRD column table):

- `quantity` ← `phx_duct.quantity`
- round (`duct_shape == 1`): `diameter` ← `diameter_mm` (`"MM"` → shape unit); omit width/height
- rect (`duct_shape == 2`): `width` ← `width_mm`, `height` ← `height_mm`; omit diameter
- `insul_thickness` ← `insulation_thickness_mm` (`"MM"` → shape unit)
- `insul_conductivity` ← `insulation_conductivity_wmk` (`"W/MK"` → shape unit)
- `insul_reflective` ← `"x"` if `is_reflective` else omit the item
- `duct_length` ← `length_m` (`"M"` → shape unit)
- `is_supply_flag` / `is_exhaust_flag` ← `1` per `duct_type` (exactly one of the two)
- `duct_assign_{phpp_vent_unit_number}` ← `1`

Use the `_create_range` / `_get_target_unit` / `partial(XlItem, _sheet_name)` idiom from
`VentUnitRow`. Register the module in `phpp_model`'s import surface the same way
`vent_units` is imported in `phpp_app.py:22-24`.

## Step 3 — Builder: `phpp_app.PHPPConnection.write_project_vent_ducting()`

File: `PHX/PHPP/phpp_app.py` (place after `write_project_ventilators`, ~line 610).

```
def write_project_vent_ducting(self, phx_project) -> None:
    if self.easyPh: return
    # 1-based ordinal of each ventilator, in the SAME enumeration order as
    # write_project_ventilators (variants -> mech_collections -> ventilation_devices)
    unit_number_by_id: dict[int, int] = {...}
    rows = []
    for variant -> mech_collection -> duct in mech_collection.vent_ducting:
        n = unit_number_by_id.get(duct.vent_unit_id)
        if n is None or n > 10: warn + skip
        rows.append(VentDuctRow(self.shape.ADDNL_VENT, duct, n))
    if not rows: return                      # duct-free model: zero sheet interaction
    truncate to section capacity (find_section_last_entry_row) with a warning
    self.addnl_vent.write_vent_ducts(rows)
```

Notes:
- `if not rows: return` must come **before** any sheet-locating call so the golden
  replay (duct-free fixture) sees zero new reads/writes.
- Type the existing `AddnlVent.write_vent_ducts(_vent_ducts: list)` signature properly
  (`list[vent_ducts.VentDuctRow]`) while you're there — it was left untyped because the
  row model didn't exist.
- Capacity check: `VentDucts.find_section_last_entry_row()` already locates the end of
  the section ("Additional lines" marker). Rows beyond capacity → `warning` (match the
  project's existing warn style) + truncate.

## Step 4 — Wire into the write sequence

Files: `PHX/hbjson_to_phpp.py` (canonical sequence, `write_phx_project_to_phpp`),
`_testing_HBJSON_to_PHPP.py` (dev harness, lines 64-65).

Insert `phpp_conn.write_project_vent_ducting(phx_project)` **after**
`write_project_ventilators` (assignment ordinals depend on the units having been written)
— i.e. between lines 49 and 50 of `hbjson_to_phpp.py`, before `write_project_spaces`.

## Step 5 — Tests

- **Unit — row model** (`tests/test_PHPP/test_phpp_model/test_vent_ducts.py`): build
  `PhxDuctElement`s (round + rect, supply + exhaust, reflective on/off, multi-segment for
  the weighted averages) and assert `create_xl_items` produces the right ranges, values,
  and units for both an SI shape (`EN_10_6`) and an IP shape (`EN_10_6IP`). Follow the
  fixture pattern in the neighboring `test_component_frame.py`.
- **Unit — builder ordering**: ventilator→ordinal mapping matches the
  `write_project_ventilators` enumeration; duct with unknown `vent_unit_id` and with
  ordinal > 10 are skipped with a warning; duct-free project → no calls on `addnl_vent`
  (mock/spy).
- **Invariant**: full suite `python -m pytest tests/` — the xl-replay golden test must
  pass **unchanged** (fixture has no ducts; do not re-record).
- Reset-counter hygiene: `PhxDuctElement` has a `_count` ClassVar — use the existing
  `reset_class_counters` conftest fixture pattern if instance numbering matters in tests.

## Step 6 — Live verification (Ed / manual)

Run an HBJSON model that has ducting (any recent project export) through
`hbjson_to_phpp.py` against PHPP 10.6 and eyeball the Ducts section: lengths in L, one
flag in M or N, assignment in the right Q–Z column, K/O/P formulas resolving (no `#REF`),
and the Ventilation worksheet heat-loss result moving vs. a no-duct write.

## Step 7 — Docs

Per repo rule 5: new public API (`write_project_vent_ducting`, `VentDuctRow`) →
docstrings in ph-docs format; check whether `docs/nav.yml` autodoc pages for
`PHX.PHPP.phpp_model` / `phpp_app` need the new module added (follow
`docs/.instructions.md` — do not restructure).
