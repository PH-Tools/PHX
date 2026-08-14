# PHX ventilation assignment state table

**Status:** Accepted for implementation · 2026-08-14

This is the PHX portion of the coordinated honeybee-ph / PHX / OpenPH
contract. PHX uses explicit absence in its transient domain model and adapts
that state separately for each target schema.

| State | `PhxSpace.vent_unit_id_num` | Device collection | Result |
|---|---|---|---|
| No mechanical system | `None` | No device added | Valid; exporters skip lookup |
| Existing summer window ventilation | `None` | No device added | Summer fields remain independent; no mechanical assignment |
| Mechanical source with real device | Real `id_num` | Exactly that converted device | Valid when the reference resolves |
| Mechanical source missing device | Not converted | No placeholder | Honeybee conversion fails with a targeted source diagnostic |
| Unresolved positive reference | Unresolved ID | Unchanged | Variant readiness reports Space and missing ID before export |

PHPP's primary `3-Only window ventilation` / K12=3 choice is not currently
authorable from honeybee-ph. PHX therefore does not infer it from summer window
ACH or from an unassigned Space. A future source representation must make that
state explicit.

## Boundary mappings

| Boundary | `None` mapping | Real ID mapping |
|---|---|---|
| Honeybee → PHX | No device and no assignment | Convert real `Ventilator`, then assign its ID |
| PHX → PHPP | Skip device lookup/assignment write | Resolve before writing |
| PHX → WUFI XML | Emit numeric `0` under the legacy writer convention | Emit ID |
| WUFI XML → PHX | Normalize blank/`0` to `None` | Preserve positive ID |
| PHX → METr JSON | Emit numeric `0` under the legacy writer convention | Emit ID |
| PHX → OpenPH | Pass `None` | Pass ID; OpenPH validates resolution |

OpenPH temporarily normalizes legacy PHX `0` input to `None`. That
compatibility behavior does not make `0` part of the new PHX domain contract.

## Duct contract

- PHX preserves zero, one, or multiple `PhxDuctElement`s and every element's
  segments.
- Elements retain a real device assignment and supply/exhaust direction.
- No 1 m element is manufactured when the source collection is empty.
- The PHPP/OpenPH boundary owns target aggregation. Its canonical formula and
  cell evidence are in OpenPH's archived
  `ventilation-input-semantics/STATE_TABLE.md`; zero elements remains the valid
  no-exterior-duct-loss state.

## Integrity diagnostics

Variant readiness aggregates every unresolved Space/device and duct/device
reference before output. Diagnostics name the source object and observed ID.
Exporters use this common check rather than failing after partial writes.
