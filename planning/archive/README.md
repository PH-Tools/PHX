# planning/archive/ — completed & superseded work

Finished feature/refactor folders that have been folded back into `context/`/`docs/`, kept for history. Move a folder here (unchanged) when its work is `Complete` or `Superseded`; keep the flat `<slug>/` name so it stays findable by name.

This README is the index — scan or grep it instead of guessing dates. Add a row when you archive something.

| Item | Kind | Completed | Summary | Folder |
|------|------|-----------|---------|--------|
| PHPP writer zeroes the U-Values surface resistances | Bug fix | 2026-09-10 | `U-values!M10`/`M11` are PHPP's orientation and adjacency *selectors*, not resistance inputs; writing `0.0` took the `ISNUMBER` branch, so every assembly PHX wrote published a film-free U (+2.6% on a `U 0.150` declared assembly, +17% at `R 1.0`). PHPP write path only, no model change: selector strings resolved from the `face_type`/`exposure_exterior` of the Components referencing each assembly (ranked by area, warning on mixed use), `activate_variants` restores them instead of re-zeroing, `r_si`/`r_se` row-offset cross-wiring corrected. Strings, not numbers, so PHPP keeps the climate dependence of Rsi and the `Rse = Rsi` behavior of `3-Ventilated`. PR [#119](https://github.com/PH-Tools/PHX/pull/119), closes [#118](https://github.com/PH-Tools/PHX/issues/118). | [`phpp-surface-films/`](phpp-surface-films/README.md) |
| Declared-U Assembly: declared Layer thickness + sandwich collapse | Feature (additive) | 2026-09-10 | Reads `properties.ph.user_data["phn_declared_u"]` for the Layer thickness (R still comes from the Honeybee Material, so the U-value never moves) and collapses an exact marked no-mass sandwich to one Layer before the layers and exterior radiation properties are built. Malformed markers fall back to the 0.1 m default with a warning; unmarked `MAT_Mass` sandwiches untouched. PR [#117](https://github.com/PH-Tools/PHX/pull/117), closes [#116](https://github.com/PH-Tools/PHX/issues/116); spun off [#118](https://github.com/PH-Tools/PHX/issues/118). | [`declared-u-layer-thickness/`](declared-u-layer-thickness/README.md) |
| PHPP ventilator ID resolves to `None-<name>` | Bug fix | 2026-08-15 | Bounds the ventilator component-ID lookup to the entry section and raises on an empty ID cell instead of building `None-<name>`; fixes five section-locator off-by-ones and adds end-to-end write-path cover. | [`phpp-ventilator-id-lookup/`](phpp-ventilator-id-lookup/README.md) |
| Project-scoped deterministic identities | Architecture feature | 2026-08-14 | Isolates HB/WUFI identities per project, preserves explicit WUFI claims, validates exporter references, and removes public reference-test dependence on global resets. | [`project-scoped-identities/`](project-scoped-identities/README.md) |
| Explicit ventilation assignment semantics | Feature (cross-repo) | 2026-08-14 | Released PHX v1.56.79 with nullable assignments, mutation-free source preflight, aggregate readiness, target-local legacy mappings, and `honeybee-ph>=1.33.42`; published OpenPH v0.5.1 matrix passes. | [`ventilation-assignment-semantics/`](ventilation-assignment-semantics/README.md) |
| Public live Honeybee → PHX API | API/docs cleanup | 2026-08-14 | Adds the typed `PHX.conversion.from_honeybee()` facade, public option names, boundary diagnostics, equivalence tests, and corrected PHX/OpenPH documentation. | [`honeybee-conversion-facade/`](honeybee-conversion-facade/README.md) |
| Aperture-level Psi-Install (Install Types) | Refactor (cross-repo) | 2026-08-12 | Resolved per-edge psi-install on aperture elements; per-row PHPP write; content-keyed WUFI/METr window-type variant synthesis; from_WUFI explicit-0.0 fallback fix. | [`aperture-psi-install/`](aperture-psi-install/aperture-psi-install-plan.md) |
| HBJSON Space loads + utilization schedules | Bug fix | 2026-08-06 | Restores per-Space people loads, Honeybee schedule fallbacks, lighting EFLH, and stable WUFI occupancy round trips. | [`hbjson-occupancy-and-schedules/`](hbjson-occupancy-and-schedules/README.md) |
| Psi-install bug fixes | Refactor (cross-repo) | 2026-08-03 | Corrects WUFI, PHPP, PPP, and METr side/value handling plus upstream HBJSON robustness and GH construction ownership. | [`psi-install-bug-fixes/`](psi-install-bug-fixes/psi-install-bug-fixes-plan.md) |
| Write ventilation ducting to PHPP "Addl vent" | Feature | 2026-08-03 | Writes PHX ventilation ducts with localized geometry, type, and unit assignments plus row/unit capacity guards. | [`phpp-vent-ducting/`](phpp-vent-ducting/README.md) |

## Conventions

- **Flat by slug:** `planning/archive/<slug>/`. Do not nest by date.
- **Index here:** every archived item gets one row above (the completed date is a column).
- **If this ever gets long** (dozens+), bucket by year — `planning/archive/2026/<slug>/` — never by day.
- Canonical outcomes live in `context/` / `docs/`; this folder is history.

_(Legacy dated working notes live in the gitignored `plans/` folder, not here.)_
