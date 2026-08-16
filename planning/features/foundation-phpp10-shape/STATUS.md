# Status — Foundation model shape for PHPP 10.x `Ground`

**Status:** Scoped — 2026-08-15. No code changed in any repo.

## Current state

Gap analysis done ([`PRD.md`](PRD.md) §3): seven PHPP 10.6 `Ground` inputs have
no source in the honeybee-ph/PHX foundation model — the "interior wall towards
heated" area/U pair on slab-on-grade, unheated basement and crawl space
(`H28/P28`, `H36/P36`, `H44/P44`), and the crawl-space wind shield factor
(`P43`). Everything else is present or exactly derivable. Three small model
defects noted alongside (`_foundation_type_num` never set by subclasses;
crawlspace perimeter default 2.5; slab defaults imply insulation).

## Blocks

- [`../../bug-fix/phpp-writer-input-gaps/05-ground-worksheet-writer.md`](../../bug-fix/phpp-writer-input-gaps/05-ground-worksheet-writer.md)
  — Phase 2 (model layer) should consume the finished shape rather than
  hardcode "template default" for four cell pairs. `05` Phase 0/1 (corpus,
  shape file) can proceed in parallel.
- OpenPH `planning/features/ground-degree-hours-alignment/` Phase 02
  (foundation objects) — waits for the honeybee-ph + PHX releases.

## Open decisions (Ed) — see PRD §6

1. Below-grade wall area derived (recommended) vs explicit.
2. Slab perimeter-insulation defaults → "none" (recommended) vs WUFI parity.
3. `H48` phase-shift override — leave out (recommended).
4. Hoist `interior_wall_to_heated_*` to the base class (recommended).

## Next step

Ed confirms §6; then honeybee-ph implements §4 (primary), releases; schema and
GH follow; PHX implements §5 with a pinned `honeybee-ph>=` minimum; then `05`
Phase 2 onward.

## On completion

Write the OpenPH hand-off doc described in `PRD.md` §"Hand-off to OpenPH"
(`openph-workspace/planning/features/ground-degree-hours-alignment/upstream/phx-foundation-phpp10-shape.md`)
before marking this `Complete`.

## Cross-repo pointers

- `honeybee_ph/planning/STATUS.md` — cross-repo row added 2026-08-15.
- OpenPH packet decision D7 records this dependency.
