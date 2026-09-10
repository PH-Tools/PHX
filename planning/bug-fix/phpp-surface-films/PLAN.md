# Implementation plan — PHPP surface-resistance selectors

DATE: 2026-09-10
STATUS: Implemented on branch
ISSUE: https://github.com/PH-Tools/PHX/issues/118

Read [`README.md`](README.md) first: it carries the evidence the phases below
assume. Five phases, in order. Each is independently testable.

Branch: `bug-fix/phpp-surface-films`.

---

## Phase 1 — Carry the selector strings in the shape files

**Files:** `PHX/PHPP/phpp_localization/shape_model.py`, all seven
`PHX/PHPP/phpp_localization/EN_*.json`.

Add two nested models and hang them off `UValuesConstructorInputs`:

```python
class UValuesRsiSelectors(BaseModel):
    """The PHPP 'U-values' orientation selector strings (Rsi)."""
    wall: str
    roof: str
    floor: str


class UValuesRseSelectors(BaseModel):
    """The PHPP 'U-values' adjacency selector strings (Rse)."""
    exterior: str
    ground: str
    ventilated: str
```

```json
"r_si_selectors": { "wall": "2-Wall",         "roof": "1-Roof",  "floor": "3-Floor" },
"r_se_selectors": { "exterior": "1-Outdoor air", "ground": "2-Ground", "ventilated": "3-Ventilated" }
```

Same values in all seven files. Verified against `PHPP_EN_V10.6_Empty.xlsx`
(`Data!A411:A414` / `C411:C414`). **Unverified for the 9.x and IP shapes** — no
archived workbook for those; the values are carried per-file precisely so a
correction is a JSON edit. Because PHPP reads only `LEFT(…,1)`, a label-text
drift between editions is harmless; a changed *digit* order would not be, which
is what the follow-up in `STATUS.md` covers.

**Test:** the existing `tests/test_PHPP/test_shape_file.py` parametrized load
test already fails if any file is missing the new required fields. Add
`PHPPVersion("10", "6IP", "EN")` to its parameter list while there — it is
currently the one shipped shape file the test does not load.

## Phase 2 — Write the selectors from the block

**File:** `PHX/PHPP/phpp_model/uvalues_constructor.py`.

Give `ConstructorBlock` the two facts PHPP needs, defaulted so every existing
construction site keeps working:

```python
face_type: ComponentFaceType = ComponentFaceType.WALL
exposure_exterior: ComponentExposureExterior = ComponentExposureExterior.EXTERIOR
```

Two properties resolve them onto the shape's strings:

- `r_si_selector`: `ROOF_CEILING → roof`, `FLOOR → floor`, anything else → `wall`.
- `r_se_selector`: `GROUND → ground`; `SURFACE` or an attached-zone number
  (`value > 0`) → `ventilated`; anything else → `exterior`.

In `create_xl_items`, replace the two `0.0` writes with the selector strings,
**at the correct offsets** (`r_si` at `rsi_row_offset`, `r_se` at
`rse_row_offset` — the cross-wiring fix). Drop the unit arguments: the value is
a string, and the IP shapes would otherwise try an `M2K/W → HR-FT2-F/BTU`
conversion on it.

**Tests:** new `tests/test_PHPP/test_phpp_model/test_uvalues_constructor.py` —
one test per stated behavior, sized like `test_areas_surface.py`:

- wall + exterior writes `2-Wall` at `M10` and `1-Outdoor air` at `M11`
  (start row 6 → the `01ud` addresses in the evidence);
- roof + exterior writes `1-Roof`;
- floor + ground writes `3-Floor` / `2-Ground`;
- wall + `SURFACE` writes `3-Ventilated`;
- a default-constructed block (no exposure given) writes `2-Wall` /
  `1-Outdoor air`.

## Phase 3 — Resolve each assembly's exposure from the model

**File:** `PHX/PHPP/phpp_app.py`.

