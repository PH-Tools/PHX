# planning/

Tracked working plans for PHX. See [`.instructions.md`](.instructions.md) for the rules and folder contract.

**Read order:** [`STATUS.md`](STATUS.md) first — it indexes active work and points to the right folder.

## Layout

- `STATUS.md` — master index of active features/refactors.
- `features/` — plans for new capabilities.
- `refactor/` — cross-cutting refactor investigations.
- `archive/` — completed/superseded work, flat by slug, indexed in `archive/README.md`.

**Not this folder:** `plans/` (gitignored) holds dated scratch notes, licensed PHPP fixtures, and perf scratch referenced by `scripts/perf/`. Committed planning lives here in `planning/`.

When an item is done, fold its outcome into `context/` (or the authoritative `docs/` deep-dives), then move its folder into `archive/<slug>/` and add a row to `archive/README.md`.
