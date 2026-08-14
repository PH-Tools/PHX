# PRD — Public Honeybee → PHX API

**Status:** Requested · 2026-08-14
**Author:** Ed May + Codex
**Kind:** API/documentation cleanup (no new conversion behavior or model-format change)

---

## Existing capability

PHX already performs the complete in-memory conversion:

```python
from PHX.from_HBJSON import create_project

project = create_project.convert_hb_model_to_PhxProject(hb_model)
```

`convert_hb_model_to_PhxProject()` accepts a live `honeybee.model.Model`
carrying honeybee-ph extensions and returns a complete transient `PhxProject`.
It does not require an HBJSON file, dictionary, temporary file, serialization,
or reread step.

This request does **not** add or replace the Honeybee → PHX conversion engine.
It gives the existing object conversion a clear, stable public API and documents
the boundary accurately.

## Requested public surface

Expose one obvious public function:

```python
from PHX.conversion import from_honeybee

project = from_honeybee(
    hb_model,
    group_components=True,
    merge_faces=False,
    merge_spaces_by_erv=False,
    merge_exhaust_vent_devices=False,
)
```

The facade delegates directly to
`PHX.from_HBJSON.create_project.convert_hb_model_to_PhxProject()`; there is one
conversion implementation and one result contract.

### Public contract

1. **Live-object input.** Accept a `honeybee.model.Model` with honeybee-ph
   extensions. Do not serialize or reread the model as HBJSON.
2. **Project result.** Return the same complete `PhxProject` produced by the
   existing converter.
3. **Public option names.** Expose the existing controls without
   underscore-prefixed parameter names:
   - `group_components: bool = True`
   - `merge_faces: bool | float = False`
   - `merge_spaces_by_erv: bool = False`
   - `merge_exhaust_vent_devices: bool = False`
4. **Unchanged semantics.** Preserve the existing defaults, merge tolerances,
   component/space/device grouping behavior, and target-specific consequences.
5. **Clear boundary errors.** Reject a wrong input type at the facade. Missing
   required honeybee-ph extensions must be identified as an object/extension
   problem, not as an HBJSON file or parsing failure.
6. **Legacy compatibility.** Keep
   `PHX.from_HBJSON.create_project.convert_hb_model_to_PhxProject()` functional.
   Existing callers and file-oriented CLIs do not need to migrate immediately.
7. **Public documentation.** Show the actual in-memory boundary:

   ```text
   Honeybee + honeybee-ph Model
       → PHX.conversion.from_honeybee(...)
       → transient PhxProject
       → target exporter or downstream adapter
   ```

### Relationship to file entry points

The HBJSON-file workflow remains a separate composition:

```python
hb_dict = read_hb_json_from_file(path)
hb_model = convert_hbjson_dict_to_hb_model(hb_dict)
project = from_honeybee(hb_model)
```

CLI entry points may call the facade but retain their existing file-oriented
names and behavior.

## Non-goals

- Do not rewrite or fork the existing conversion implementation.
- Do not move or rename the implementation modules under `PHX/from_HBJSON/`.
- Do not introduce an options dataclass unless a separate demonstrated need
  justifies another public type; the existing four keyword controls are clear.
- Do not change the `PhxProject` model, conversion output, or serialization
  policy.
- Do not add a PHX-level `from_honeybee_variant()` convenience function.
  Honeybee conversion produces a `PhxProject`, potentially with multiple
  variants. A downstream single-variant consumer such as OpenPH owns the
  cardinality check and Project → Variant selection in its adapter.

## Why

The working ph-modeler POC already used the correct object path: it constructed
a Honeybee `Model` in memory, added honeybee-ph data, and passed the live model
to `convert_hb_model_to_PhxProject()`.

The remaining problem is discoverability and API quality:

- the callable is hidden under a package named `from_HBJSON`, implying that a
  file or dictionary may be required;
- its public-use keyword arguments are underscore-prefixed;
- the top-level architecture documentation presents the file workflow without
  clearly separating file parsing from object conversion;
- downstream examples must import an implementation module rather than a
  stable public facade.

## Acceptance criteria

- `from PHX.conversion import from_honeybee` is a documented public import.
- The facade is statically typed `Model -> PhxProject` and exposes the four
  existing options with public names and unchanged defaults.
- Facade and legacy calls produce equivalent projects for reference cases and
  representative option combinations.
- Conversion through the facade performs no temporary-file or JSON round-trip.
- Wrong input types and missing honeybee-ph extension data produce boundary-
  appropriate errors.
- Existing `convert_hb_model_to_PhxProject()` callers and file-based CLIs
  continue to work.
- Public architecture, importer/exporter, and API documentation distinguish
  the live-object conversion from the optional HBJSON file-reading step.
- OpenPH examples use the new facade but retain their own single-variant
  cardinality check and unwrap.
- `python -m pytest tests/` passes.
