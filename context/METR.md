# METr — the app, how to test our JSON in it, and what we have learned

METr (https://metr.c3rro.com, built by C3rro, version seen: front end `1.92` / back end `2.74`)
is Phius's browser replacement for WUFI-Passive. PHX writes its JSON in `PHX/to_METr_JSON/`
(structure: `docs/dev/exporter-patterns.md` § METr JSON Exporter).

Read this before debugging METr output, so the investigation isn't repeated. Add to it as
facts are confirmed. Open bugs and their status belong in `planning/STATUS.md`, not here.

## 1. Test loop (Claude in Chrome, driving Vivaldi)

The Claude in Chrome extension is installed in Vivaldi, so its tabs share Ed's METr sign-in.
The agent can only drive tabs in its own tab group, not a METr tab Ed already has open.

**METr has no cloud copy of a local model.** Project › Locally › Load reads a JSON file into
the tab's memory. Nothing gets loaded by URL, so every tab must load the file itself.

Load a file without the native file picker (which the agent can't operate):

1. Navigate the agent's tab to `https://metr.c3rro.com`.
2. Patch the page in JS before opening the menu:
   ```js
   window.confirm = () => true;               // auto-accept the "Store & Sync…not checked" dialog
   HTMLInputElement.prototype.click = function () {};  // stop the native file picker opening
   ```
   A native `confirm()` left open freezes the renderer, and CDP clicks time out after 30 s.
   If it does happen, pressing `Return` through the extension dismisses it.
3. Click **Project › Locally › Load**. This arms the file input `input[name=own]`
   (`accept=".json,.mwp"`). Setting a file on that input *before* clicking Load does nothing.
4. Put the file on that input with the extension's `file_upload` (limit 10 MB per call).
5. **Click "Calculate mean month shading"** in the Status bar. METr requires this after every
   load. Until it runs, Status shows only "Shading factors are not consistent with building
   geometry" and no results appear. It takes about 20 s on a 1 MB model.
6. Read results and warnings with `get_page_text` (Status panel + MAIN RESULTS).

The JS patches are lost on every page reload.

## 2. Reading METr's in-memory model

- `window._c3r_` is the app object. `_c3r_.projectJSON` is the parsed, live model, the same
  shape as our file plus METr's own additions. `_c3r_.def` (about 1,588 entries) looks like the
  field defaults/definitions. Not explored yet.
- After a load, the original file is still readable in the page:
  `await document.querySelector('input[name=own]').files[0].text()`.
- Tool output is truncated at roughly 1–2 kB, so **diff inside the page** and return only the
  diff, in slices. The recursive diff used 2026-10-24 normalized array indices to `[]`, then
  bucketed paths into missing / added / changed with a count and one example each. Rebuild it
  from that description when needed.

### Field definitions: `_c3r_.def`

`_c3r_.def[<key>]` defines a field: `n` is the UI label, and `sel` is the option list as
`[code, label, …]`. Search it by key to decode any enum before guessing. Device-type rules
live in `def.tHdev.sel[…][2]`: `refQ` lists the allowed reference quantities, and `refED`
lists the allowed norm references per type.

**Enums do not match WUFI's.** PHX carries WUFI codes in the model, so the METr writer has to
translate each one.

| METr `refED` | Label | Value field read |
|---|---|---|
| 1 | Use | `enDrU` |
| 2 | Day | `enDrD` |
| 3 | Year | `enDrY` |
| 4 | CEF | `CEFef` |
| 5 | Use | `enDrU1` |
| 6 | Year | `enDY` |
| 7 | Year | `enDrU2` |
| 8 | Use | `enDrU`, `EFGas` |
| 9 | CEF (gas) | `CEFGas` |

For the fridge-type devices (refrigerator, freezer, fridge/freezer combo) METr allows
`refED` ∈ {3 Year, 2 Day}, and WUFI's `ReferenceEnergyDemandNorm` codes them 1 = Day,
2 = Year (verified in WUFI-Passive 3.6, 2026-10-24). The writer translates these for the
fridge types.

**WUFI's norm code is an index into each device's own dropdown**, so its meaning depends on
the device (honeybee-ph `default_elec_equip.py`): dishwasher 2 = Year, washer 2 = Year,
dryer 2 = CEF, fridge types 1 = Day, cooktop 1 = Use.

**METr narrows `refED` by calc scope.** In the Phius scope (`calcScope` 4, checked in the UI
2026-10-24):

| Device | Allowed `refED` | Notes |
|---|---|---|
| Dishwasher | 7 Year only | Hardcoded 7 is correct |
| Washer | 6 Year only | Hardcoded 6 is correct |
| Dryer (vented electric) | 4 CEF only | Hardcoded 4 is correct |
| Fridge / freezer / combo | 2 Day or 3 Year | The only real choice; mapped from the model |
| Cooktop | none (kWh/use) | Type comes from `tCook`: 1 Electric coil, 3 Induction, 2 Gas |

The nested `refED` lists in `def.tHdev` appear to be per calc-scope group (compare the
`defVal` groups `[3,5,6]`, `[7,8]`, `[9,10]`), not per `refQ`. That is unconfirmed, so check in
the UI before relying on it.

### Mixed (inhomogeneous) layers

A layer with exchange materials carries three extra keys. Shape taken from Ed's hand-built
`15_METr/With-Exchange-Materials.json`, 2026-10-24:

```json
{"thick": 0.18415, "idMat": 16,
 "lExDivH": [0.18415, 0.0381, 0.3683, 0.0381, 0.18415],   // column widths [m]
 "lExDivV": [],                                           // row heights [m]; [] = one row
 "lExMat":  [[1, 0, 15], [3, 0, 15]]}                     // [column, row, idMat], exchange cells only
```

- Cells holding the layer's own material are not listed. `idMat` must be in `lMaterial`.
- This matches PHX's `PhxLayerDivisionGrid` (`cell.column`, `cell.row`, 0-based from top-left)
  and the WUFI writer's convention of dropping a single row or column.
- On load METr adds `tAss`, `inh`, `U`, `U6946` and `partRes`
  (`{tRes, tRes6946, U, U6946, inh}`). `tRes` is the homogeneous value and `tRes6946` is
  ISO 6946 with the mix. Our `tRes` is ignored and recomputed.

### Heat pumps (`tHP`)

`def.tHP`: 2 Combined, 3 Heat pump (annual COP), 4 Heat pump – rated monthly COP,
5 HPWH (EF) inside, 7 HPWH (UEF) inside. Several keys share a UI label, so check by loading
a probe file rather than by label. For `tHP 3`, checked 2026-10-24:

| UI field | Key METr reads | Not it |
|---|---|---|
| Annual heating coefficient of performance (COP) | `aCOPHP` | `aCOP` (a separate "Annual COP" field) |
| Total system performance ratio of heat generator | `tSysPHP` | `pHGHP` (same label, still flagged empty) |

When either is missing, Status shows "No data or invalid format" for it, and no results
appear. The writer has set both since 2026-10-24. Monthly (`tHP 4`) and HPWH (`tHP 5`)
keys are not yet checked this way.

### Getting a "truth" file

Ed can fix a value by hand in METr and save it with **Project › Locally › Save**. Diffing
that file against ours (plain Python, both on disk) isolates the one key METr expects.

## 3. Load-time behavior (what METr changes, and what that means)

These diffs between our file and `projectJSON` are **METr's doing, not exporter bugs**,
unless noted:

| Field | What METr does |
|---|---|
| Selector fields `{sel, iV, val[]}` (e.g. zone `flAreaZ`, `netVolZ`, `grossVolZ`) | `val` holds one value per option and `iV` picks the active one. On load METr recomputes the non-selected `val` slots from geometry and **keeps `val[iV]`** (ours). PHX writes the same number into every slot, so those slots always show up in a diff. That is noise as long as `val[iV]` is unchanged |
| Foundation-style fields (`slabFlU`, `flPer`, `flSArea`, `bmentFlU` …) | Expanded to `[[[value, …flags]], index]` lists, with null defaults for unused ones |
| `geom.lIDXYZ` vertices | Translated as a whole (re-centered), so every coordinate changes |
| `geom.lPoly[]` | Rounds `areaP`/`perim`/`incl` to 4 dp, **swaps `horW`/`vertH`**, adds `pos3P`, `tri3P`, `azimN`, `U` |
| `tv`, `ntv`, `nr`, `view`, `uuid`, `jobNr`, `vFE`, `vBE` … | UI tree and session state |
| `HVAC…distrib.lVentDuct[].id` | Renumbered from 1 |
| `lZone[].desCondZ.TRedUD` | Moved up to `lZone[].TRedUD` |
| `lAssembly[]` | Recomputes `tRes` and adds `U` and `partRes`. The 6.99 → 7.86 gap on Elizabeth St was the missing stud subdivision: METr was computing all-insulation. With the mix written (fixed 2026-10-24), the Exterior-Wall reads `tRes6946` 6.93 / `tRes` 7.86, i.e. R-39.38 inhomogeneous / R-44.66 homogeneous in IP. WUFI shows R-38.38 / R-43.69 for the same wall; that offset of about 1 in both values is METr vs WUFI and not yet explained |
| `lWindow[]` | Rounds `Uw`/`frF`. **Recomputes `Ufr`** (ours 1.578 → 2.396 on Elizabeth St; see §5) |

## 4. Hardcoded values in `metr_schemas.py` (audit 2026-10-24)

The writer assigns about 570 literals. METr wants every key on every object (the
"super-device", "super-foundation" and "super-component" pattern), so most of them are
inert structural defaults: hygrothermal (HAM) settings, DIN 4108, the building generator,
unused device families, and the Phius-case extras that the WUFI writer hardcodes too (WC count,
evaporation 15 W, `tVentSys`, `tInfiltr` …). The audit compared each literal with what the
WUFI writer reads from the PHX model, because the WUFI XML is the reference that opens
correctly.

| Where | Literal | Model has | Status |
|---|---|---|---|
| `_component_surface_defaults` | `tAbsC -2`, `absEC 0.4`, `emisEC 0.9` | `assembly.exterior_solar_absorptance` / `exterior_thermal_emissivity` (WUFI writes them when not the PHPP defaults 0.6 / 0.9) | **Fixed 2026-10-24.** METr's own defaults are 0.4 / 0.9 (`def.absEC` help text), so the writer keeps them at the PHPP defaults and overrides only when the assembly differs, the same rule as the WUFI writer. Elizabeth St: 4 components now at 0.7 |
| `_PhxZone` / `_zone_design_conditions` | `tAttZ 0`, `TRedUD 1.0` | `attached_zone_type`, `attached_zone_reduction_factor` | Gap. Only matters for attached zones |
| `_PhxZone` | `grossVolZ.sel 7`, `netVolZ.sel 6`, `flAreaZ.sel 6` | `volume_gross_mode`, `volume_net_mode`, `weighted_floor_area_mode` | Gap. Matches Elizabeth St's modes by luck |
| `_PhxZone` | `shCapZ.iV 0` (always `val[0]` = 60 Wh/m²K) with `sel` from the model | `specific_heat_capacity`, `specific_heat_capacity_wh_m2k` | Suspect for mixed/heavy or user-defined capacity; not tested |
| `_PhxElectricalDevice` | `refED` 7 / 6 / 4 | `reference_energy_norm` | OK in the Phius scope (§2) |
| Components | `inclC 90`, `azimN 180`, `orient 1` | polygon geometry | Probably recomputed from `lPoly` (METr fills polygon `azimN`); not verified |
| Apertures, foundations, DHW recirculation | type defaults | | OK: overridden from the model per type |

## 5. Reference case: 2626 Elizabeth St

- METr JSON: `~/Dropbox/bldgtyp/2626 Elizabeth St/15_METr/Elizabeth_St_Apartments_261024.json`
- Matching WUFI-Passive XML of the same model: `…/13_WUFI/Elizabeth_St_Apartments_261024.xml`
- Source HBJSON: `…/14_HBJSON/Elizabeth_St_Apartments_261024.hbjson`. To reproduce Ed's export
  from the CLI, pass the merge flags (positional, after the output dir: `group_components`,
  `merge_faces`, `merge_spaces_by_erv`, `merge_exhaust_vent_devices`):
  `.venv/bin/python PHX/hbjson_to_metr_json.py <hbjson> <name> <out_dir> True True True False`.
  The defaults (no ERV merge) give 17 rooms instead of 1 and a different polygon set, which
  buries the real change in a diff.
- 1 variant, 1 zone, 6 assemblies, 22 materials, 1 window type, 63 components, 764 polygons.
- METr results after the shading calc (2026-10-24, IP): heating demand 9.52 kBtu/ft²yr,
  cooling demand 3.02, heating load 7.04 Btu/hr ft², cooling load 1.48, source energy
  2084 kWh/person yr, site energy 11.48 kBtu/ft²yr.
- After the fridge Day/Year fix: heating 8.63, cooling 3.64. After the mixed-layer fix as
  well: heating 9.4 kBtu/ft²yr, heating load 7.3 Btu/hr ft², cooling load 1.65. After the
  exterior absorptance fix (0.4 → 0.7 on 4 components): heating 9.12, cooling 3.79,
  heating load 7.34, cooling load 1.74.
- Warnings: DHW distribution missing inputs, fresh-air supply 1365.9 cfm vs 1161 cfm required,
  overheating 32 %, ACH50 0.85.
- Window `Passive_House`: PHX writes `Ufr = Uw = 1.578` to **both** METr and WUFI (WUFI
  `U_Value_Frame` = `U_Value`, with per-edge `Frame_U_*` = 1.3). So the value comes from the
  PHX model, not the METr writer. Not yet checked whether METr's 2.396 is right.
