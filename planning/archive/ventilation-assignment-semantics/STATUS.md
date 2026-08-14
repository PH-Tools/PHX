# STATUS — ventilation-assignment-semantics

**Status:** Complete · PHX v1.56.79 released and archived · 2026-08-14

- `STATE_TABLE.md` freezes `PhxSpace.vent_unit_id_num: Optional[int] = None` as
  the domain representation of no assignment.
- PHX's duct model already preserves multiple elements and multiple segments;
  this packet does not propose lossy model-level aggregation.
- Target formats that require a numeric value map `None` to `0` only while
  writing and normalize blank/`0` to `None` while importing.
- Primary PHPP K12=3 window-only authoring is deferred because honeybee-ph has
  no explicit source state; existing summer window ACH is not overloaded.
- `PhxSpace.vent_unit_id_num` now defaults to `None`; WUFI import normalizes
  missing/blank/`0`, while WUFI and METr writers adapt `None` back to legacy
  numeric `0` only at their boundaries.
- Honeybee conversion validates every source ventilation system before any
  PHX/source mutation and rejects a mechanical system without a real unit.
- Variant readiness aggregates unresolved/ambiguous Space references,
  unassigned mechanical airflow, and collection-scoped duct references.
- PHPP, WUFI, METr, and PPP run readiness before output; PHPP skips Space
  lookup for `None`.
- honeybee-ph **v1.33.42** and PHX **v1.56.79** are published and pass clean
  installed-artifact smoke tests. PHX requires `honeybee-ph>=1.33.42`.
- The published matrix `honeybee-ph==1.33.42`, `PHX==1.56.79`,
  `openph==0.5.1`, and `openph-demand==0.5.0` installs and converts the
  no-mechanical, zero-duct, and multi-duct states successfully.
- Both active packets are archived. No release blocker or next implementation
  step remains in this feature.
- Cross-repo coordination:
  - honeybee-ph `planning/archive/default-ventilation-system-factory/`
  - OpenPH `planning/archive/dated/2026-08-14/ventilation-input-semantics/`
- No contract blocker remains. OpenPH already supports `None`, zero ducts, and
  multiple duct elements; it retains legacy input `0` compatibility.
- Phase 01 documentation gate: no broken links or stale status language;
  `/Users/em/Dropbox/bldgtyp-00/00_PH_Tools/PHX/.venv/bin/python -m pytest tests/`
  passed with **881 tests**, **3 skipped**, and **1 deselected**.
- Implementation affected-surface gate: **516 passed**, **3 skipped** across
  HBJSON/WUFI conversion, WUFI/METr/PPP/PHPP exports, xl-replay, project/HVAC
  model tests, and ventilation readiness.
- OpenPH compatibility against the updated honeybee-ph + PHX source graph:
  **29 focused OpenPH tests** and **4 openph-demand tests** passed. A direct
  Honeybee Room/HVAC → HBJSON → PHX → OpenPH matrix passed for no mechanical
  equipment and balanced systems with zero or two supply/exhaust ducts.
- Full PHX gate: Black and `git diff --check` passed; `python -m pytest
  tests/` passed with **901 tests**, **3 skipped**, and **1 deselected**.
- Final locked release gate against published `honeybee-ph==1.33.42`: Black,
  `uv lock --check`, and `git diff --check` pass; **907 tests** pass with
  **3 skipped** and **1 deselected** on Python 3.10.
