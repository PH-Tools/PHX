# PRD — Write Ventilation Ducting to PHPP "Addl vent"

## Problem

The PHX→PHPP export (`PHX/hbjson_to_phpp.py` → `phpp_app.PHPPConnection`) writes to the
"Addl vent" worksheet:

- **Rooms section** — `write_project_spaces()` (`phpp_app.py:611`)
- **Vent-Units section** — `write_project_ventilators()` (`phpp_app.py:589`)
- **Ducts section** — *never implemented*

The duct data exists in the PHX model (`mech_collection.vent_ducting` →
`PhxDuctElement`/`PhxDuctSegment`, `PHX/model/hvac/ducting.py`) and is already written by
the other two exporters:

- WUFI-XML: `_PhxDuctElement()` at `PHX/to_WUFI_XML/xml_schemas.py:1484`
- METr-JSON: `_PhxDuctElement()` at `PHX/to_METr_JSON/metr_schemas.py:1890`

Result: PHPP models produced by PHX show zero duct heat loss on the cold-side ducts,
understating ventilation heat losses vs. the equivalent WUFI model.

## Existing groundwork (already in `main`, never exercised)

Much of the plumbing was stubbed long ago and left dangling:

| Piece | Location | State |
|-------|----------|-------|
| Shape pydantic model `AddnlVentInputsDucts` / `AddnlVentRoomsInputBlockDucts` | `PHX/PHPP/phpp_localization/shape_model.py:566-612` | Done |
| Shape data `ADDNL_VENT.ducts` in all 7 localization JSONs | `PHX/PHPP/phpp_localization/EN_*.json` | Present but has 2 column bugs (below) |
| Sheet-IO section locator `VentDucts` + `AddnlVent.write_vent_ducts()` | `PHX/PHPP/sheet_io/io_addnl_vent.py:309-376, 405-414` | Done (note: `write_vent_ducts(_vent_ducts: list)` is untyped because the row model never existed) |
| Row model `phpp_model/vent_ducts.py` | `PHX/PHPP/phpp_model/vent_ducts.py` | **Empty file** |
| Builder in `phpp_app.py` + call in write sequence | — | **Missing** |

So the actual feature is: the row model, the `phpp_app` builder, the write-sequence call,
the shape-file fixes, and tests.

## PHPP worksheet semantics (verified against a real PHPP EN 10.6)

Verified 2026-08-03 by reading
`plans/20260714/excel-interop-refactor/scratch/PHPP_EN_V10.6_Empty__record__20260715-003138.xlsx`
with openpyxl. Section title (row 82): *"Data entries for duct sections between the
ventilation unit and the thermal envelope"*. Header row 86 (found via `"Round"` in col E —
matches `VentDucts.find_section_header_row`); first entry row 95 = header + 9 (matches the
hard-coded offset in `VentDucts.find_section_first_entry_row`).

Entry columns (PHPP 10.6 EN):

| Col | Header | Unit | Write |
|-----|--------|------|-------|
| D | Quantity | – | `duct.quantity` (always 1 today) |
| E | Round duct diameter | mm | `duct.diameter_mm` (round ducts) |
| F | Rectangular duct width | mm | `duct.width_mm` (rect ducts) |
| G | Rectangular duct height | mm | `duct.height_mm` (rect ducts) |
| H | Insulation thickness | mm | `duct.insulation_thickness_mm` |
| I | Thermal conductivity | W/(mK) | `duct.insulation_conductivity_wmk` |
| J | Reflective aluminum coating? | (x) | `"x"` if `duct.is_reflective` else blank |
| K | Conductance duct | W/(mK) | *formula — do not write* |
| L | Length of supply air duct | m | `duct.length_m` |
| M | Outdoor or supply air duct | (1) | `1` if `duct_type == SUPPLY` |
| N | Exhaust or extract air duct | (1) | `1` if `duct_type == EXHAUST` |
| O | Duct type | – | *formula — do not write* |
| P | Design air flow rate | – | *formula — do not write* |
| Q–Z | Assignment to ventilation unit 1–10 | (1) | `1` in the column of the assigned vent unit |

