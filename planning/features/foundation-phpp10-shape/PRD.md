# PRD — Foundation model shape for PHPP 10.x `Ground`

**Status:** Scoped — 2026-08-15
**Umbrella:** [`README.md`](README.md)

## 1. Problem

The foundation model in honeybee-ph and PHX is WUFI-shaped. It carries what
WUFI-Passive's `FoundationInterface` needs and nothing PHPP 10.x's `Ground`
worksheet asks for beyond that. Two consequences:

- The PHX `Ground` writer (`05`) can only leave several PHPP inputs at the blank
  template's defaults "and say so" — an export that silently describes a
  different building on those cells.
- OpenPH cannot build a PHPP-faithful ground object for any type but heated
  basement, and even that one had to be authored as a fiction (heated basement
  at zero depth) for a slab-on-grade case, which PHPP then rejected. See the
  OpenPH packet for the −18 % that produced.

The fix is upstream: make the model PHPP-complete, then let the writer and the
solvers read it.

## 2. Sources compared

- **PHPP 10.6** blank template, `Ground!C17:S44` labels and formulas
  (`sample_files/_blank_phpp_v10-6/PHPP_EN_V10.6_Empty.xlsx`, read with openpyxl
  2026-08-15), cross-checked against `phi-rules`
  `rulesets/phpp-10-r1/manual/P17-ground.md` §17.1–17.6 and the `05` cell map.
- **PHX** `PHX/model/ground.py`, `from_WUFI_XML/wufi_file_schema.py::WufiFoundationInterface`,
  `to_WUFI_XML/xml_schemas.py::_Phx*` foundation schemas.
- **honeybee-ph** `honeybee_ph/foundations.py`.

## 3. Field-by-field gap

Legend: ✓ present · ≈ derivable exactly · ✗ **missing** · — not a model input
(PHPP takes it from `Areas`/`Climate`, or it is a formula).

### 3.1 Shared inputs (all types)

| PHPP cell | Meaning | honeybee-ph / PHX source | |
|---|---|---|---|
| `H9` | soil conductivity λ [W/mK] | `PhxSite.ground.ground_thermal_conductivity` | ✓ |
| `H10` | soil heat capacity ρc [**MJ/m³K**] | `ground_density × ground_heat_capacity / 1e6` (PHX stores kg/m³ and J/kgK) | ≈ |
| `H18` / `P18` | floor slab / basement ceiling area, U | `=Areas!L18` / `=Areas!P18` (formulas). The foundation's own `floor_slab_area_m2` / `floor_slab_u_value` are WUFI inputs only | — |
| `H19` | exposed perimeter P | `floor_slab_exposed_perimeter_m` (crawlspace: `crawlspace_floor_exposed_perimeter_m`) | ✓ |
| `P19` | Ψ·l floor-slab TBs | `=Areas!AU25` | — |
| `H48` | phase-shift override [months], *optional expert input* | none | ✗ (deliberately not adding — see §6) |
| `H53` / `H54` | groundwater depth [m], flow [m/d] | `PhxSite.ground.depth_groundwater` / `flow_rate_groundwater` | ✓ |

### 3.2 Slab on grade (`C24`)

| PHPP cell | Meaning | Source | |
|---|---|---|---|
| `H25` | perimeter insulation width (horizontal) / depth (vertical) D | `perim_insulation_width_or_depth_m` | ✓ |
| `H26` | perimeter insulation thickness dn | `perim_insulation_thickness_m` | ✓ |
| `H27` | perimeter insulation conductivity λn | `perim_insulation_conductivity` | ✓ |
| `P25` / `P26` | orientation horizontal / vertical (`P26` derives from `P25`) | `perim_insulation_position` (`HORIZONTAL`/`VERTICAL`; PHX also has `UNDEFINED`) | ✓ |
| **`H28`** | area of interior wall towards heated space, AwI [m²] | none | **✗** |
| **`P28`** | U-value of that interior wall, UwI [W/m²K] | none | **✗** |

### 3.3 Heated basement (`C30`)

