# STATUS — ventilation-assignment-semantics

**Status:** Requested · 2026-08-14

- Confirmed current defaults: `PhxSpace.vent_unit_id_num = 0`; missing
  honeybee-ph units can yield a blank default `PhxDeviceVentilator`.
- PHX's duct model already preserves multiple elements and multiple segments;
  this packet does not propose lossy model-level aggregation.
- **Next step:** document the target-by-target state matrix, add failing tests
  for no device/incomplete/unresolved assignments, then choose the smallest
  explicit model representation.
- Cross-repo coordination:
  - honeybee-ph `planning/features/default-ventilation-system-factory/`
  - OpenPH `planning/features/ventilation-input-semantics/`
- Blocker: natural/window and no-mechanical target encodings must be verified
  against PHPP and WUFI before freezing the enum/state names.

