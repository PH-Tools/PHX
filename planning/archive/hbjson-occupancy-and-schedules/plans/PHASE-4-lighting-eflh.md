# Phase 4 — Report lighting full-load hours as EFLH

**Status:** Complete — 5 boundary tests, Excel replay, and the 850-test full gate pass.

**Depends on: Phase 3. Dependency satisfied.**

Phase 3 populates `relative_utilization_factor` on every schedule. This phase must remain after
Phase 3; reversing the order would collapse full-load hours from `8760` to **`0`** — a
plausible-looking number with a silent failure mode.

---

## Context

```python
# PHX/model/schedules/lighting.py:117-119
@property
def full_load_lighting_hours(self) -> float:
    """Return the annual full-load lighting hours, clamped to 0-8760."""
    return max(0, min(8760, self.annual_operating_hours))
```

`annual_operating_hours` is `annual_utilization_days * daily_operating_hours` — the **window**,
not the **load**. `relative_utilization_factor` is never applied, so with the `0-24 / 365` shape
every space reports `8760`: lights at full rated power every hour of the year.

Consumed at `to_WUFI_XML/xml_schemas.py:1881` (`<LightingFullLoadHours>`) and
`to_METr_JSON/metr_schemas.py:1194` (`lFLoadH`).

## Why this is a plain bug, not a judgment call

`LightingFullLoadHours` is **EFLH** — Equivalent Full Load Hours in LEED/COMNET terms — which is
by definition `SUM(hourly load fraction)` over the year, i.e. `8760 x mean`. From the 2021 Phius
thread (`../phius-correspondance-background/`, read order 01 → 03 → 02):

> *"one pattern for the space covering occupancy, and then use the **utilization full hours,
> EFLH in LEED speak**, to cover the electrical and lighting loads"* — Al Mitchell, Sep 28
>
> *"the **EFLH overrides the lighting**, which is to our advantage for simplicity"* — Al, Oct 7

Two consequences:

1. EFLH is meant to be set **directly** — WUFI's own files write `0` there, which is simply what
   you get when nobody sets it. PHX deliberately diverges. `RoomCategory` pointing at the
   occupancy pattern (`xml_schemas.py:1865`) is correct and stays.
2. Because EFLH **overrides** the lighting pattern, the wrong number is the *governing* one.
   Nothing downstream corrects it.

Defects 2 and 3 are one protocol (D8): Phase 3 supplies the shape, Phase 4 supplies the
multiplication, and together they produce exactly `8760 x mean` = EFLH.

**Applies to all models, residential included (D10)** — the WUFI A/B run showed the field is
inert for `BuildingCategory=1`, so there is no re-certification risk.

---

## Files you may touch

```
PHX/model/schedules/lighting.py
tests/test_model/                                (add the boundary tests)
```

---

## The change

```python
@property
def full_load_lighting_hours(self) -> float:
    """Return the annual equivalent full-load lighting hours (EFLH), clamped to 0-8760.

    EFLH is the LOAD-weighted hour count -- SUM(hourly load fraction) over the year --
    not the operating window. Per the 2021 Phius protocol this value OVERRIDES the
    lighting utilization pattern in WUFI (the pattern reference points at the
    occupancy pattern), so it must carry the load, not the window.
    """
    return max(0, min(8760, self.annual_operating_hours * self.relative_utilization_factor))
```

That is the whole change. Do not touch anything else in the class.

---

## Guardrails

- **Verify Phase 3 has landed** before starting. Check that
  `PhxScheduleLighting.relative_utilization_factor` is nonzero for a stock HB schedule; if it is
  `0.0`, Phase 3 is not in and this change will produce `0`.
- **Do not** change `RoomCategory` / `IdentNrUtilizationPattern` to point at a separate lighting
  pattern. Referencing the occupancy pattern is the agreed Phius protocol.
- **Do not** apply the same multiplication to `PhxScheduleOccupancy` — it has no equivalent
  consumer, and its factor is already exported directly as `RelativeAbsenteeism`.

---

## Tests

`tests/test_model/test_schedules/test_lighting_eflh.py`

```python
def test_eflh_applies_the_utilization_factor():
    """0-24h, 365d, factor 0.2917 -> 2555 h, not 8760."""

def test_eflh_at_full_utilization_equals_the_window():
    """factor 1.0 -> annual_operating_hours unchanged."""

def test_eflh_at_zero_utilization_is_zero():
    """factor 0.0 -> 0 h."""

def test_eflh_is_clamped_to_8760():
    """A schedule whose window x factor would exceed 8760 must clamp."""

def test_eflh_is_never_negative():
    """Lower clamp holds."""
```

---

## Verification gate

```bash
python -m pytest tests/test_model/ -v
python -m pytest tests/test_xl_replay/ -v      # MUST be unchanged
python -m pytest tests/
```

Expected values after Phases 3 + 4:

| model | lighting schedule | mean | EFLH before | EFLH after |
|---|---|---|---|---|
| 39 15th St | `OfficeSmall BLDG_LIGHT_SCH_2013` | 0.3436 | 8760 | **3010** |
| `Default_Model_Single_Zone` | `Generic Office Lighting` | 0.2917 | 8760 | **2555** |
| `Multi_Room_Complete` | `hbph_sfh_Lighting` | 0.0417 | 8760 | **365** |

If any of these comes out `0`, Phase 3 has not landed — stop and check.

Golden movement: `LightingFullLoadHours` (WUFI) and `lFLoadH` (METr) only.

---

## Definition of done

- [x] All five boundary tests pass
- [x] The three corpus models produce 3010 / 2555 / 365 — **none of them 0**
- [x] Golden movement confined to `LightingFullLoadHours` / `lFLoadH`
- [x] `tests/test_xl_replay/` unchanged

## Commit

```
fix(model): report lighting full-load hours as EFLH (load-weighted), not the operating window
```
