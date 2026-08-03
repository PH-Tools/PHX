# Research — Psi-Install across the tool chain

```
DATE:    2026-08-03
TIME:    10:48
STATUS:  Research complete — code survey of all four package repos + PHN + rules corpus
AUTHOR:  Ed + Claude
SCOPE:   Reference only. How psi-install is stored/flows today in honeybee_ph, PHX,
         honeybee_grasshopper_ph(+), and PH-Navigator; program default values; gaps.
RELATED: README.md (router), PRD.md (draft design), STATUS.md
```

Everything below was verified against source on 2026-08-03. File:line references
are to the repos under `~/Dropbox/bldgtyp-00/00_PH_Tools/`.

---

## 1. What the programs actually require (default values)

### Phius (2024-r1 corpus, guidebook §1.4.4.6, pp. 66–74)

Verified against `bldgtyp/phius-rules/rulesets/phius-2024-r1/guidebook/1.4.4.6-visualized-components.md`
and `checklists/windows.md`:

| Condition | Ψ-install (IP, Btu/hr·ft·°F) | ≈ SI (W/m·K) |
| --- | --- | --- |
| **Default** (flange-mounted / unknown) | **0.030** | **0.052** |
| Mid-wall mounted, not over-insulated | 0.020 | 0.035 |
| Mid-wall mounted, over-insulated | 0.015 | 0.026 |
| Lower values | only with TB calc (manufacturer value or THERM per the **Phius Psi-Install Modeling Protocol**, §1.4.2.6) | — |
| **Mulled sides** | **0** | **0** |

Two WUFI methods for mulled units (§1.4.4.6): (1) uncheck "From window parameters"
and enter 0 on the mulled sides, typical psi-install on the others; or (2) modify
the frame's frame-to-wall psi parameter for that window type. Exception: a mull
connector substantially more conductive than the frame needs its own TB calc.

**Consequence: the 0.04 W/mK default baked through our whole stack is NOT the
Phius default.** Phius' sanctioned default is ≈0.052 W/mK, with the lower tiers
only for specific mounting conditions.

### PHI / PHPP

