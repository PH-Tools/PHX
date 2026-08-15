# Planning Status

Master index of tracked planning work in PHX. Update when a unit of work is added, changes status, or is folded back into `context/`/`docs/`.

_Last updated: 2026-08-15_

## Active / current work

| Item | Kind | Status | Pointer |
|------|------|--------|---------|
| Public live Honeybee → PHX API | API/docs cleanup | **Complete** — verified and archived | [`archive/honeybee-conversion-facade/`](archive/honeybee-conversion-facade/PRD.md) |
| Aperture-bearing xl-replay golden fixture | Follow-up (manual) | **Open** — needs live Excel + licensed PHPP (`scripts/perf/record_replay_fixture.py`); covered by unit tests meanwhile | [`archive/aperture-psi-install/`](archive/aperture-psi-install/aperture-psi-install-plan.md) |
| Five PHPP inputs the writer never writes | Feature | **Requested** — dwelling units, summer heat-recovery mode, wind-protection class, `Ground`, climate-block name. All present in the PHX model; all left at blank-template defaults on export, three of them silently. Filed from OpenPH, where they cost a 3.4x error in annual useful cooling. Needs a scope decision (one packet, or split `Ground` out) | [`features/phpp-writer-input-gaps/`](features/phpp-writer-input-gaps/README.md) |
| Align `FloorAreaUtilizationZone` between WUFI and METr | Bug fix | **Filed** — exporter contract needs a source-of-truth decision | [`bug-fix/floor-area-utilization-zone.md`](bug-fix/floor-area-utilization-zone.md) |
| Component-ID lookups can still build `None-<name>` | Bug fix | **To investigate** — same silent exposure remains in the glazing / frame / constructor lookups; three per-lookup writeups filed, constructor is highest-priority (its search column also holds material-layer names). Needs a scope decision (bound only, or also hard-fail) | [`bug-fix/component-id-lookup-hardening.md`](bug-fix/component-id-lookup-hardening.md) |
| Decouple "Dwelling" from `Room.zone` | Refactor (cross-repo) | **Implemented** — awaiting step 3 (`honeybee_grasshopper_ph`), then the `hbph_test_models.gh` end-to-end run | [`refactor/dwelling-zone-decoupling.md`](refactor/dwelling-zone-decoupling.md) |

## Completed / archived work

| Item | Kind | Status | Pointer |
|------|------|--------|---------|
| PHPP ventilator ID resolves to `None-<name>` | Bug fix | **Complete** — entry-section bounding + loud failure, plus five locator off-by-ones; the originally-filed trigger never reproduced. 971 tests green, replay invariant unchanged; archived | [`archive/phpp-ventilator-id-lookup/`](archive/phpp-ventilator-id-lookup/README.md) |
| Project-scoped deterministic identities | Architecture feature | **Complete** — isolated HB/WUFI allocation, explicit claims, exporter validation, and full regression suite; archived | [`archive/project-scoped-identities/`](archive/project-scoped-identities/README.md) |
| Explicit ventilation assignment semantics | Feature (cross-repo) | **Complete** — PHX v1.56.79 released with `honeybee-ph>=1.33.42`; published OpenPH v0.5.1 matrix verified | [`archive/ventilation-assignment-semantics/`](archive/ventilation-assignment-semantics/README.md) |
| HBJSON Space loads + utilization schedules | Bug fix | **Complete** — seven phases implemented and verified; packet archived | [`archive/hbjson-occupancy-and-schedules/`](archive/hbjson-occupancy-and-schedules/README.md) |
| Aperture-level Psi-Install (Install Types) | Refactor (cross-repo) | **Complete** — merged (PR #80) + released v1.56.73; archived | [`archive/aperture-psi-install/`](archive/aperture-psi-install/aperture-psi-install-plan.md) |
| Psi-install bug fixes | Refactor (cross-repo) | **Complete** — eight phases published across PHX, honeybee_ph, and honeybee_grasshopper_ph | [`archive/psi-install-bug-fixes/`](archive/psi-install-bug-fixes/psi-install-bug-fixes-plan.md) |
| Write ventilation ducting to PHPP "Addl vent" | Feature | **Complete** — PHPP 10.6 row/formula check and full suite pass | [`archive/phpp-vent-ducting/`](archive/phpp-vent-ducting/README.md) |

## Cross-repo work

`aperture-psi-install` spans four repos. PHX holds the export-side heavy lifting: resolved
per-edge Ψ-install on the aperture element, PHPP per-row write, and the WUFI/METr window-type
variant synthesis. Blocked on the `honeybee_ph` primary shipping.

| Repo | Doc | Role |
|------|-----|------|
| `honeybee_ph` | `planning/refactor/aperture-psi-install.md` | Primary — data model + resolver + tests |
| `PHX` | [`archive/aperture-psi-install/`](archive/aperture-psi-install/aperture-psi-install-plan.md) | PHPP per-row write; WUFI/METr variant synthesis — **complete, archived** |
| `honeybee_grasshopper_ph` | `planning/refactor/aperture-psi-install.md` | Components; deletes the bug-#59 mechanism |
| `ph-navigator-v2` | `planning/features_v1.1/aperture-psi-install/upstream-alignment.md` | Phase-07 GH-client mapping |

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
