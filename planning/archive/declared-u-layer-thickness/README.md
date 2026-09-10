# `from_HBJSON`: honor a declared thickness on a marked no-mass Layer, and collapse the sandwich shells

- **Status:** Complete — merged to `main` 2026-09-10 via PR
  [#117](https://github.com/PH-Tools/PHX/pull/117). Both steps landed in
  `PHX/from_HBJSON/create_assemblies.py` with 17 new tests; 1111 green, reference XML/METr output
  and the xl-replay golden state unchanged. Decisions D1–D5 all taken as recommended; the §9 films
  divergence is now [#118](https://github.com/PH-Tools/PHX/issues/118). Outcome folded into
  `docs/reference/phx-model-reference.md` and `context/UBIQUITOUS_LANGUAGE.md`.
- **Filed:** 2026-09-10 (Ed May / Claude)
- **Issue:** [#116](https://github.com/PH-Tools/PHX/issues/116)
- **Kind:** Feature — additive, gated entirely by an upstream marker
- **Owners:** `PHX/from_HBJSON/create_assemblies.py`
- **Origin:** PH-Navigator for SketchUp, Assembly Builder phase 6, decision E4-2
  (2026-09-09; `ph-navigator-sketchup/planning/phases/E4_complex-construction-representation.md`)

---

## 1. What the issue asks for

`build_layer_from_hb_material` gives every `EnergyMaterialNoMass` the default
0.1 m thickness and back-solves conductivity from it. PH-Navigator for SketchUp
now emits a **Declared-U Assembly** as the sandwich `GHCompo_CreateSDConstructions`
has always used, and rides the real declared thickness on the no-mass material:

```
[ EnergyMaterial   phn_declared_shell   t = 0.010 m,  λ = 100 W/mK ]
[ EnergyMaterialNoMass  phn_<id>_declared   R = 1/U − Rsi − Rse     ]  ← marker here
[ EnergyMaterial   phn_declared_shell   t = 0.010 m,  λ = 100 W/mK ]
```

```python
material.properties.ph.user_data["phn_declared_u"] = {
    "u_w_m2k": ..., "thickness_mm": ..., "r_in": ..., "r_out": ..., "r_no_mass": ...,
}
```

Two steps requested:

1. Use `thickness_mm` as the Layer thickness instead of the 0.1 m default.
2. Collapse the two shell Layers into the marked no-mass Layer, so the Assembly
   is one row instead of three.

---

## 2. What today's conversion actually produces (verified 2026-09-10)

Probe: declared U = 0.150 W/m²K, Rsi 0.13, Rse 0.04, declared thickness 305 mm.
`r_no_mass` = 1/0.150 − 0.13 − 0.04 = 6.4967 m²K/W.

| | Layers | Thicknesses (mm) | λ (W/mK) | Assembly R (m²K/W) |
|---|---|---|---|---|
| Today | 3 | 10 / **100** / 10 | 100 / 0.015393 / 100 | 6.496867 |
| Wanted | 1 | **305** | 0.046949 | 6.496667 |

- The two shells contribute **0.0002 m²K/W** total, exactly as the issue says.
- Reconstructing U through the stripped films: today `1/(6.496867 + 0.17)` =
  **0.1499955**, against the declared 0.150. Error **4.5e-6 W/m²K**, three orders
  of magnitude inside the Assembly Builder's ±0.0005 W/m²K regression bar. The
  issue's "the U-value already round-trips correctly" is confirmed.
- The visible defect is thickness: PHX reports **120 mm** where the assembly
  declares 305 mm, and three rows where the modeler declared one.

### Where the wrong thickness surfaces

| Target | Path | What is wrong today |
|---|---|---|
| WUFI XML | `_PhxLayer` → `<Thickness>` | three layers, 0.01 / 0.1 / 0.01 m |
| METr JSON | `_PhxConstructionOpaque` → `lLayer[].thick` | same three |
| PHPP `U-values` | `uvalues_constructor.create_xl_items` | three rows; `R23` total thickness = 12 cm, which `Components!J13` reads as the Assembly thickness |
| PPP (designPH) | `u_value_sections` writes `asm.u_value` only | unaffected |

Note that `ConstructorBlock.is_mass_material` already skips the *Grasshopper*
shell by name (`display_name == "MAT_Mass" and conductivity == 100`). The
PH-Navigator shell is named `phn_declared_shell`, so it is **not** skipped, and
PHPP shows all three rows. That name-matching skip also leaves a blank layer row
behind it, because the `continue` does not rewind the enumerate index. Collapsing
upstream in `from_HBJSON` sidesteps both.

---

## 3. Design

### 3.1 The marker is the entire opt-in

No new function argument, no new flag on `convert_hb_model_to_PhxProject`, no
plumbing through the CLI entry points. A Layer changes behavior if and only if
its Honeybee material carries `properties.ph.user_data["phn_declared_u"]`.

`EnergyMaterialNoMassPhProperties.user_data` is serialized in `to_dict` and read
back in `from_dict` (honeybee_ph `honeybee_energy_ph/properties/materials/opaque.py`),
so the marker survives the HBJSON round-trip. Confirmed.

### 3.2 Read the marker for thickness only, never for R

The Layer's R must keep coming from the Honeybee material's own `r_value`. PHX
would then set λ = t / R, which preserves R exactly and leaves U untouched.
Recomputing R from the marker's `u_w_m2k`/`r_in`/`r_out` would create a second
source of truth that can disagree with what honeybee actually stored (honeybee
clamps `EnergyMaterialNoMass.r_value` at its own minimum). `r_no_mass` and
`u_w_m2k` in the marker are provenance for a human reader, not inputs.

### 3.3 Shell detection

Collapse only when the whole three-material shape matches:

- exactly three materials, and
- the middle one is an `EnergyMaterialNoMass` carrying the marker, and
- the outer two are `EnergyMaterial`, share one identifier, and are shell-shaped
  (t = 0.01 m, λ = 100 W/mK, compared with `math.isclose`).

Matching the literal string `"phn_declared_shell"` would work today but couples
PHX to one producer's naming; shape plus a shared identifier is the same test
without the coupling. See decision **D3**.

### 3.4 Order of operations inside `build_opaque_assemblies_from_HB_model`

Collapse the Honeybee material list **before** both the Layer build and
`_set_opaque_assembly_exterior_radiation_properties`, which reads `materials[0]`.
Today that is the outer shell (`thermal_absorptance` 0.9, `solar_absorptance` 0.7);
after collapse it is the no-mass material, constructed with the same 0.9 / 0.7.
The PHPP `Areas` AI/AJ values are therefore unchanged either way — but only if
the collapse happens first, so the radiation read still sees the outermost
*surviving* material rather than a removed shell.

---

## 4. Implementation sketch

All of it lands in `PHX/from_HBJSON/create_assemblies.py`. Nothing becomes public
API, so `docs/nav.yml` is untouched.

```python
DECLARED_U_MARKER_KEY = "phn_declared_u"
DECLARED_U_SHELL_THICKNESS_M = 0.01
DECLARED_U_SHELL_CONDUCTIVITY_W_MK = 100.0


def _get_declared_u_marker(_hb_material) -> dict | None:
    """Return the PH-Navigator declared-U marker from a material's PH user-data, or None."""
    ph_props = getattr(_hb_material.properties, "ph", None)
    user_data = getattr(ph_props, "user_data", None)
    if not isinstance(user_data, dict):
        return None
    marker = user_data.get(DECLARED_U_MARKER_KEY)
    return marker if isinstance(marker, dict) else None


def _get_declared_thickness_m(_hb_material) -> float | None:
    """Return the declared layer thickness (M), or None if the marker carries no usable one."""
    if (marker := _get_declared_u_marker(_hb_material)) is None:
        return None
    try:
        thickness_mm = float(marker["thickness_mm"])
    except (KeyError, TypeError, ValueError):
        logger.warning("Declared-U material '%s' has no usable 'thickness_mm'; "
                       "using the default no-mass thickness.", _hb_material.display_name)
        return None
    if thickness_mm <= 0:
        logger.warning("Declared-U material '%s' declares thickness %s mm; "
                       "using the default no-mass thickness.", _hb_material.display_name, thickness_mm)
        return None
    return thickness_mm / 1000
```

In `build_layer_from_hb_material`, the no-mass branch becomes:

```python
    elif isinstance(source_material, EnergyMaterialNoMass):
        declared_thickness_m = _get_declared_thickness_m(source_material)
        new_layer.thickness_m = _no_mass_thickness_m if declared_thickness_m is None else declared_thickness_m
        new_layer.set_material(build_phx_material_from_hb_EnergyMaterialNoMass(source_material, new_layer.thickness_m))
```

The collapse:

```python
def _is_declared_u_shell(_hb_material) -> bool:
    return (
        isinstance(_hb_material, EnergyMaterial)
        and math.isclose(_hb_material.thickness, DECLARED_U_SHELL_THICKNESS_M, rel_tol=1e-9)
        and math.isclose(_hb_material.conductivity, DECLARED_U_SHELL_CONDUCTIVITY_W_MK, rel_tol=1e-9)
    )


def _collapse_declared_u_sandwich(_hb_materials: list) -> list:
    """Reduce a marked declared-U sandwich to its single no-mass material. Any other list is returned as-is."""
    if len(_hb_materials) != 3:
        return _hb_materials
    outer, core, inner = _hb_materials
    if _get_declared_u_marker(core) is None:
        return _hb_materials
    if not (_is_declared_u_shell(outer) and _is_declared_u_shell(inner)):
        return _hb_materials
    if outer.identifier != inner.identifier:
        return _hb_materials
    return [core]
```

and in `build_opaque_assemblies_from_HB_model`, one line before the existing
`if hb_const.identifier not in _project.assembly_types:`:

```python
            materials = _collapse_declared_u_sandwich(getattr(hb_const, "materials", DEFAULT_MATERIALS))
```

---

## 5. Steps 1 and 2 ship together, not separately

Honoring the thickness without collapsing makes the reported total **worse**, not
better: 305 + 10 + 10 = **325 mm** for an assembly that declares 305 mm, and
PHPP's `Components!J13` would carry 0.325 m. Today's 120 mm is at least obviously
a placeholder. Only the pair produces the declared number. If Ed wants step 1
alone, the shells should be subtracted from the declared thickness instead, which
is worse in every way (it invents a layer thickness that no one declared).

**Recommendation: one PR containing both.**

---

## 6. Refusal / fallback table

Every path below falls back to today's behavior. Nothing raises; a Declared-U
Assembly that PHX cannot read still exports with the correct U-value.

| Input | Result |
|---|---|
| No marker on the no-mass material | 0.1 m default, three rows (unchanged) |
| Marker present, `thickness_mm` absent or `None` | 0.1 m default + `logger.warning` |
| `thickness_mm` ≤ 0, or not a number | 0.1 m default + `logger.warning` |
| `user_data` is not a dict, or `properties.ph` absent | 0.1 m default, silent |
| Marker present but the sandwich is not the exact 3-material shape | thickness honored, **no** collapse |
| Marked material inside a Division Grid | not reachable — `build_layer_from_hb_material` picks the base material from the grid before the type branch, and no-mass materials do not carry grids |

---

## 7. Tests

New: `tests/test_from_HBJSON/test_create_assemblies/test_declared_u_assembly.py`.
Built from synthetic Honeybee materials in-test (as `test_create_window_type.py`
does), so no new reference fixture and nothing licensed.

1. Marked no-mass material → Layer thickness is the declared thickness and
   `layer_resistance` still equals the material's `r_value` to 1e-9.
2. Unmarked no-mass material → 0.1 m default (regression guard).
3. Malformed marker matrix (missing / `None` / `0` / `-5` / `"305"` as a string /
   `user_data` not a dict) → default thickness, no exception.
4. Marked sandwich → one `PhxLayer`; assembly `r_value` within 2.1e-4 of the
   pre-change three-layer value (the shells' 0.0002), and the reconstructed
   `1/(R + Rsi + Rse)` equals the declared U to 1e-9.
5. Unmarked `MAT_Mass` sandwich (the Grasshopper `CreateSDConstructions` shape) →
   still three Layers.
6. Marked core with one shell, three shells, or a differently-shaped shell →
   not collapsed.
7. `exterior_solar_absorptance` / `exterior_thermal_emissivity` after collapse
   come from the no-mass material.
8. End-to-end: a one-room Honeybee model with the sandwich on one face through
   `convert_hb_model_to_PhxProject` → one Layer on the `PhxConstructionOpaque`.

**Regression guards already in the tree, which must stay byte-identical:**

- The three `to_xml_reference_cases` and three `to_metr_json_reference_cases`.
  `Multi_Room_Complete` writes `Generic Wall Air Gap` (an `EnergyMaterialNoMass`)
  as `<Thickness>0.1</Thickness>` with λ 0.667, so the default path is locked by
  an existing reference file.
- `tests/test_xl_replay/` golden cell state. No reference model carries the
  marker, so the PHPP write path cannot move. (`Multi_Room_Complete.hbjson` does
  contain a `MAT_Mass` sandwich, `test_floor`, but no face uses it, so it never
  becomes a `PhxConstructionOpaque` — verified 2026-09-10.)
- Full suite: `python -m pytest tests/`.

---

## 8. Explicitly out of scope

- **Extending the collapse to the Grasshopper `MAT_Mass` sandwich.** It has the
  same shape but no marker, so it stays on today's path. Doing it would change
  validated WUFI/METr output and the PHPP row layout for every existing SD-
  construction model. Follow-up issue if wanted, not this one.
- **Fixing the `is_mass_material` blank-row gap** in `uvalues_constructor.py`.
  Pre-existing, harmless (PHPP sums `AJ13:AJ20`), and only reachable on the
  Grasshopper path this change does not touch.
- **The `r_si` / `r_se` offset cross-wiring** in `uvalues_constructor.create_xl_items`
  (`"r_si"` is written at `rse_row_offset` and `"r_se"` at `rsi_row_offset`).
  Both values are `0.0` in the same column, so it is cosmetic. Noted, not fixed.

---

## 9. Adjacent finding — needs its own issue, not this one

**PHX writes `Rsi = Rse = 0.0` into PHPP, so a film-stripped declared U lands
2.6% high in the workbook.** This is much larger than the shell effect this
issue is about, and this change neither causes nor cures it.

The PHX model has no surface-film concept (0 hits for any surface-resistance
field in `PHX/model/`). The PHPP writer puts `0.0` into both selector cells, and
the corpus-verified formulas take a number as given:

```
M24 = IF(M10="","",IF(ISNUMBER(M10),M10, ...Data!$B$412:$B$414...))   ← Rsi
M25 = IF(M11="","",IF(ISNUMBER(M11),M11, ...Data!$D$412:$D$413...))   ← Rse
AJ25 = $M24 + SUM(AJ13:AJ20) + $M25
R25  = ... 1/Y25 ... + R11                                            ← the U-value PHPP publishes
```
(phi-rules `rulesets/phpp-10-r1/calculators/phpp-u-values/rules.md`)

So every PHX-written PHPP assembly publishes a **construction-only** U-value.
That is coherent with the WUFI target, where the assembly U is construction-only
and WUFI applies films per component exposure — which is exactly why E4-2 strips
the films upstream. The two targets then diverge:

| Target | What the declared-U assembly resolves to |
|---|---|
| WUFI / METr | 1/(6.4967 + Rsi + Rse) applied by the tool = **0.150**, the declared value |
| PHPP | `R25` = 1/6.4967 = **0.1539**, i.e. **+0.0039 W/m²K, +2.6%** |

Two possible directions, both bigger than this packet: PHX learns per-exposure
surface resistances for the PHPP write path (affects every assembly PHX has ever
written, and the xl-replay golden state), or PH-Navigator stops stripping films
and emits a PHPP-shaped R instead (breaks the WUFI number). **Neither should be
decided here.** Recommend filing it as a separate PHX issue with this table.

Per the house rule, this is reported as a verified numeric divergence, not as a
defect claim: PHX is internally consistent, and no one has yet checked a
PHX-written PHPP against a hand-built one on this point.

---

## 10. Decisions needed before implementation

| # | Question | Recommendation |
|---|---|---|
| **D1** | Adopt `phn_declared_u` as PHX's permanent contract key, or define a vendor-neutral one (`ph_declared_u`) and change the producer? | Adopt as-is behind a module constant. One producer exists; renaming later is a one-line change plus an alias. |
| **D2** | Implement the collapse (step 2), or thickness only? | Both, one PR. See §5. |
| **D3** | Detect shells by shape + shared identifier, or by the literal `phn_declared_shell`? | Shape + shared identifier. Same discrimination, no coupling to one producer's names. |
| **D4** | Warn on a malformed marker, or fall back silently? | `logger.warning`. `create_assemblies.py` already has a logger and emits nothing today, so a warning here is legible rather than noise. |
| **D5** | File the §9 films divergence as its own issue? | Yes. |

---

## 11. Closeout

- [ ] `python -m pytest tests/` green, including `test_xl_replay`.
- [ ] Reference XML and METr JSON outputs byte-identical.
- [ ] Black + isort clean.
- [ ] Conventional commit: `feat(from_HBJSON): honor declared thickness on marked no-mass layers`.
- [ ] PR body: `Closes #116`.
- [ ] Fold into `docs/reference/phx-model-reference.md`: one row in the *Honeybee
      to PHX Concept Mapping* table for `EnergyMaterialNoMass` → `PhxLayer`, and a
      short paragraph naming the marker contract.
- [ ] Add **Declared-U Assembly** to `context/UBIQUITOUS_LANGUAGE.md`, aligned with
      the definition already in `ph-navigator-sketchup/00_Context/UBIQUITOUS_LANGUAGE.md`.
- [ ] Move this folder to `planning/archive/declared-u-layer-thickness/` and add a
      row to `planning/archive/README.md`.
- [ ] Tell `ph-navigator-sketchup` the follow-up landed, and note the one upstream
      gap found while reading it: E4-2 says the assembly colour rides on the no-mass
      material, but `phn_assemblies.py` sets no `ph_color` on it, so the collapsed
      Layer will export with PHX's default colour.
