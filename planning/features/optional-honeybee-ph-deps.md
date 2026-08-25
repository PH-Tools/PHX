# Optional `honeybee-ph` dependencies (Pollination integration)

**Status:** `Scoped` — researched and drafted 2026-04-02, **not implemented**. Re-verified
2026-08-25: no `HAS_PH` flag exists in `PHX/`, so nothing has landed.

## Why

Ladybug Tools wants PHX's WUFI/METr output available inside **Pollination**, where users
will not have `honeybee-ph`, `honeybee-energy-ph`, or `honeybee-phhvac` installed. Those
users would get a "bare" PHX model — geometry and assemblies only, no HVAC, no
certification data — rather than an `ImportError`.

## Scope (as measured 2026-04-02; re-measure before implementing)

- 29 module-level imports from `honeybee-ph` / `-energy-ph` / `-phhvac` across 10 files in
  `PHX/from_HBJSON/`.
- ~54 runtime `.properties.ph` accesses across 6 files.

## Approach

- Conditional imports behind a `HAS_PH` flag in `_type_utils.py`.
- Guard at two levels: `create_project.py` (entry) and `create_variant.from_hb_room()` —
  one `if` there skips 15 PH-only `add_*` calls.
- `cleanup.py` already try/excepts the PH imports; change the re-raise to set the flag.
- `create_building.py:389` already models the pattern with `getattr(..., "ph", None)`.
- Use walrus guards at access points.

## Open

Awaiting a decision to proceed — this is a real API-surface commitment, not just a refactor.

Original draft: `plans/20260402/optional-honeybee-ph-deps.md` (gitignored; this file is the
tracked summary).
