# planning/archive/ — completed & superseded work

Finished feature/refactor folders that have been folded back into `context/`/`docs/`, kept for history. Move a folder here (unchanged) when its work is `Complete` or `Superseded`; keep the flat `<slug>/` name so it stays findable by name.

This README is the index — scan or grep it instead of guessing dates. Add a row when you archive something.

| Item | Kind | Completed | Summary | Folder |
|------|------|-----------|---------|--------|
| Psi-install bug fixes | Refactor (cross-repo) | 2026-08-03 | Corrects WUFI, PHPP, PPP, and METr side/value handling plus upstream HBJSON robustness and GH construction ownership. | [`psi-install-bug-fixes/`](psi-install-bug-fixes/psi-install-bug-fixes-plan.md) |
| Write ventilation ducting to PHPP "Addl vent" | Feature | 2026-08-03 | Writes PHX ventilation ducts with localized geometry, type, and unit assignments plus row/unit capacity guards. | [`phpp-vent-ducting/`](phpp-vent-ducting/README.md) |

## Conventions

- **Flat by slug:** `planning/archive/<slug>/`. Do not nest by date.
- **Index here:** every archived item gets one row above (the completed date is a column).
- **If this ever gets long** (dozens+), bucket by year — `planning/archive/2026/<slug>/` — never by day.
- Canonical outcomes live in `context/` / `docs/`; this folder is history.

_(Legacy dated working notes live in the gitignored `plans/` folder, not here.)_
