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
fridge types. The dishwasher (7), washer (6) and dryer (4) `refED` values are still
hardcoded and not yet checked against the model's norm.

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
| `lAssembly[]` | Recomputes `tRes` and adds `U`. **Open question:** ours 6.99 → METr 7.86 (m²K/W) on Elizabeth St; a film difference would be about 0.17, not 0.87 |
| `lWindow[]` | Rounds `Uw`/`frF`. **Recomputes `Ufr`** (ours 1.578 → 2.396 on Elizabeth St; see §4) |

## 4. Reference case: 2626 Elizabeth St

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
- Warnings: DHW distribution missing inputs, fresh-air supply 1365.9 cfm vs 1161 cfm required,
  overheating 32 %, ACH50 0.85.
- Window `Passive_House`: PHX writes `Ufr = Uw = 1.578` to **both** METr and WUFI (WUFI
  `U_Value_Frame` = `U_Value`, with per-edge `Frame_U_*` = 1.3). So the value comes from the
  PHX model, not the METr writer. Not yet checked whether METr's 2.396 is right.