Add a private static resolver next to `_collect_custom_groups`, which is the
same shape of helper:

```python
@staticmethod
def _resolve_assembly_exposures(
    phx_project: project.PhxProject,
) -> dict[int, tuple[ComponentFaceType, ComponentExposureExterior]]:
    """Return {assembly id_num: the (face-type, exterior-exposure) pair that dominates its use by area}."""
```

Walk `phx_variant.building.opaque_components` across all variants, accumulating
`component.get_total_gross_component_area()` into
`{assembly.id_num: {(face_type, exposure): area}}`. Pick the largest area;
break ties deterministically on `(-area, face_type.value, exposure.value)`.

`write_project_constructions` passes the resolved pair into each
`ConstructorBlock`; an assembly no component references keeps the dataclass
defaults (wall / outdoor air).

When one assembly is used at more than one `(face_type, exposure)`, warn through
`self.xl.output` — name the assembly, the pairs found, and the pair chosen, and
say that PHPP carries one selector pair per assembly block so a split assembly
is the manual fix. Silence there would hide a real modelling decision.

**Tests:** extend `tests/test_PHPP/` with a resolver test — single use resolves
to that pair; mixed use resolves to the larger area and emits the warning;
an unreferenced assembly is absent from the map.

## Phase 4 — Stop `activate_variants` re-zeroing the films

**File:** `PHX/PHPP/sheet_io/io_u_values.py`.

`activate_variants` runs after `write_project_constructions`, calls
`clear_all_constructor_data` (which blanks `M+4:M+5`) and then writes `0` back
into both film cells. It must restore the resolved selectors instead.

`write_constructor_blocks` records `{display_name: (r_si_selector,
r_se_selector)}` on the controller as it writes. `activate_variants` looks the
assembly name up and writes the pair back at the correct offsets — two separate
`XlItem`s, not the single `M11:M10` range it writes today. An unknown name falls
back to the shape's `wall` / `exterior` strings, which is what PHPP's own
formula defaults to anyway.

**Test:** a fake-XL test asserting the film cells hold the selectors, not `0`,
after `write_constructor_blocks` + `activate_variants`.

## Phase 5 — Golden state, suite, docs

1. **Golden fixture.** The change moves exactly six cells in
   `tests/test_xl_replay/fixtures/single_zone_replay.json` `golden_writes`:

   | Cell | Was | Becomes |
   |---|---|---|
   | `U-values!M10` / `M11` | `0.0` | `2-Wall` / `1-Outdoor air` |
   | `U-values!M31` / `M32` | `0.0` | `3-Floor` / `2-Ground` |
   | `U-values!M52` / `M53` | `0.0` | `1-Roof` / `1-Outdoor air` |

   Nothing in the write sequence reads those cells back (`Areas` selects from
   `Components`; the U-Values reads are the name column `L` and the generated ID
   column `Q`), so no other golden write moves and the recorded `seed` /
   `epoch_deltas` stay valid for replay. Edit those six entries in place rather
   than re-recording: the diff is then exactly the intended change and stays
   reviewable. A full live re-record against the licensed template is the
   follow-up in `STATUS.md`, tracked with the one already open as #102.

2. **`python -m pytest tests/`** — the whole suite, per hard rule 6.

3. **Hand check** the worked example: a declared-U assembly
   (`R_no_mass = 6.4967`) written through the new path resolves `R25` to `0.150`
   under `2-Wall` / `1-Outdoor air`, not `0.1539`.

4. **Docs pass.** Fold the outcome into `docs/reference/phx-model-reference.md`
   (the PHPP write path now selects surface resistances from component exposure)
   and note the term pair in `context/UBIQUITOUS_LANGUAGE.md` if
   "surface resistance" / "selector" is not already there. `docs/nav.yml` needs
   nothing: no new public API.

5. **Status + archive.** Add the row to `planning/STATUS.md`, PR body carries
   `Closes #118`.
