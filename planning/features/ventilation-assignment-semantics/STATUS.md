# STATUS — ventilation-assignment-semantics

**Status:** In progress · contract accepted · 2026-08-14

- `STATE_TABLE.md` freezes `PhxSpace.vent_unit_id_num: Optional[int] = None` as
  the domain representation of no assignment.
- PHX's duct model already preserves multiple elements and multiple segments;
  this packet does not propose lossy model-level aggregation.
- Target formats that require a numeric value map `None` to `0` only while
  writing and normalize blank/`0` to `None` while importing.
- Primary PHPP K12=3 window-only authoring is deferred because honeybee-ph has
  no explicit source state; existing summer window ACH is not overloaded.
- **Next step:** add failing tests for no device, incomplete, and unresolved
  assignments, then implement the accepted nullable representation.
- Cross-repo coordination:
  - honeybee-ph `planning/features/default-ventilation-system-factory/`
  - OpenPH `planning/archive/dated/2026-08-14/ventilation-input-semantics/`
- No contract blocker remains. OpenPH already supports `None`, zero ducts, and
  multiple duct elements; it retains legacy input `0` compatibility.
- Phase 01 documentation gate: no broken links or stale status language;
  `/Users/em/Dropbox/bldgtyp-00/00_PH_Tools/PHX/.venv/bin/python -m pytest tests/`
  passed with **881 tests**, **3 skipped**, and **1 deselected**.
