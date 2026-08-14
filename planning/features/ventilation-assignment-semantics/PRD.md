# PRD — Explicit ventilation assignment semantics

**Status:** In progress · cross-repo contract accepted · 2026-08-14
**Author:** Ed May + Codex
**Kind:** Cross-boundary model/converter feature (PHX is primary for PHX representation)

---

## WHAT

Define and implement explicit PHX semantics for a Space's ventilation mode and
mechanical-device assignment. An absent assignment must not masquerade as the
integer ID `0`, and a missing honeybee-ph ventilation unit must not create a
blank `PhxDeviceVentilator` merely to satisfy downstream lookups.

### Current hazardous behavior

- `PhxSpace.vent_unit_id_num` defaults to `0`.
- `from_HBJSON/create_rooms.py` copies the honeybee-ph system's numeric ID.
- `build_phx_ventilator()` constructs a new default `PhxDeviceVentilator` before
  checking whether the honeybee-ph system has a unit and returns that blank
  device when it does not.
- PHPP/OpenPH consumers later attempt lookup by numeric ID and can fail with an
  opaque message such as `Device 0 not Found`.

### Required source-state matrix

Before implementation, document the mapping for at least these states:

| Source state | PHX meaning | Device reference |
|---|---|---|
| No ventilation airflow and no mechanical system | None/unassigned | `None` |
| Existing summer window-ventilation data | Summer ACH fields; no primary K12=3 mode | `None` |
| Balanced/extract mechanical system with device | Mechanical | Valid device ID |
| Mechanical airflow/system but missing device | Invalid/incomplete | Diagnostic; no placeholder |
| Device exists but Space reference does not resolve | Invalid/incomplete | Diagnostic naming both objects |

The accepted implementation uses `Optional[int]` for assignment. Existing
summer window-ventilation inputs remain separate; primary PHPP K12=3 window
mode is deferred until an upstream source representation exists.

### Model contract

1. Replace `vent_unit_id_num: int = 0` with
   `vent_unit_id_num: Optional[int] = None`. `0` is not the no-device sentinel.
2. Preserve every positive imported device ID exactly. Normalize blank/`0`
   absence at supported import boundaries; PHX device IDs start at 1.
3. Provide a model-level integrity check that validates every Space mechanical
   assignment against the variant's device collections and returns all
   unresolved references together.
4. `vent_unit_display_name` is descriptive only and never repairs or replaces
   an invalid ID.
5. Space grouping/`__add__` behavior must keep assignment mode and device
   identity in its equality/merge key; unlike assignments cannot merge.

### Converter contract

1. Honeybee → PHX creates a `PhxDeviceVentilator` only when a real source unit
   exists or a deliberately named source state requires one.
2. No-mechanical and natural/window states remain device-free.
3. Incomplete source systems produce a structured conversion error/diagnostic,
   not a blank zero-performance device.
4. WUFI XML import maps missing/blank device references to the explicit PHX
   state, while preserving real imported identifiers.

### Export contract

Each exporter translates explicit PHX states according to its own format:

- PHPP skips assignment lookup/write for `None`.
- WUFI XML and METr JSON emit numeric `0` under the accepted legacy writer
  convention; WUFI import normalizes blank/`0` to `None`. This is a boundary
  compatibility rule, not a PHX domain value.
- Existing summer window inputs remain independent. Primary PHPP K12=3 window
  mode is deferred rather than inferred from absence.
- Mechanical assignments always reference a device actually written by that
  exporter.
- Invalid/incomplete states fail before partial output is produced.

### Duct relationship

PHX already represents:

- multiple `PhxDuctElement`s in a mechanical collection;
- multiple `PhxDuctSegment`s inside each element;
- length-weighted aggregate properties on an element;
- an explicit `vent_unit_id` and supply/exhaust `duct_type`.

Keep that information. Add a deterministic query such as
`ducts_for_ventilation_unit(device_id, direction)` if needed so consumers do not
reimplement filtering. Do **not** collapse all elements to one equivalent duct
in the target-neutral PHX model unless a separately verified physical contract
supports it. PHPP/OpenPH-specific consolidation belongs at that target boundary.

### Compatibility

- PHX is transient, but source importers and target exporters form a public
  compatibility surface. Update them together.
- Any behavior change to PHPP cell writes must keep the xl-replay golden-state
  invariant or intentionally rerecord it with evidence.
- Update model reference and exporter/importer docs.

## WHY

The POC had to add a ventilation device and two physical 1 m ducts to avoid a
downstream device-lookup failure. That workaround produced a calculable model
but blurred three different facts: whether ventilation exists, which device
serves the Space, and whether exterior duct losses are modeled.

PHX is the exchange layer where those source semantics must remain explicit.
If it reduces absence to integer `0` or manufactures a blank device, every
target has to reverse-engineer intent and may silently calculate the wrong
system.

Explicit assignments also improve error reporting, merging, WUFI round-trips,
and OpenPH readiness validation without requiring PHX to adopt OpenPH-specific
solver rules.

## Acceptance criteria

- Default `PhxSpace()` has an explicit unassigned state, not device ID `0`.
- No source ventilation unit produces no PHX device.
- Mechanical airflow without a device fails with a targeted diagnostic.
- Every valid assignment resolves to exactly one device in its variant.
- Natural/window, none, and mechanical states round-trip through each supported
  source/target path with documented behavior.
- Multiple duct elements/segments remain preserved and queryable.
- Space grouping never merges incompatible assignment states.
- PHPP xl-replay and WUFI/METr/PPP reference outputs are unchanged for existing
  valid mechanical-system fixtures.
- Full `python -m pytest tests/` passes.
