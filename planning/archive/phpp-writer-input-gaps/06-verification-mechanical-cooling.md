# `Verification!N30` "Mechanical cooling" is never written — and has no model source

**Status:** Scoped — needs a one-field model change in honeybee-ph first (cross-repo, honeybee-ph primary)
**Opened:** 2026-08-15
**Owner:** `PHX/PHPP/phpp_app.py` → `write_certification_config`; model: `PHX/model/certification.py::PhxSetpoints`; upstream: `honeybee_ph/bldg_segment.py::SetPoints`
**Umbrella:** [`README.md`](README.md)
**Filed from:** OpenPH `planning/features/ground-degree-hours-alignment/` (Root 2 of the `native_reference` ground degree-hours gap)
**Related:** [`01`](01-verification-version-guard.md) — same method, same shape file; `01` already notes this cell as "written by nothing"

## The defect

`phpp_localization/EN_10_6.json` (and all six other shape files) carry a
`mechanical_cooling` item:

```json
"mechanical_cooling": { "locator_col": "M", "locator_string": "Mechanical cooling:", "input_column": "N", "input_row_offset": 0 }
```

No `write_item` call uses it (`phpp_app.py:184-292` writes twelve inputs, not
this one), and **PHX has no attribute that could feed it** — `PhxSetpoints`
carries `winter`/`summer` only, and `PhxPhBuildingData` has no cooling flag.
The blank 10.6 template leaves `N30` empty, so every PHX → PHPP export
describes a building **without** mechanical cooling, whatever the model meant.

## What `N30` drives (verified in the blank 10.6 and a recalculated 10.6)

`Verification!AB30 = (N30="x")` and from there:

| Consumer | Effect when `N30` is blank |
|---|---|
| `Verification!I39` cooling & dehumidification demand | not reported (`I40` overheating frequency is reported instead) |
| `Ground!N122 = Verification!N30` → `Ground!E197 = MAX(P9, MIN(IF(N122="x", P10, MAX(P10, T_summer)), AVG(…)))` | the ground-iteration interior temperature **free-floats above the summer setpoint** — 30.8 °C in July on the OpenPH `native_reference` case; ground heating degree-hours came out **+18 %** against a model held at 25 °C |
| `Windows!AJ10:AJ14` | solar-load column switches between `Cooling` and `Summer` |
| `SummVent!L66 / R66` | overheating vs. active-cooling branch |

The `Ground` consequence is the one nobody expects: it changes *heating* demand
on a building with a slab, silently, and it is what surfaced this item.

## Why not derive it from cooling devices

`Verification!N30` means "this building is actively cooled to the summer
setpoint" — a boundary-condition statement, next to the setpoints on the sheet.
It is *correlated* with `mech_systems.cooling_devices` being non-empty, but not
equal to it: BLDGTYP's `linde_home` reference workbook (curated in PHPP by
hand) has `N30 = "x"` and its HBJSON has **no** PHX cooling device. Deriving
would silently flip that building. It needs an explicit, authored flag.

## The change (three repos, in order)

### 1. honeybee-ph — primary

`honeybee_ph/bldg_segment.py::SetPoints` gains `mechanical_cooling: bool =
False` (serialised as `mechanical_cooling` in `to_dict`/`from_dict`;
`duplicate`, `__eq__`, `ToString` updated). Default `False` because that is what
an un-authored PHPP describes, and the flag must be a conscious statement.

- Grasshopper: the setpoints/building-segment component gains a
  `mechanical_cooling_` boolean input (`honeybee_grasshopper_ph`).
- `honeybee-ph-schema`: add the field to the `SetPoints` schema; regenerate.
- Tests: round-trip, default, GH input.

Placing it on `SetPoints` rather than on `PhiCertification`: it is a modelling
boundary condition, it sits with the setpoints in PHPP's own UI
(`Verification!E28:N30` "Boundary conditions"), and it is not PHI-specific
(Phius/WUFI models can carry it too, even if WUFI has no single field for it —
see below).

### 2. PHX — model + writer

- `PHX/model/certification.py::PhxSetpoints.mechanical_cooling: bool = False`;
  `from_HBJSON/create_variant.py` copies it from `SetPoints`.
- `write_certification_config`: one more `VerificationInput.item(...)` after
  `setpoint_summer`, `input_type="mechanical_cooling"`, `input_data="x" if
  setpoints.mechanical_cooling else ""` — the `x`-cell vocabulary from the
  umbrella README (`""` to clear, never `None`). It belongs in the *item*
  block, so it lands regardless of the version guard once [`01`](01-verification-version-guard.md)
  narrows it — sequence this after `01`.