| PHPP cell | Meaning | Source | |
|---|---|---|---|
| `H31` | area of basement wall below ground, Awb [m²] | `floor_slab_exposed_perimeter_m × slab_depth_below_grade_m` — PHX/WUFI carry the **depth**; PHPP wants the **area** and recovers z = Awb/P itself, so the round-trip is exact for a uniform depth | ≈ (see §6 open question) |
| `P31` | U-value wall below ground, Uwb | `basement_wall_u_value` | ✓ |

PHPP requires `H31 > 0` **and** `P31 > 0` (`Ground!S31` flags "Data missing" and
the detailed calc is dropped otherwise). A model with `slab_depth_below_grade_m
= 0` is therefore not exportable as a heated basement — the writer must refuse,
and honeybee-ph/PHX validation should say so.

### 3.4 Unheated basement (`C33`)

| PHPP cell | Meaning | Source | |
|---|---|---|---|
| `H34` | area of basement wall **above** ground, AW | `perimeter × basement_wall_height_above_grade_m` | ≈ |
| `P34` | U-value wall above ground, UW | `basement_wall_uValue_above_grade` | ✓ |
| `H35` | area of basement wall **below** ground, Awb | `perimeter × slab_depth_below_grade_m` | ≈ |
| `P35` | U-value wall below ground, Uwb | `basement_wall_uValue_below_grade` | ✓ |
| **`H36`** | area of interior wall towards heated, AwI | none | **✗** |
| **`P36`** | U-value of that wall, UwI | none | **✗** |
| `H37` | air change rate of the unheated basement n [1/h] | `basement_ventilation_ach` | ✓ |
| `P37` | U-value of the basement floor slab, Ufb | `floor_slab_u_value` | ✓ |
| `H38` | air volume of the basement V [m³] | `basement_volume_m3` | ✓ |
| (`H18`/`P18`) | basement **ceiling** area/U | from `Areas` group B; model's `floor_ceiling_area_m2` / `ceiling_u_value` are WUFI-only | — |

### 3.5 Suspended floor above ventilated crawl space (`C40`)

| PHPP cell | Meaning | Source | |
|---|---|---|---|
| `H41` | U-value crawl space (ground/floor of the crawl space), UCrawl | `crawlspace_floor_u_value` | ✓ |
| `P41` | area of ventilation openings εP [m²] | `crawlspace_vent_opening_are_m2` (sic) | ✓ (typo, §5) |
| `H42` | height of crawl-space wall h [m] | `crawlspace_wall_height_above_grade_m` | ✓ |
| `P42` | wind velocity at 10 m, v [m/s] (template default 4) | `PhxSite.climate.avg_wind_speed` (default 4.0) — **confirm same quantity** (WUFI "AverageWindSpeed" is annual mean at station height?) before wiring | ≈? |
| `H43` | U-value crawl-space wall, UW | `crawlspace_wall_u_value` | ✓ |
| **`P43`** | wind shield factor fW (0.02 protected / 0.05 average / 0.10 exposed; template default 0.05) | none | **✗** |
| **`H44`** | area of interior wall towards heated, AwI | none | **✗** |
| **`P44`** | U-value of that wall, UwI | none | **✗** |
| (`H18`/`P18`) | ceiling above crawl space area/U | from `Areas`; `crawlspace_floor_slab_area_m2` / `ceiling_above_crawlspace_u_value` are WUFI-only | — |

### 3.6 What "interior wall towards heated" is