PHPP has no built-in default — every window edge gets an installation-situation
toggle (0/1) plus a Ψ-install value. **0.04 W/mK is the conventional conservative
planning value** in PHI practice (and the PHI "certified installation" benchmark
figure), which is why it is the default in honeybee_ph, the GH plugins, and V0.
PHI retrofit (EnerPHit) work generally requires project-specific calculated
values (Flixo) for most install conditions. *(No corpus citation — PHI guidance
is not in phius-rules; treat 0.04 as "legacy stack convention + PHI planning
practice", verify against PHPP manual if a citation is ever needed.)*

### Default-policy takeaway

The project default should be **program-aware**: Phius projects → 0.052 W/mK
(0.030 IP), PHI projects → 0.04 W/mK. A single hard-coded 0.04 is wrong for
Phius submissions.

---

## 2. honeybee_ph — the data model of record

Repo: `honeybee_ph`. Everything lives in
`honeybee_energy_ph/construction/window.py`.

- **`PhWindowFrameElement.psi_install`** — float, W/m·K, **default 0.04**
  (`window.py:36`; docstring `:21`). One element per side.
- **`PhWindowFrame`** holds four named elements `top/right/bottom/left`
  (`window.py:106-127`); `.elements` iterates **T, R, B, L** (`:127`).
- **Ownership: the frame belongs to the *window construction*, not the aperture**:
  `Aperture.properties.energy.construction.properties.ph.ph_frame`
  (`honeybee_energy_ph/properties/construction/window.py:25`; parallel copy on
  `windowshade.py:26`). Two apertures sharing a `WindowConstruction` share the
  same four psi-install values.
- **Granularity: per (construction × edge)** — 4 independent floats per window
  type. There is **no per-aperture or per-instance value**.
- **No install on/off flags exist anywhere** (`install_l/r/t/b`, "installed",
  "mull*" — zero hits). The *only* way to express a mulled/non-installed edge is
  `psi_install = 0.0` on that edge.
- The only aperture-level "install" attribute is geometric:
  `AperturePhProperties.install_depth` (`honeybee_ph/properties/aperture.py:83`,
  0.1016 m = 4 in; note `from_dict` fallback is 0.1 at `:141` — minor
  inconsistency).
- **Serialization** round-trips losslessly (`window.py:41-65`), but `from_dict`
  reads `_input_dict["psi_install"]` as a required key (`:61`) — legacy HBJSON
  without it raises `KeyError`.
- **U-w consumption**: `honeybee_ph_utils/iso_10077_1.py` —
  `side_psi_install_heat_lost = psi_install × side_exterior_length` (`:220-223`),
  where side length is the full width/height (`:166-175`). Every edge always
  counts; no edge can be skipped. Uw = (glazing + frame + Ψg + Ψinstall)/area
  (`:264-276`). Tests exercise the mulled pattern by zeroing one side at a time
  (`tests/test_honeybee_ph_utils/test_iso_10077_1.py:71-116`).

---

## 3. PHX — HBJSON → WUFI / PHPP / METr / PPP

Repo: `PHX`. The value is faithfully per-edge through the whole pipeline, always
riding on the **window type**, never the aperture instance.

### 3.1 Read (HBJSON → PHX)

- `from_HBJSON/create_assemblies.py:406` — baseline
  `set_all_frames_psi_install(0.0)`, then per-edge copy from the HBPH frame
  (`:328/:335/:342/:349`). **PHX's default is 0.0, not 0.04** — a plain HB
  `WindowConstruction` without a PH frame silently lands at 0.0.
- `PhxWindowFrameElement.psi_install: float = 0.00` (`model/constructions.py:603`).
  "Unset" is represented as `0.0` — no None/sentinel.
- `create_assemblies.py:363` — `u_value_window` is computed via ISO 10077-1 on
  the fixed 1.23×1.48 m standard window and is therefore
  **psi-install-inclusive**, while the per-edge values are *also* exported
  separately (mostly self-correcting because `use_detailed_uw = True` lets
  WUFI/PHPP recompute).
- Aperture side: exactly one `PhxApertureElement` per HB Aperture, geometry +
  shading only — **no psi and no install flags at element level**
  (`from_HBJSON/create_building.py:200-217`).

### 3.2 Write — WUFI-XML

- `to_WUFI_XML/xml_schemas.py:892-907` — `Frame_Psi_Left/Right/Top/Bottom` on
  the **WindowType** element (W/m·K). No install *lengths* are written — WUFI
  derives install perimeter from the exported polygon geometry, so **mulled
  sashes exported as separate elements each contribute their full perimeter**
  unless the psi on the shared edge is 0.

### 3.3 Write — PHPP

- Components sheet: `PHPP/phpp_model/component_frame.py:164-182` writes per-edge
  psi-install; PHPP 10.x localizations map left+right to one shared column →
  values sharing a column are **arithmetically averaged** (weights machinery
  exists but always resolves to 1.0 — see bug list).
- Windows sheet: `PHPP/phpp_model/windows_rows.py:89-99` writes the raw psi
  value per edge, with in-code TODO `:89` "Install condition, not Psi-Install" —
  PHPP's window-row columns are an install-*situation* selector, not a psi cell.
- One `WindowRow` per aperture polygon, all reading the shared
  `window_type` (`phpp_app.py:492-527`) — every instance of a type gets
  identical psi-installs.

### 3.4 Write — METr-JSON

- `to_METr_JSON/metr_schemas.py:237-242` — `"lrtbFrPsi": [top, right, bottom,
  left]` on the window type (key says lrtb, array is filled TRBL — see bug
  list). Component-level override array exists but is always written as NaN
  (= "use type value") at `:655`.

### 3.5 Write — PPP

- `to_PPP/ppp_schemas.py:703-707` — single **unweighted average** of the 4 edges
  per frame row; install-situation columns left empty (`:693`);
  `Fenster_Einbau` per-edge flags hard-coded `"1"` for every window (`:477-481`).

### 3.6 PHX/upstream bug list found during this survey (not this feature's scope, worth filing)

1. `PHX/from_WUFI_XML/phx_schemas.py:284-290` — `frame_data_bottom` reads the
   `*_Top` XML fields; bottom frame is a copy of top on every WUFI-XML import.
2. PHPP localizations `EN_10_6.json` vs `EN_10_6IP.json` (also 10_4A/10_4IP) —
   `psi_i_bottom`/`psi_i_top` columns swapped between the SI and IP variants of
   the same PHPP version (Components §589-608 and Windows §725-739 sections).
3. `windows_rows.py:90-99` — psi-install written with no unit conversion; IP
   PHPP files receive raw SI W/m·K numbers in the Windows sheet (Components
   sheet does convert).
4. `component_frame.py:179-182` + `phpp_app.py:329-334` — psi-install column
   averaging is always unweighted (weights dict only ever carries `psi_g_*`
   keys).
5. `metr_schemas.py:219-242` — all `lrtb*` arrays populated in T,R,B,L order
   despite the l,r,t,b key name.
6. `ppp_schemas.py:663-672` — `_frame_dedup_key` omits psi_install/psi_glazing;
   distinct frame types can collapse into one PPP entry.
7. `honeybee_ph window.py:61` — `psi_install` required key in `from_dict`, no
   legacy fallback.
8. `win_set_psi_install_values.py:186-200` (GH) — per-aperture psi assignment
   writes into a construction shared across apertures (aliasing hazard).

---

## 4. Grasshopper plugins

### 4.1 honeybee_grasshopper_ph (authoring side)

Three components write `psi_install`, all per-edge onto `PhWindowFrameElement`:

| Component | Impl | Notes |
| --- | --- | --- |
| `HBPH - Create PH Window Frame Element` | `gh_compo_io/apertures/win_create_frame_element.py:34` | default 0.04 validator |
| `HBPH - Set Aperture Psi-Installs` | `win_set_psi_install_values.py:194-197` | DataTree: branch=aperture group, item=edge (T/R/B/L); **aliasing hazard** — writes into the shared construction |
| `HBPH - Set HB-Construction Psi-Installs` | `win_set_hb_const_psi_install_values.py:104-108` | duplicates the construction properly; **not registered in `_component_info_.py`** (gap) |

No component sets per-edge install *flags* — none exist in the model.

### 4.2 honeybee_grasshopper_ph_plus (PH-Nav client, "Get Apertures", route 3)

`honeybee_ph_plus_rhino/gh_compo_io/ph_navigator/v1/window_types_schema.py`:

- `FrameType.psi_install_w_mk` parsed null-safe with **0.04 fallback**
  (`:167`, helper `_as_float` `:24-29`). This fallback is exactly the gap this
  feature closes (project 2524: 196 nulls across 27 types).
- Build pipeline (`v0/window_types_get.py`):
  - Each PH-Nav grid element becomes its own `PhWindowFrame` +
    `WindowConstruction` named `"{type}_C{col}_R{row}"` (`:112-133`), with four
    independently-sourced edge elements. **The per-mullion-cell structure the
    mulled-edge rule needs already exists on the client side.**
  - ⚠️ **Frame elements are deduped by frame-type *name*** (`:93-94,:107`) — all
    edges/apertures using frame product "X" share ONE `PhWindowFrameElement`,
    hence one psi_install. **If PHN starts emitting per-edge values that vary by
    location, this dedup breaks them.** The client must apply psi per-edge
    *after* dedup (or stop deduping) — a required client change, record it in
    the export contract.
- Precedent worth copying: the AirTable path
  (`gh_compo_io/airtable/create_window_constructions.py:99-107, 230, 247-260`)
  already implements a **named psi-install lookup**: a `{name: value}`
  dictionary from a psi-install table, applied per edge via
  `PSI-INSTALL-{TOP|RIGHT|BOTTOM|LEFT}-NAME` linked fields (fallback 0.0). This
  is precisely the "install-detail types applied per edge" model the PRD
  proposes, proven in production on the AirTable workflow.

---

## 5. PH-Navigator today

### 5.1 Where psi-install already lives

- **`ProjectFrame.psi_install_w_mk: float | None`** —
  `backend/features/project_document/envelope_models.py:412` (and `FrameRef`
  `:110`). Nullable; effectively never set (the origin of the 196 nulls).
- **Firm catalog**: `catalog_frame_types` SQL table has a `psi_install_w_mk`
  column (`backend/features/catalogs/frame_types/models.py:47,94,124`); the
  **catalog Frame Type create modal is the only data-entry point in the entire
  app today** (`frontend/src/features/catalogs/components/FrameTypeCreateModal.tsx:245-246`).
- **Route 3 emission**: `backend/features/gh_api/aperture_types_export.py:147`
  emits `frame_type.psi_install_w_mk` per element-side frame block (sides dict
  keyed top/right/bottom/left at `:104-116`).
- **Display**: U-Values report already shows per-edge Ψ-install
  (`UValueReportPanel.tsx:389`, `ApertureEdgeBreakdown.psi_install_w_mk` in
  `aperture_u_value/models.py:66`) and the Frames spec report has a Ψ-install
  column (`ApertureSpecReportPanel.tsx:738-753`). Note Ψ-install is
  deliberately excluded from the PHN U-w calc (`aperture_u_value/service.py:12-14`).

### 5.2 Why `ProjectFrame` is the wrong home for the real feature

`ensure_project_frame` dedupes frame rows by catalog product
(`aperture_commands/handlers/picks.py:61`): a head, sill, and jamb using the
same frame product resolve to the **same `pfrm_*` row**. A psi-install stored
there cannot express "head differs from sill", let alone "this particular
aperture's sill". Per-edge values need a home on the element-side slot
(`ApertureElementFrames` is already 4-sided, `envelope_models.py:488-497`) or an
assignment to a separate install-type table.

### 5.3 Ready-made building blocks (verified)

- **Unused per-edge click seam**: `ApertureCanvasOverlay.tsx` already renders a
  hit target per element-side and threads `onRegionClick?(elementId, region)`
  (`:39,:53,:129`) — declared, tested, and **never passed by any production
  caller**. A per-edge interaction can be added without inventing new events.
- **Empty metric cell**: `FrameRow.tsx:76-78` — the element card's per-side row
  has a hardcoded `-` third cell, an obvious display home for effective
  Ψ-install.
- **Reusable elevation drawing**: `ApertureSvgCanvas.tsx` + pure
  `aperture-geometry.ts::elementRegionsMm` (`:111-147`) already compute and draw
  the four frame strips per element — a read-only "key view" in a modal is
  cheap.
- **Table recipe**: `thermal_bridges` is the exact template — typed columns +
  custom fields, `pdf_report_asset_ids` PDF-only attachment
  (`assets/registry.py:121-130`, `_attachment_fields.py`), status field,
  `focus=` deep links. New attachment fields must pass the reachability guard
  (`test_attachment_reachability_guards.py`); **aperture rows are currently NOT
  walkable by the attachment registry** (`assets/registry.py:293-313`) — a
  separate project-level table is far cheaper than attaching PDFs to aperture
  elements.
- **Status page**: one `StatusSummaryTable` entry
  (`status_summary.py:168-220`) + one destination kind + one branch in
  `frontend .../project_status/summary.ts:72-92`.
- **Documentation page gap**: only `datasheet_*` and `photo_*` axes are
  tracked (`documentation_summary.py:36-44, 393-396`) — `pdf_report_asset_ids`
  is invisible there today (same gap as thermal bridges). Decide: extend the
  axes, or accept Status-only tracking (TB precedent).
- **Schema bump**: current document `schema_version = 9` (`document.py:228`);
  new table/field ⇒ v9→v10 in `migrations/upgrade.py` + `templates.py` seed +
  `_validators.py` + `document_validation.py` + `downloads.py` +
  `gh_api/tables_export.py`.

### 5.4 Mulled units in PHN

No first-class mull concept. A mulled unit is a grid (`row_heights_mm ×
column_widths_mm`) of elements; the mullion is implicit — two abutting frame
strips. `ProjectFrame.mull_type` (`envelope_models.py:405`, seeded options
OP-to-OP / OP-to-FX / FX-to-FX) is a descriptive product attribute; the only
mull-aware logic is the `mullion_frame_at_void_boundary` warning
(`aperture_u_value/service.py:445-465`). **No helper yet classifies an
element edge as perimeter (wall-abutting) vs interior (mullion)** — but the
grid geometry (`row_span`/`column_span` + the mm arrays) makes it a pure
function on both sides (backend `_element_width_m`-style helpers, frontend
`aperture-geometry.ts`).

---

## 6. Cross-package contract summary (the shape the feature must satisfy)

```
PHN (per aperture-type, per element, per side: effective Ψ-install)
  → route 3: element.frames.{side}.psi_install_w_mk (effective value, incl. 0 on mull edges)
  → GH client: per-cell PhWindowFrame; MUST stop sharing PhWindowFrameElement.psi_install
    across dedup (client change required)
  → honeybee_ph: PhWindowFrameElement.psi_install per edge (model of record)
  → PHX: PhxConstructionWindow.frame_{side}.psi_install per window type
  → WUFI: Frame_Psi_{side} per WindowType (mull edges must carry 0)
  → PHPP: per-edge install psi columns (10.x: L/R share a column, averaged)
  → METr: lrtbFrPsi array per type
```

Granularity ceiling: downstream, psi-install always rides on the **window
type**, keyed per edge. PHN's aperture *types* map 1:1 onto that (each grid
cell → its own construction), so per-(aperture-type × element × side) in PHN is
exactly the granularity the pipeline can carry. Per-placed-instance (Rhino)
overrides remain a GH-side concern (`HBPH - Set Aperture Psi-Installs`).