- `from_WUFI_XML`: there is no single WUFI element for this. Leave `False` on
  import and say so in the reader docstring; do **not** infer from cooling
  distribution nodes (same reasoning as above). `to_WUFI_XML`: no target;
  nothing written.
- Tests: `tests/test_PHPP/test_phpp_app_verification.py` (created by `01`)
  gains a case asserting `Verification!N30` = `"x"` / `""` for the two flag
  states.

### 3. Downstream consumers (for information; not this repo)

- **OpenPH** hardcodes `OpPhPHPP.active_cooling_on = True` ("To Do: Get from
  Model"). Once the flag exists it reads it from
  `variant.phius_cert.ph_building_data.setpoints.mechanical_cooling`, and its
  committed reference HBJSONs (`linde_home`, `adelphi`, `native_reference`)
  need the flag set `True` to keep matching their `N30 = "x"` workbooks.
  Tracked in `openph-workspace/planning/features/ground-degree-hours-alignment/`
  (decision D2 follow-up).
- **BLDGTYP `tools/write_native_reference_phpp.py`** does *not* patch `N30`
  (Ed's call 2026-08-15: fix it here, not there); it only audits the computed
  observable (`max(Ground!E197:P197) <= Ground!P10`) once PHX writes the cell.

## Phases

### Phase 0 — honeybee-ph field lands and is released
Nothing here can be tested end-to-end until the HBJSON carries the flag.
Cross-repo pattern as `default-ventilation-system-factory` (honeybee-ph
primary, PHX follows with a pinned minimum version).

### Phase 1 — PHX model + reader
`PhxSetpoints.mechanical_cooling`; `create_variant.py` copy; `PhxSetpoints.__eq__`.
**Verify:** unit test on the HBJSON → PHX path with the flag on and off.

### Phase 2 — writer
The `write_item` call. **Verify:** the `01` test module case; the fake-XL
framework shows exactly one new cell (`Verification!N30`).

### Phase 3 — replay fixture
`Single_Zone.hbjson` will not carry the flag until regenerated; the fixture then
gains one cell. Re-record with live Excel per the umbrella README, or note the
`EXTRA write` as expected until the next recording.

### Phase 4 — closeout
Docs (`docs/reference/phx-model-reference.md` PHX→PHPP table:
`Verification!N30`), umbrella README table (six items), `planning/STATUS.md`,
and a pointer in `honeybee_ph/planning/STATUS.md` cross-repo table.

## Hand-off to OpenPH — required on completion

OpenPH is the consumer of this change and its work is blocked on it. When this
item (and its honeybee-ph half) is **done and released**, write a **new** doc —
do not just edit this one — at

```
openph-workspace/planning/features/ground-degree-hours-alignment/upstream/phx-06-mechanical-cooling.md
```

(if that packet has been archived, put it in the archived folder's `upstream/`
and say so in `openph-workspace/planning/STATUS.md` or the successor packet).
Front matter `DATE`/`STATUS`/`SCOPE`/`RELATED`; contents:

- Released versions: `honeybee-ph`, `honeybee-ph-schema`, `honeybee_grasshopper_ph`,
  `PHX` — the exact version strings OpenPH should pin.
- The field as shipped: honeybee-ph attribute path and JSON key
  (`SetPoints.mechanical_cooling` / `set_points.mechanical_cooling`), the PHX
  path (`PhxSetpoints.mechanical_cooling`), type, default, and how a legacy
  HBJSON without the key reads (`False`).
- What PHX writes: worksheet/cell (`Verification!N30`), the values for
  True/False (`"x"` / `""`), and where in `phpp_app.py` (method name).
- Any deviation from this doc's plan, and why.
- Test names that prove it (honeybee-ph round-trip, PHX writer test), so OpenPH
  can cite them.
- One line on what OpenPH must do next (read the flag in `from_phx_variant`;
  patch the three fixture HBJSONs; retire nothing in `tools/` — that tool never
  wrote `N30`).

Then update `openph-workspace/planning/features/ground-degree-hours-alignment/STATUS.md`
"Blockers" to point at the new doc. That folder's `upstream/README.md`
describes the same expectation from the OpenPH side.

## Acceptance

- A model with `mechanical_cooling = True` exports `Verification!N30 = "x"`;
  `False` exports `""`; a recalculated 10.6 shows `Verification!AB30` TRUE/FALSE
  accordingly and `Ground!N122` following it.
- The flag round-trips through HBJSON in honeybee-ph and reaches
  `PhxSetpoints` unchanged.
- No inference from cooling devices anywhere in the path.
