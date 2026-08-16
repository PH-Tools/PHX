# The `Ground` worksheet has no writer at all

**Status:** Scoped — largest of the five; its own PR. Single-foundation (building
section 1) only; see *The hard part* below.
**Opened:** 2026-08-15
**Owner:** `PHX/PHPP/` — no owner today; `GROUND` is an unused stub
**Umbrella:** [`README.md`](README.md)
**Filed as:** "Ground / floor-slab type → `Ground` worksheet" (gap 4 of the incoming request)
**Depends on:** [`03`](03-summvent-heat-recovery-mode.md) Phase 2 (the radio-group helper); **and, for
Phase 2 onward, [`features/foundation-phpp10-shape/`](../../features/foundation-phpp10-shape/README.md)**
— the honeybee-ph/PHX foundation model is WUFI-shaped and lacks the "interior wall towards
heated" pairs and the crawl-space wind shield factor that this writer would otherwise leave at
template defaults. Ed's call 2026-08-15: fix the shape upstream first, then write from it.

## Confirmed as filed

```json
"GROUND": { "name": "Ground", "columns": {} }
```

backed by `class ColGround(BaseModel): ...`. No `io_ground.py`, no call in
`write_phx_project_to_phpp`, no writes in the golden fixture. In the blank 10.6,
`C24`, `C30`, `C33` and `C40` are all empty, so nothing is selected and the sheet
computes nothing. On a *populated* starting workbook the example's foundation
survives and computes ground heat loss for a different building.

## The cell map (verified against the blank 10.6)

The corpus (`phi-rules` → `phpp-ground/rules.md`) covers the selectors and the
hidden ISO 13370 calculation core, but **not** the visible type-specific input
rows — which is exactly what a writer needs. Read out of the workbook:

### Column roles, three building sections

| Role | Section 1 | Section 2 | Section 3 |
|---|---|---|---|
| type selector | `C` | `W` | `AQ` |
| left label / symbol / **value** / unit | `D` / `G` / **`H`** / `I` | `X` / `AA` / **`AB`** / `AC` | `AR` / `AU` / **`AV`** / `AW` |
| right label / symbol / **value** / unit | `L` / `O` / **`P`** / `Q` | `AF` / `AI` / **`AJ`** / `AK` | `AZ` / `BC` / **`BD`** / `BE` |

A flat `+20` column offset per section for every role. Confirmed independently by
the `PHPP_Daten_Ankreuzen` validation range, which covers
`C24 C30 C33 C40 P25 W24 W30 W33 W40 AJ25 AQ24 AQ30 AQ33 AQ40 BD25`, and by
`Ground!BG18`, which tests `BD18`.

> **Corpus correction to fold back.** `phpp-ground/rules.md` lists the section-2
> and section-3 floor U-values as `AK18` and `BE18`. Those are the *unit* cells
> (`'W/(m²K)'`); the value cells are `AJ18` and `BD18`.

### Section-1 inputs (add 20 / 40 for sections 2 / 3)

**Shared**

| Cell | Input | Blank default |
|---|---|---|
| `H9` | soil thermal conductivity λ | `2` |
| `H10` | soil heat capacity ρc, **MJ/(m³K)** | `2` |
| `H18` | floor slab / basement ceiling area — `=Areas!L18` | formula |
| `P18` | floor slab / basement ceiling U — `=Areas!P18` | formula |
| `H19` | **perimeter length P** | empty |
| `H48` | phase shifting (optional) | empty |

