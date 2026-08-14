# PRD — Public Honeybee → PHX conversion facade

**Status:** Requested · 2026-08-14
**Author:** Ed May + Codex
**Kind:** Feature (PHX public API; no model-format change)

---

## WHAT

Expose one obvious, documented public function for the in-memory conversion:

```python
from PHX import from_honeybee

project = from_honeybee(hb_model)
```

or an equivalently clear import such as:

```python
from PHX.conversion import from_honeybee
```

The canonical function accepts a live `honeybee.model.Model` carrying
honeybee-ph extensions and returns a complete in-memory `PhxProject`.

### Public contract

1. **No file requirement.** The function does not serialize, write, or reread
   HBJSON. It accepts the already constructed Honeybee object.
2. **One implementation.** It delegates to or becomes the existing
   `PHX.from_HBJSON.create_project.convert_hb_model_to_PhxProject()` logic. Do
   not fork conversion behavior.
3. **Typed conversion options.** Preserve the existing controls for component
   grouping, face merging/tolerance, space grouping by ERV, and exhaust-device
   grouping. If exposed as a typed options value, defaults and target-specific
   consequences must be documented. An options object should reduce ambiguity,
   not create a second configuration path.
4. **Stable result.** The returned project has the same variants, components,
   zones, spaces, schedules, constructions, site data, and HVAC data as the
   legacy call for identical inputs/options.
5. **Clear errors.** A wrong input type or missing required honeybee-ph
   extension reports the object/path involved. It must not be mislabeled as a
   file/HBJSON parse error.
6. **Public docs.** Document the actual boundary:

   ```text
   Honeybee + honeybee-ph Model
       → PHX.from_honeybee(...)
       → transient PhxProject
       → target exporter or OpenPH
   ```

7. **Compatibility.** Keep
   `from_HBJSON.create_project.convert_hb_model_to_PhxProject()` functional for
   a documented migration window as a thin alias/delegating entry point.
8. **Naming cleanup is additive first.** Do not move every `from_HBJSON`
   implementation module merely to make the tree aesthetically consistent.

### Relationship to file entry points

The HBJSON-file workflow remains available as a separate composition:

```python
hb_dict = read_hb_json_from_file(path)
hb_model = convert_hbjson_dict_to_hb_model(hb_dict)
project = from_honeybee(hb_model)
```

CLI functions may reuse the facade but retain their file-oriented names.

### Constraints

- PHX models remain transient; this feature does not serialize `PhxProject`.
- No new dependency.
- Update public API docs/navigation for the new function.
- Preserve conventional release/commit requirements.

## WHY

The working POC never needed an HBJSON file. It built a Honeybee `Model` in
memory, added honeybee-ph objects, and passed the live object into
`convert_hb_model_to_PhxProject()`. That correct path is hidden under a package
named `from_HBJSON` and a mixed-style internal function name.

The current naming creates three avoidable uncertainties for an integrator:

- whether a file is required;
- whether a dictionary or a Honeybee `Model` is accepted;
- which package owns Honeybee → PHX versus PHX → OpenPH.

A small public facade makes the intended in-memory architecture discoverable
without destabilizing the mature converter internals.

## Acceptance criteria

- One documented public import converts a live Honeybee model.
- Canonical and legacy calls produce equivalent project snapshots for all
  reference cases and option combinations.
- No temporary file or JSON round-trip occurs.
- Static typing exposes `Model -> PhxProject`.
- File-based CLIs continue to work.
- Public architecture/exporter docs show the live-object path.
- Full `python -m pytest tests/` passes.

---

## Addendum — 2026-08-14 (from OpenPH `phx-conversion-facade` closeout)

The OpenPH-side facade (`openph.conversion.from_phx_variant`) shipped
2026-08-14. Its documented example still has to write the three PHX-owned
sharp edges the ph-modeler POC hit, so this request additionally covers:

1. **Underscore-prefixed load-bearing kwarg.** The public conversion requires
   `convert_hb_model_to_PhxProject(model, _group_components=True)` — an
   underscore-prefixed keyword doing public work. The facade (or its typed
   options value, contract item 3) must give this a public name.
2. **Project→Variant unwrap.** OpenPH is structurally single-zone and accepts
   one `PhxVariant`; every caller must know to unwrap
   `phx_project.variants[0]` themselves and assert there is exactly one.
3. **Single-variant convenience.** Provide a public single-variant conversion
   (e.g. `from_honeybee_variant(hb_model)` / `convert_hb_model_to_PhxVariant`)
   that performs the unwrap with a clear error when the model does not produce
   exactly one variant.

When this surface lands, update the canonical example in OpenPH
(`openph/src/openph/conversion.py` module docstring and `openph/README.md`) —
both currently document the raw call sequence above verbatim.
