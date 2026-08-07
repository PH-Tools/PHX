# Phase 3 — HB-style fallback for occupancy and lighting schedules

**Status:** Complete — 8 focused tests, Excel replay, and the 845-test full gate pass.

**Depends on:** Phase 2. Dependency satisfied; Phase 4 is unblocked.

---

## Context

`build_ventilation_schedule_from_hb_room()` (`create_schedules.py:139-176`) already does the
right thing: it checks whether the HB schedule carries detailed PH operating periods, and falls
back to deriving them from the raw E+ values when it does not.

`build_occupancy_schedule_from_hb_room()` (`:179-217`) and
`build_lighting_schedule_from_hb_room()` (`:220-258`) have **no such fallback**. They read
`schedule.properties.ph` directly. When `daily_operating_periods` is empty:

| property | value | why |
|---|---|---|
| `first_operating_period` | `None` | → start/end forced to `0` / `24` |
| `annual_average_operating_fraction` | `0.0` | empty loop ÷ 8760 (`ruleset.py:214-227`) |
| `operating_days_year` | `365.0` | `52.1429 x 7` default |

Which produces exactly the degenerate `Begin 0 / End 24 / 365 days / Relative absence 0` row
that started this investigation.

**This affects every project, residential included.** The honeybee-ph residential standards ship
with no PH properties at all (`hbph_sfh_occupancy.json` → `hbph_sfh_Occupant_Presence -> {}`).

## The protocol (authority: the 2021 Phius thread)

From `../phius-correspondance-background/` — **read order 01 → 03 → 02**, the filenames do not
sort chronologically.

> *"set the start / end to 0 and 24 respectively, and 365 days, then calc the annual util factor
> based on the OpenStudio hourly values, and input that as the use-factor"* — Ed → Al, Sep 24

Al did not object, and the shape is what the WUFI screenshots in that thread show. So the
fallback is:

```
start_hour = 0
end_hour = 24
annual_utilization_days = 365
relative_utilization_factor = mean(schedule.values())
```

## Two things already settled

- **`RelativeAbsenteeism` is a UTILIZATION factor, not an absence factor (D7).** PHX's existing
  mapping is correct — do not invert it. Confirmed by the Phius standards library: an open
  office at `1.0`, a public restroom at `0.1`. The reverse reading is absurd.
- **This applies to all models, residential included (D10).** The WUFI A/B run showed the field
  is inert for `BuildingCategory=1`, so there is no re-certification risk and no reason to gate
  by building category.

---

## Files you may touch

```
PHX/from_HBJSON/create_schedules.py
tests/test_from_HBJSON/test_create_schedules/    (new dir + tests)
```

---

## The change

Mirror the ventilation structure at `:139-176` exactly.

### 1. Add the "has PH-style data?" predicates

Model on `_room_has_ph_style_ventilation()` (`:23-49`):

```python
def _room_has_ph_style_occupancy(_hb_room: room.Room) -> bool:
    """True if the Room's occupancy schedule has detailed PH-style operating periods."""
    try:
        hbe_sched = get_people_schedule(_hb_room)
    except MissingEnergyPropertiesError:
        return False
    prop_ph: phx_ruleset.ScheduleRulesetPhProperties = hbe_sched.properties.ph
    return bool(prop_ph.daily_operating_periods)
```

Same shape for `_room_has_ph_style_lighting()` using `get_lighting_schedule`.

### 2. Split each builder into `_ph_style` / `_hb_style`

The `_ph_style` variants are today's bodies **moved verbatim**. R10 requires their output be
bit-identical for any schedule that does carry PH periods — this is a pure extract-method, no
behavior change on that branch.

```python
def build_occupancy_schedule_from_hb_room(_hb_room) -> occupancy.PhxScheduleOccupancy | None:
    try:
        get_people_schedule(_hb_room)
    except MissingEnergyPropertiesError:
        return None
    if _room_has_ph_style_occupancy(_hb_room):
        return _create_occupancy_schedule_from_ph_style(_hb_room)
    return _create_occupancy_schedule_from_hb_style(_hb_room)
```

### 3. The `_hb_style` variants

Assign through the existing **`annual_utilization_factor` setter**
(`PHX/model/schedules/occupancy.py:70-82`, `lighting.py:84-96`) rather than hand-setting four
fields — that setter already writes `0 / 24 / 365 / factor`, so the shape has one definition:

```python
def _create_occupancy_schedule_from_hb_style(_hb_room) -> occupancy.PhxScheduleOccupancy:
    """Derive a PH-style pattern from a raw HB/E+ hourly schedule.

    Per the 2021 Phius protocol: 0-24h, 365 days, with the annual mean of the
    hourly values as the utilization factor. Equivalent in
    `annual_utilization_factor` terms to the explicit-window PH-style form.
    """
    hbe_sched = get_people_schedule(_hb_room)
    new_sched = occupancy.PhxScheduleOccupancy()
    new_sched.identifier = hbe_sched.identifier
    new_sched.display_name = hbe_sched.display_name
    new_sched.annual_utilization_factor = mean(hbe_sched.values())
    return new_sched
```

### 4. Keep the ID alignment identical across both branches

**This is the trap in this phase.** The schedule collection is keyed on `identifier`, and
`metr_schemas.py:1180/1203` and `xml_schemas.py:1853/1865` reference `schedule.id_num`. Getting
it wrong silently re-points a Space's utilization pattern at a different room's schedule — no
crash, no test failure, wrong model.

Mirror whatever `_create_vent_schedule_from_ph_style()` / `..._from_hb_style()` do for
`identifier`, `display_name`, and `id_num`, on **both** branches.

---

## Guardrails

- **Do not touch** `PHX/model/schedules/lighting.py` — that is Phase 4.
- **Do not** invert `relative_utilization_factor` into an absence factor (D7).
- **Do not** gate by building category (D10).
- These builders run per **HB room** in
  `add_all_HB_Model_occupancy_schedules_to_PHX_Project()` (`:335-363`) — i.e. **pre-merge**, so
  the room in hand is already the original. No `_space.host` indirection needed here.

---

## Tests

`tests/test_from_HBJSON/test_create_schedules/test_hb_style_fallback.py`

### The derived factor

```python
def test_no_ph_periods_uses_annual_mean():
    """A stock HB schedule -> 0/24/365 with the annual mean as the factor."""
```

Expected values from the corpus:

| model | schedule | mean |
|---|---|---|
| 39 15th St | `OfficeSmall BLDG_OCC_SCH` | 0.2867 |
| `Default_Model_Single_Zone` | `Generic Office Occupancy` | 0.2886 |
| `Multi_Room_Complete` | `hbph_sfh_Occupant_Presence` | 0.7208 |
| `Multi_Room_Complete` | `hbph_sfh_Lighting` | 0.0417 |

### R10 — the PH-style branch is unchanged

```python
def test_ph_style_schedule_output_is_unchanged():
    """A schedule WITH operating periods must produce byte-identical output."""
```

### R11 — the two shapes agree

```python
def test_annual_utilization_factor_is_preserved_across_shapes():
    """Converting a PH-style pattern to its HB-style equivalent must preserve
    annual_utilization_factor.

    Phius 'Office Workspace Open': 7-18h, 250 days, factor 1.0
        PH-style  (11 * 250 / 8760) * 1.0        = 0.313927
        HB-style  (24 * 365 / 8760) * 0.313927   = 0.313927
    """
```

Better than asserting magic numbers — it tests the property the Phius protocol actually cares
about, and it is the equivalence Ed proposed and Al accepted.

### ID alignment

```python
def test_schedule_id_alignment_is_identical_across_branches():
    """identifier / display_name / id_num must line up the same way whether the
    schedule came from the ph_style or hb_style branch."""
```

---

## Verification gate

```bash
python -m pytest tests/test_from_HBJSON/test_create_schedules/ -v
python -m pytest tests/test_xl_replay/ -v      # MUST be unchanged
python -m pytest tests/
```

Golden movement confined to these fields and their METr equivalents:

```
BeginUtilization  EndUtilization  AnnualUtilizationDays  RelativeAbsenteeism
```

`LightingFullLoadHours` will **still read 8760** after this phase — the window is now
`0-24 x 365` and the factor is not yet applied. That is expected. Phase 4 fixes it.

Anything outside those four fields moving means the ID alignment is wrong.

---

## Definition of done

- [x] `relAbs` equals the annual mean on all corpus models
- [x] PH-style fixture output byte-identical (R10)
- [x] R11 equivalence test passes
- [x] ID alignment test passes
- [x] Golden movement confined to `Multi_Room_Complete.xml` `RelativeAbsenteeism`
- [x] `tests/test_xl_replay/` unchanged

## Commit

```
fix(from_hbjson): derive occupancy and lighting utilization patterns from HB schedules when no PH operating periods are set
```