`H11` (penetration depth), `H20` (characteristic dimension B'), `P9:P15`
(climate), `P19`, `P47`, `P48` are all formulas — never write them.

**Slab on grade — selector `C24`**

| Cell | Input |
|---|---|
| `H25` | perimeter insulation width/depth `D` |
| `H26` | perimeter insulation thickness `dn` |
| `H27` | perimeter insulation conductivity `λn` |
| `P25` | orientation: `"x"` = horizontal (`P26 = IF(P25="x","","x")` derives vertical) |
| `H28` / `P28` | area / U-value of interior wall towards heated |

**Heated basement — selector `C30`**

| Cell | Input |
|---|---|
| `H31` / `P31` | area / U-value of basement wall below ground |

**Unheated basement — selector `C33`**

| Cell | Input | Blank default |
|---|---|---|
| `H34` / `P34` | area / U-value of basement wall **above** ground | empty |
| `H35` / `P35` | area / U-value of basement wall **below** ground | empty |
| `H36` / `P36` | area / U-value of interior wall towards heated | empty |
| `H37` | air change rate of unheated basement | `0.2` |
| `P37` | U-value of basement floor slab | empty |
| `H38` | air volume of basement | empty |

**Ventilated crawl space — selector `C40`**

| Cell | Input | Blank default |
|---|---|---|
| `H41` | U-value crawl space | empty |
| `P41` | area of ventilation openings | empty |
| `H42` | height of crawl space wall | empty |
| `P42` | wind velocity at 10 m | `4` |
| `H43` | U-value crawl space wall | empty |
| `P43` | wind shield factor | `0.05` |
| `H44` / `P44` | area / U-value of interior wall towards heated | empty |

`H95` selects among the four: `IF(C30="x",H74+P47, IF(C24="x",H65+P47,
IF(C33="x",H79+P47, IF(C40="x",H87+P47,""))))`. Note it tests `C30` **first**,
so two ticked boxes resolve to heated basement — clearing siblings is mandatory.

## PHX model → PHPP, with the derivations spelled out

`PhxPhBuildingData.foundations: list[PhxFoundation]`
(`model/certification.py:153`), subclassed in `model/ground.py`. Several PHPP
inputs are **not** direct attribute copies:

| PHPP | PHX source |
|---|---|
| `H9` | `PhxSite.ground.ground_thermal_conductivity` |
| `H10` | **derived**: `ground_density * ground_heat_capacity / 1e6` — PHX stores 2000 kg/m³ and 1000 J/(kgK); PHPP wants MJ/(m³K), so 2.0 |
| `H19` | `<foundation>.floor_slab_exposed_perimeter_m` (all four types carry it, under two different names — crawlspace uses `crawlspace_floor_exposed_perimeter_m`) |
| `H25`/`H26`/`H27` | `PhxSlabOnGrade.perim_insulation_width_or_depth_m` / `_thickness_m` / `_conductivity` |
| `P25` | `PhxSlabOnGrade.perim_insulation_position == HORIZONTAL` |
| `H31` | **derived**: `PhxHeatedBasement.floor_slab_exposed_perimeter_m * slab_depth_below_grade_m` — PHX has no below-grade wall *area* |
| `P31` | `PhxHeatedBasement.basement_wall_u_value` |
| `H34` | **derived**: perimeter × `PhxUnHeatedBasement.basement_wall_height_above_grade_m` |
| `P34` | `basement_wall_uValue_above_grade` |
| `H35` | **derived**: perimeter × `slab_depth_below_grade_m` |
| `P35` | `basement_wall_uValue_below_grade` |
| `H37` | `basement_ventilation_ach` |
| `P37` | `PhxUnHeatedBasement.floor_slab_u_value` |
| `H38` | `basement_volume_m3` |
| `H41` | `PhxVentedCrawlspace.crawlspace_floor_u_value` |
| `P41` | `crawlspace_vent_opening_are_m2` |
| `H42` | `crawlspace_wall_height_above_grade_m` |
| `H43` | `crawlspace_wall_u_value` |
| `P42` | `PhxSite.climate.avg_wind_speed` (PHX default 4.0 = PHPP default) — confirm this is the same quantity before wiring it |

**No PHX source exists today** for the "interior wall towards heated" pairs
(`H28`/`P28`, `H36`/`P36`, `H44`/`P44`) or the wind shield factor `P43`.
**Superseded 2026-08-15:** these are being added to the model upstream
([`features/foundation-phpp10-shape/`](../../features/foundation-phpp10-shape/PRD.md) §4–5);
Phase 2 below maps them from the model. Until that release lands, do not
implement Phase 2 with template defaults.

**No PHPP target exists** for `PhxHeatedBasement.slab_depth_below_grade_m`
(consumed only by the derivation above) or `PhxSlabOnGrade.floor_slab_area_m2` /
`PhxVentedCrawlspace.crawlspace_floor_slab_area_m2` (PHPP takes the area from
`Areas`). That asymmetry is inherent to the PHPP method, not a defect.

## The hard part: more than one foundation

`Ground!H18`/`P18` are **formulas** reading `Areas!L18`/`P18` — the single
group-`B` ("Floor slab / basement ceiling") aggregate that PHX already feeds via
`write_project_opaque_surfaces` (`areas_surface.py` maps `GROUND`-exposed floors
to group 11). Sections 2 and 3 have no such link: `AB18`/`AJ18` and `AV18`/`BD18`
are blank manual inputs.

So a second foundation cannot simply be written into section 2 — its area would
still be inside the group-`B` total that section 1 consumes, and the building
would lose ground heat twice.

**Scope decision — settled 2026-08-15: single foundation only.** Building
section 1, and nothing else. `len(foundations) > 1` raises with a message that
names the limitation, rather than silently writing the first and losing the rest.

Multi-section support is deliberately deferred. It is not a `Ground`-writer
change at all — it requires splitting the `Areas` group-`B` total per foundation
so each section gets its own area and U-value, which is an `Areas`-writer change
plus a `Ground` change plus a decision about how a PHX model expresses "this
floor belongs to that foundation". None of that is in evidence as a real user
need yet; a raise makes the limit visible the first time someone hits it, which
is the cheapest way to find out whether it matters.

Concretely, this drops from scope: the `+20` / `+40` section column offsets (map
them in the shape anyway — Phase 1 — but write only section 1), and the
`AB18`/`AJ18`, `AV18`/`BD18` manual area/U inputs, which exist only for
sections 2 and 3.

## Phases

### Phase 0 — corpus first

`phpp-ground/rules.md` does not carry the type-specific input rows. Add them, fix
the `AK18`/`BE18` → `AJ18`/`BD18` error, and record the `+20` section offset.
Doing this first means the writer is implemented against a reviewed map rather
than against a probe script, and the corpus feedback loop is mandatory under the
`phi-rules` contract.

**Verify:** `.venv/bin/python tools/check_corpus.py rulesets/phpp-10-r1` clean in
the corpus repo.

### Phase 1 — shape

Replace `ColGround` with a real model in `shape_model.py` and populate `GROUND`
in all seven localization JSONs. Structure it as: a `sections` list (three
entries, each carrying its selector/value column letters) plus per-type input
definitions keyed by row offset from a located header. Locate the block by
`"Floor slab type (select only one)"` in the selector column rather than
hardcoding row 22 — every other `sheet_io` module locates by string.

The 9.x shapes need their own inspection; PHPP 9's `Ground` sheet is not the same
layout. If it does not map, leave `GROUND` a stub in `EN_9_*` and have the writer
skip when the shape is absent.

**Verify:** `tests/test_PHPP/test_shape_file.py` passes for all seven files.

### Phase 2 — model layer

`PHX/PHPP/phpp_model/ground_data.py`: one dataclass per foundation type
converting a `PhxFoundation` subclass plus the site's `PhxGround` into an
`XlItem` list, using the radio-group helper from [`03`](03-summvent-heat-recovery-mode.md)
for the type selector and for `P25`. Every derived quantity (`H10`, `H31`, `H34`,
`H35`) gets a comment naming the units on both sides.

Dispatch on the concrete subclass, not on `foundation_type_num`. None of the four
subclasses sets `_foundation_type_num`, so all four report
`FoundationType.NONE` when constructed directly:

```
PhxSlabOnGrade           foundation_type_num = FoundationType.NONE
PhxHeatedBasement        foundation_type_num = FoundationType.NONE
PhxUnHeatedBasement      foundation_type_num = FoundationType.NONE
PhxVentedCrawlspace      foundation_type_num = FoundationType.NONE
```

It is populated only by the readers — `from_HBJSON/create_foundations.py:38` and
`from_WUFI_XML/phx_schemas.py` — and nothing enforces that it agrees with the
class. The subclass is the structurally guaranteed discriminator; the enum is
not. Cheap belt-and-braces: assert the two agree when the enum is not `NONE`,
and raise if they disagree, since a mismatch means an upstream reader is wrong.

Unsupported or bare `PhxFoundation` → raise, per the request's acceptance
criterion 3.

**Verify:** `tests/test_PHPP/test_phpp_model/test_ground_data.py` — one case per
type asserting the full expected `XlItem` set including the three cleared
siblings, plus the `H10` unit conversion and each derived area.

### Phase 3 — IO controller and wiring

`PHX/PHPP/sheet_io/io_ground.py` following `io_ventilation.py`.
`PHPPConnection.__init__` instantiates it. `phpp_app.write_project_ground` reads
`variant.phius_cert.ph_building_data.foundations`, guarded by `if self.easyPh:
return` and the standard `ph_building_data` check, raising on `len > 1`.

`hbjson_to_phpp.write_phx_project_to_phpp`: add the call **after**
`write_project_opaque_surfaces`, since `Ground!H18` reads `Areas!L18` and the
existing sequence already re-calculates after `Climate` to keep locator reads off
error cells.

Zero foundations is normal (a model with no ground contact) — write nothing and
do not raise.

**Verify:** `tests/test_PHPP/test_sheet_io/test_io_ground.py` against the fake XL
framework, one case per type end-to-end.

### Phase 4 — live check against a recalculated workbook

The unit tests prove PHX writes the cells it intends; they cannot prove PHPP then
computes something sensible. Export one model per foundation type into a blank
10.6, recalculate in Excel, and read back `H95` (steady-state conductance) and
`P116` (temperature reduction factor). Both must be numeric, non-zero, and of a
plausible magnitude for the geometry. This is the step that catches a plausible
but wrong cell map.

**Verify:** four workbooks, `H95` and `P116` numeric in all four; record the
values in this file.

### Phase 5 — re-record the replay fixture

Live Excel required. `Single_Zone.hbjson` — check whether it carries a foundation
at all. If it does not, the fixture will not change, and a *second* fixture with a
foundation-bearing HBJSON is needed for regression cover (there is precedent:
`planning/STATUS.md` already tracks an open "aperture-bearing xl-replay golden
fixture" item with the same constraint).

**Verify:** `python -m pytest tests/test_xl_replay/` green.

### Phase 6 — closeout

`python -m pytest tests/`. Fold the mapping into
`docs/reference/phx-model-reference.md` (the PHX→PHPP mapping tables) and
`docs/dev/exporter-patterns.md`. Record the Phase 4 numbers. Update
[`README.md`](README.md) and `planning/STATUS.md`.

**Hand-off to OpenPH (required).** This writer is what regenerates OpenPH's
`native_reference` PHPP workbook once its `tools/write_native_reference_phpp.py::_write_ground`
patch is retired. Contribute the *as-implemented* attribute → cell map, the
derived-quantity conversions, the validation/raise behaviour and the Phase 4
numbers to the hand-off doc the foundation-shape packet owns —
`openph-workspace/planning/features/ground-degree-hours-alignment/upstream/phx-foundation-phpp10-shape.md`
(see `features/foundation-phpp10-shape/PRD.md` §"Hand-off to OpenPH") — or, if
this ships separately from that packet, write a sibling
`upstream/phx-05-ground-writer.md` there with the same front matter and note it
in the OpenPH packet's `STATUS.md` "Blockers".

## Related

- `phi-rules` → `rulesets/phpp-10-r1/calculators/phpp-ground/rules.md`
- [`03`](03-summvent-heat-recovery-mode.md) — supplies the radio-group helper
