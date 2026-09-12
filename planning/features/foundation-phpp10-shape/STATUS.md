# Status — Foundation model shape for PHPP 10.x `Ground`

**Status:** PHX model half merged to main — 2026-09-12 (PR
[#121](https://github.com/PH-Tools/PHX/pull/121), [#120](https://github.com/PH-Tools/PHX/issues/120)
Part A). The `05` `Ground` writer consuming it is merged too (PR
[#122](https://github.com/PH-Tools/PHX/pull/122), PHX 1.56.106). honeybee-ph
released 2026-09 (PH-Tools/honeybee_ph#111, merged #123, `honeybee-ph` **1.33.64**).

## Current state

Upstream shipped every PHPP 10.6 `Ground` input except `H48`. PHX mirrors it:

| Class | Field | Default | PHPP cell |
|---|---|---|---|
| `PhxSlabOnGrade` | `interior_wall_to_heated_area_m2` / `_u_value` | `0.0` / `0.0` | `H28` / `P28` |
| `PhxUnHeatedBasement` | `interior_wall_to_heated_area_m2` / `_u_value` | `0.0` / `0.0` | `H36` / `P36` |
| `PhxVentedCrawlspace` | `interior_wall_to_heated_area_m2` / `_u_value` | `0.0` / `0.0` | `H44` / `P44` |
| `PhxVentedCrawlspace` | `wind_velocity_at_10m_m_s` | `4.0` | `P42` |
| `PhxVentedCrawlspace` | `wind_shield_factor` | `0.05` | `P43` |

- `PhxHeatedBasement` gains nothing: PHPP has no `AwI` cell for it, and `C30` is
  absent from the `Ground!H51` conductance sum.
- `PhxSlabOnGrade` perimeter-insulation defaults moved `0.300/0.050/0.04` → `0.0/0.0/0.0`
  (PHPP 10.6 ships `Ground!H25:H27` blank). WUFI XML import is unaffected (it sets all
  three from the file); only a directly constructed slab changes.
- `from_HBJSON/create_foundations.py` needed no code (generic attribute copy);
  `tests/test_from_HBJSON/test_create_foundations.py` pins the flow.
- `pyproject.toml`: `honeybee-ph>=1.33.64`. Against an older honeybee-ph the copy has
  nothing to copy and PHX would silently keep its own defaults.
- No WUFI XML target for any new field.

## Decisions taken (PRD §6, settled upstream)

1. **Below-grade wall area: derived** at write time (`Awb = P × z`, `AW = P × h`); no
   authored area field. A stepped or partial basement gets its own issue if a project hits it.
2. **Slab perimeter-insulation defaults: `0.0`** ("none").
3. **`H48` phase-shift override: left out.**
4. **Interior-wall pair: per type, not hoisted** to the base class; heated basement
   excluded because PHPP has no slot.

Not done here (PRD §5, not in #120's scope): subclasses still do not set
`_foundation_type_num`; the `05` writer dispatches on the concrete subclass instead.

## Blocks

- [`../../bug-fix/phpp-writer-input-gaps/05-ground-worksheet-writer.md`](../../bug-fix/phpp-writer-input-gaps/05-ground-worksheet-writer.md)
  — done, merged in PR [#122](https://github.com/PH-Tools/PHX/pull/122).
- OpenPH `planning/features/ground-degree-hours-alignment/` Phases 03–04
  (foundation objects, fixture retype) — PHX side released (1.56.106); tracked in
  [Open-PH/openph-workspace#3](https://github.com/Open-PH/openph-workspace/issues/3).

## On completion

Write the OpenPH hand-off doc described in `PRD.md` §"Hand-off to OpenPH"
(`openph-workspace/planning/features/ground-degree-hours-alignment/upstream/phx-foundation-phpp10-shape.md`)
before marking this `Complete`. Owed once honeybee-ph (released), `honeybee-ph-schema`
(no issue or PR found yet), GH (PH-Tools/honeybee_grasshopper_ph#79) and PHX (1.56.106, done) are
released. The OpenPH side tracks it in
[Open-PH/openph-workspace#3](https://github.com/Open-PH/openph-workspace/issues/3).

## Cross-repo pointers

- `honeybee_ph/planning/STATUS.md` — cross-repo row added 2026-08-15.
- OpenPH packet decision D7 records this dependency.