Key semantic (this is why the stub shape-field names are misleading): **L is the single
length column for every duct row**; M and N are *type flags* ("enter 1"), not lengths.
"Outdoor **or** supply air" / "Exhaust **or** extract air" — PHPP treats the interior-unit
cold ducts (ODA/EHA) and exterior-unit warm ducts (SUP/ETA) with the same two flags, so the
`PhxVentDuctType.SUPPLY→M`, `EXHAUST→N` mapping holds regardless of unit placement. This
matches the WUFI convention (`DuctType` 1=supply, 2=exhaust), so PHPP and WUFI exports of
the same model stay consistent.

### Shape-file bugs found (all 7 `EN_*.json`, identical `ducts` block)

1. **`diameter` column is `"F"` — should be `"E"`.** (E=round diameter, F=rect width; the
   stub had diameter/width both on F.)
2. **`duct_assign_9` column is `"Z"` — should be `"Y"`.** (Q–Z map to units 1–10;
   assign_9=Y, assign_10=Z. The stub had both on Z.)

All other duct columns in the shape files match the verified workbook. The
`sup_air_duct_len`/`oda_air_duct_len`/`exh_air_duct_len` field names are misleading
(they are really *length / supply-flag / exhaust-flag*) — see PLAN step 1 for the rename
decision.

## Data mapping (PHX → PHPP row)

Source: for each `variant` → `mech_collection` → `mech_collection.vent_ducting`
(`list[PhxDuctElement]`, see `PHX/model/hvac/collection.py:745-750`). All aggregate
properties (length-weighted diameter, insulation, etc.) already exist on `PhxDuctElement` —
the same ones the WUFI exporter uses. `from_HBJSON/create_variant.py:546-548` creates one
SUPPLY and one EXHAUST `PhxDuctElement` per ventilator, with
`vent_unit_id = phx_ventilator.id_num`.

**Vent-unit assignment (Q–Z):** `write_project_ventilators()` writes one row per
`phx_ventilator`, in enumeration order, starting at the Units section's first entry row —
so a ventilator's PHPP unit number is simply its 1-based ordinal in that same enumeration.
Build the duct rows in the same pass (or re-enumerate identically) and map
`duct.vent_unit_id` → ordinal → `duct_assign_<n>`. Do **not** read the unit number back
from Excel (`get_vent_unit_num_by_phpp_id`) — it costs an xl-read per duct and adds
nothing.

**Round vs rectangular:** `duct.duct_shape` returns 1=round / 2=rect. Round → write E,
leave F/G blank; rect → write F/G, leave E blank. (Writing both would double-define the
duct in PHPP.)

**Units:** pass source-unit + shape target-unit through `XlItem` exactly as
`VentUnitRow` does (`phpp_model/vent_units.py:49-54`) so the IP shape files (`EN_*IP`,
inches) convert automatically. Flag columns (J, M, N, Q–Z) have `unit: null` — write raw.

## Constraints

- **PHPP capacity:** the Ducts section has a fixed number of entry rows (~15 in 10.6;
  `find_section_last_entry_row` locates the end via the "Additional lines" text). More
  ducts than rows → warn and truncate (match how the sheet handles overflow elsewhere;
  do not write past the section).
- Max 10 vent units are assignable (Q–Z). Ducts serving a ventilator beyond #10 → warn+skip.
- **Golden-replay invariant** (`tests/test_xl_replay/`): the `Single_Zone.hbjson` fixture
  has **no ducting**, so the new step must write nothing for a duct-free model and the
  existing golden state must pass unchanged, without re-recording. (If the fixture is ever
  swapped for one with ducts, re-record via `scripts/perf/record_replay_fixture.py`.)
- `easyPh` mode: skip (return early), same as the other Addl-vent writers.

## Success criteria

1. `hbjson_to_phpp.py` on a model with ventilation ducting fills the Ducts section:
   correct geometry/insulation columns, one type-flag, one unit-assignment flag per row.
2. A duct-free model produces zero writes to the Ducts section; full test suite
   (incl. golden replay) passes with no fixture re-record.
3. PHPP duct rows are consistent with the WUFI-XML export of the same model
   (same lengths, diameters, insulation, type, unit assignment).
