# Planning Status

Master index of tracked planning work in PHX. Update when a unit of work is added, changes status, or is folded back into `context/`/`docs/`.

_Last updated: 2026-08-03_

## Active / current work

| Item | Kind | Status | Pointer |
|------|------|--------|---------|
| Psi-install bug fixes | Refactor (cross-repo) | **In progress** — Phases 1–7 complete; Phase 8 live GH check assigned to Ed | [`refactor/psi-install-bug-fixes-plan.md`](refactor/psi-install-bug-fixes-plan.md) |
| Decouple "Dwelling" from `Room.zone` | Refactor (cross-repo) | **Implemented** — awaiting step 3 (`honeybee_grasshopper_ph`), then the `hbph_test_models.gh` end-to-end run | [`refactor/dwelling-zone-decoupling.md`](refactor/dwelling-zone-decoupling.md) |

## Completed / archived work

| Item | Kind | Status | Pointer |
|------|------|--------|---------|
| Write ventilation ducting to PHPP "Addl vent" | Feature | **Complete** — PHPP 10.6 row/formula check and full suite pass | [`archive/phpp-vent-ducting/`](archive/phpp-vent-ducting/README.md) |

## Cross-repo work

`dwelling-zone-decoupling` spans three repos. PHX is the **downstream consumer**: it never
reads `Room.zone` (verified, 0 hits), so its role is to prove the upstream change is safe and
to retire a duplicated dwelling-aggregation helper. Deferrable without blocking the others.

| Repo | Doc | Role |
|------|-----|------|
| `honeybee_ph` | `planning/refactor/dwelling-zone-decoupling.md` | Primary — shared helper + tests |
| `honeybee_grasshopper_ph` | `planning/dwelling-zone-decoupling.md` | Root cause — the two `Room.zone` references |
| `PHX` | [`refactor/dwelling-zone-decoupling.md`](refactor/dwelling-zone-decoupling.md) | Downstream consumer — clearance + dedup |

## Note on legacy dated notes

Historical working notes live in the gitignored `plans/<YYYYMMDD>/` folders (e.g. pydantic-v2 migration, METr-JSON exporter, excel-interop refactor). Those are scratch/reference, not tracked planning — new tracked work should use `features/`/`refactor/` here.

## Update rule

When an item reaches `Complete`, fold its outcome into the relevant `context/` doc (or authoritative `docs/` deep-dive), then move its folder to `archive/<slug>/` and add a row to `archive/README.md`.