PHPP manual §17.2/17.4/17.5 (`P17-ground.md` L137, L182): *"AwI: area of an
interior wall toward another heated part of the building; UwI: U-value of that
interior wall."* Workbook mechanics: `Ground!H51 = P18 + (P19 + IF(C24="x",
H28*P28, 0) + IF(C33="x", H36*P36, 0) + IF(C40="x", H44*P44, 0)) / H18` — the
pair adds a conductance `A·U` into the effective floor U used by the ISO 13370
chain. It exists for the multi-section cases of §17.6 (a heated part of the
building adjoining this section through an interior wall). Single-section
buildings leave it blank; PHPP treats blank as 0. So the model default is
`0.0` / `0.0` (or `None`), and the field is optional in every UI.

## 4. Required model changes — honeybee-ph (primary), schema, Grasshopper

Names follow the existing `*_m2` / `*_u_value` conventions in
`honeybee_ph/foundations.py`.

| Class | New attribute | Type / default | Serialisation |
|---|---|---|---|
| `PhSlabOnGrade` | `interior_wall_to_heated_area_m2` | `float = 0.0` | `to_dict`/`from_dict` |
| `PhSlabOnGrade` | `interior_wall_to_heated_u_value` | `float = 0.0` | " |
| `PhUnheatedBasement` | `interior_wall_to_heated_area_m2` | `float = 0.0` | " |
| `PhUnheatedBasement` | `interior_wall_to_heated_u_value` | `float = 0.0` | " |
| `PhVentedCrawlspace` | `interior_wall_to_heated_area_m2` | `float = 0.0` | " |
| `PhVentedCrawlspace` | `interior_wall_to_heated_u_value` | `float = 0.0` | " |
| `PhVentedCrawlspace` | `wind_shield_factor` | `float = 0.05` (PHPP default; manual Table 12 values 0.02 / 0.05 / 0.10 documented in the docstring — a free float, not an enum, because PHPP accepts any number) | " |

Consider hoisting the `interior_wall_to_heated_*` pair to `PhFoundation` (all
four subclasses would then carry it; heated basement simply never writes it).
Simpler API, one place to document, no per-type duplication — recommended
unless there is a WUFI-side reason to keep the heated basement free of it.

Also fix while here (each is small, none is behaviour-neutral, list them in the
release notes):

- **Defaults imply insulation.** `PhSlabOnGrade` defaults to
  `0.300 / 0.050 / 0.04` — a slab authored with no perimeter insulation must
  explicitly zero three fields or it exports one. Decide: keep (WUFI parity)
  or change to `0.0 / 0.0 / 0.0` = "none". Ed's call (§6).
- `PhVentedCrawlspace.crawlspace_floor_exposed_perimeter_m` defaults to `2.5`
  (looks copied from a *depth* default). Should be `0.0` like the others.
- Naming: `crawlspace_vent_opening_are_m2` (typo), `basement_wall_uValue_*`
  (camelCase). Renames are breaking for HBJSON files in the wild — do them
  with `from_dict` accepting the old key for one minor series, or leave and
  note. Not blocking.

`honeybee-ph-schema`: mirror the fields on the foundation schemas; regenerate
docs. `honeybee_grasshopper_ph`: `honeybee_ph_rhino.gh_compo_io.foundations_create.get_component_inputs`
adds the per-type inputs (optional, defaulted). The GH `HBPH - Create
Foundation` component builds its input list dynamically from that map, so no
component-file change beyond the version pin.

## 5. Required model changes — PHX

- `PHX/model/ground.py`: the same attributes on `PhxSlabOnGrade`,
  `PhxUnHeatedBasement`, `PhxVentedCrawlspace` (or on `PhxFoundation` if
  hoisted). Same defaults.
- `from_HBJSON/create_foundations.py` copies every public attribute
  generically — verify the new ones flow through and add a test that asserts
  each new field survives HBJSON → PHX for all four types.
- `to_WUFI_XML/xml_schemas.py`: no WUFI target for any of the new fields —
  write nothing; comment says why. `from_WUFI_XML/phx_schemas.py`: leave
  defaults.
- **Set `_foundation_type_num` in each subclass `__init__`** (today all four
  report `FoundationType.NONE` when constructed directly — `05` Phase 2 flags
  it). The subclass is the discriminator; the enum should agree with it.
- Fix the `crawlspace_floor_exposed_perimeter_m` naming asymmetry only if
  honeybee-ph does (keep the two in lock-step).
- Docs: `docs/reference/phx-model-reference.md` foundation tables gain the
  fields with the PHPP cell each maps to; `05`'s "No PHX source exists" list
  shrinks to `H48` only.

## 6. Open decisions (Ed)

1. **Below-grade wall area: derived or explicit?** PHPP wants `Awb` (area);
   WUFI wants depth. `Awb = P × z` is exact for a uniform depth and PHPP itself
   recovers `z = Awb/P`, so derivation round-trips. A stepped or partial
   basement (§17.6 examples) is where an explicit `basement_wall_area_below_grade_m2`
   override would matter. Recommendation: **derive by default; add an optional
   explicit area (`None` = derive)** only if a real project needs it — file it,
   don't build it yet.
2. **Slab perimeter-insulation defaults**: keep WUFI parity (`0.3/0.05/0.04`)
   or move to "none" (`0/0/0`)? Recommendation: **"none"** — a default that
   silently adds insulation is the same class of trap as the PHPP template
   defaults this whole family of packets is about; WUFI parity is not worth a
   phantom 30 cm of XPS.
3. **`H48` phase-shift override**: leave out (recommended — an expert override
   with no WUFI counterpart and no PHPP guidance beyond "optional").
4. **Hoist `interior_wall_to_heated_*` to the base class** or keep per type?
   Recommendation: hoist.

## Hand-off to OpenPH — required on completion

OpenPH's foundation objects (its packet Phase 03) are blocked on this shape and
will be built from whatever ships here. When the honeybee-ph, schema, GH and
PHX halves are **done and released**, write a **new** doc — do not just edit
this packet — at

```
openph-workspace/planning/features/ground-degree-hours-alignment/upstream/phx-foundation-phpp10-shape.md
```

(if that packet has been archived, put it in the archived folder's `upstream/`
and note it in `openph-workspace/planning/STATUS.md` or the successor packet).
Front matter `DATE`/`STATUS`/`SCOPE`/`RELATED`; contents:

- Released versions to pin: `honeybee-ph`, `honeybee-ph-schema`,
  `honeybee_grasshopper_ph`, `PHX`.
- **The shape as shipped**, per foundation class: every attribute name, type,
  unit, default, and JSON key — including the ones that already existed, so
  OpenPH has one authoritative table and does not read the WUFI-era docstrings.
  State explicitly which of PRD §6's four decisions Ed took (derived vs explicit
  wall area; slab insulation defaults; `H48`; hoisted or per-type interior-wall
  pair) and what the resulting defaults are.
- The PHX → PHPP `Ground` cell map **as implemented** in `05` (attribute → cell
  per type, the derived quantities `H10/H31/H34/H35` with their unit
  conversions, the selector cells and how siblings are cleared, `P42`'s
  source), and which cells PHX still leaves at template default (expected:
  `H48` only).
- Validation behaviour: what raises (heated basement with `z ≤ 0` /
  `U_wall ≤ 0`; unsupported types; `len(foundations) > 1`) and the messages.
- `_foundation_type_num` now set by subclasses (or not — say which).
- Any deviation from `PRD.md` §4–5, and why.
- Test names in each repo that pin the fields and the writer, so OpenPH can
  cite them.
- What OpenPH must do next (in its own words is fine): build the four
  `OpPhFoundation*` classes on these fields; retire `tools/write_native_reference_phpp.py::_write_ground`;
  regenerate the `native_reference` pair with the PHX writer.

Then update `openph-workspace/planning/features/ground-degree-hours-alignment/STATUS.md`
"Blockers" to point at the new doc. That folder's `upstream/README.md`
describes the same expectation from the OpenPH side.

## 7. Acceptance

- honeybee-ph, schema, GH and PHX all carry the seven new inputs with the same
  names, types, units and defaults; HBJSON round-trips them; PHX receives them.
- `05`'s writer maps `H28/P28`, `H36/P36`, `H44/P44`, `P43` from the model,
  and its "no PHX source" list is down to `H48`.
- A heated basement with zero below-grade depth is refused at export with a
  message naming `Ground!S31`.
- OpenPH can construct all four ISO 13370 objects from the PHX model without
  inventing a value.
