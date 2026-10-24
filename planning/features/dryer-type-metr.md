---
DATE: 2026-10-24
STATUS: In progress (stage 1 implemented on branch `fix/dryer-type-metr-01`)
AUTHOR: Ed May, Claude
ISSUE: https://github.com/PH-Tools/PHX/issues/160
REPOS: PHX (primary), honeybee_ph, honeybee_grasshopper_ph
---

# Clothes-dryer type: METr heat pump (7) and per-type `refED` / `rDamp`

## Outcome

One dryer type keeps serving WUFI-Passive, METr and PHPP. No `Dryer-WUFI` / `Dryer-METr`
split: METr kept WUFI's codes 1–6 in the same order with new labels, and added one code.

The work:

1. The PHX METr writer sets `refED` and `rDamp` from the dryer type, the way METr itself does.
   Today it writes `refED = 4` and `rDamp = NaN` for every dryer, so clothes-line, drying-closet
   and gas dryers reach METr with the wrong energy-demand reference.
2. `7` (METr "Ventless: Heat Pump") becomes a valid dryer type. METr receives it as-is; WUFI and
   PHPP, whose lists stop at 6, receive `4` with a warning.
3. The Grasshopper `dryer_type` hover text lists all seven with both the WUFI/PHPP and METr names.

## Evidence

### METr's own saves (Ed, 2026-10-24)

Ed set the dryer in one METr model to each type in turn and saved after each:
`~/Downloads/{clothes-line, drying-closet, drying-closet-at-exhaust, ventless-condensing,
vented-electric, vented-natural-gas, ventless-heat-pump}.json`. These are project models and are
not committed. The dryer is `lVariant[0].building.lZone[0].loadsZ.lHomeDev[3]`. A full-file diff
showed only these keys change between the seven:

| METr label | `tDryer` | `refED` | `rDamp` | `enDrY` | WUFI `Dryer_Choice` / PHPP selector |
|---|---|---|---|---|---|
| Clothesline | 1 | 3 | 0.5 | 1234 | 1-CLOTHES LINE |
| Drying closet (cold) | 2 | 3 | 0.5 | 1234 | 2-DRYING CLOSET (COLD!) |
| Drying closet (cold) at exhaust | 3 | 3 † | 0.5 † | 1234 | 3-DRYING CLOSET (COLD!) IN EXTRACT AIR |
| Ventless: Condensation | 4 | 4 | NaN | 0 | 4-CONDENSATION DRYER |
| Vented: Electric | 5 | 4 | NaN | 0 | 5-ELECTRIC EXHAUST AIR DRYER |
| Vented: Natural Gas | 6 | 9 | NaN | 0 | 6-GAS EXHAUST AIR DRYER |
| Ventless: Heat Pump | 7 | 4 | NaN | 0 | none |

† From a second save (`02-drying-closet-cold-at-exhaust.json`, 2026-10-24), made by switching
from Clothesline. The first type-3 save, made right after `ventless-condensing`, showed
`refED 4` / `rDamp NaN`: METr does not reset those fields when switching from a CEF type.

The `1234` values are what Ed typed into the yearly-energy and gas-consumption fields; they show
which field each `refED` reads (`refED 3` → `enDrY`, kWh/yr).

### Other tools' lists

- WUFI-Passive: `indexListPH_HomeDevice_3` stops at 6 ("Clothesline" … "Gas exhaust air dryer"),
  `wufi-passive/research/decompiled/WUFIplus/SC_ProgData.cs:4626`.
- PHPP 9.6A, 9.7IP, 10.6: `clothes_drying.selection_options` stops at 6,
  `PHX/PHPP/phpp_localization/EN_*.json`.

### How WUFI uses the type (`dPH_HomeDevice.cs`, dryer branch, ~l.295–360)

- Choices 4/5/6 read CEF when the reference norm is 2 (forced to 2 under Phius); choices 1/2/3
  read the normal energy-demand field.
- Choice 6 renames `EfficiencyFactorGas` to "CEF - Gas" and reads `GasConsumption`.
- `ResidualDampness` (XML `rDamp`) is read for choices 1/2/3, and for every choice outside Phius.
  Under Phius, choices 4/5/6 use a fixed 0.6 instead.

METr's `refED` per type follows the same split: 3 (yearly energy) for 1/2/3, 4 (CEF) for 4/5/7,
9 for gas.

### Current code

- `PHX/to_METr_JSON/metr_schemas.py` `_PhxElectricalDevice`, dryer branch: `dev["refED"] = 4`
  for every dryer; `rDamp` stays at the shared default `NaN`.
- `PHX/to_WUFI_XML/xml_schemas.py` `_PhxDeviceClothesDryer`: writes `Dryer_Choice` as given,
  never writes `rDamp`.
- `PHX/PHPP/phpp_model/electricity_item.py` `_clothes_dryer`:
  `selection_options[str(equip.dryer_type)]` raises `KeyError` for 7.
- `honeybee_ph/honeybee_energy_ph/load/_ph_equip_types.py` `PhClothesDryerType.allowed`: six
  values. `CustomEnum` serializes the label string (`{"value": "5-ELECTRIC EXHAUST AIR DRYER"}`)
  and accepts an int by list position, so appending a seventh entry leaves old HBJSON loading
  unchanged. The existing six strings must not be reworded.
- `PHX/from_HBJSON/create_elec_equip.py` copies `PhClothesDryerType.number` to the PHX int, so a
  seventh entry reaches PHX as `7` with no change there.
- `PHX/model/elec_equip.py` `PhxDeviceClothesDryer.dryer_type` is a plain int; no validation.
- Reference output `tests/reference_files/*/metr_json/Multi_Room_Complete.json` has one dryer,
  type 5, `refED 4`. It does not move under this change.

## Scope

In:

- METr writer: `refED` and `rDamp` per dryer type.
- Type 7 end to end: honeybee_ph enum, METr passthrough, WUFI and PHPP fallback to 4 with a
  warning.
- Grasshopper hover text for `dryer_type`.

Out (noted, not changed here):

- A user input for residual dampness (see Q2).
- `PhClothesDryer.annual_energy_kWh` in honeybee_ph uses CEF for every dryer type, including
  clothesline and drying closets. Only affects honeybee_ph's own estimate, not the exports.
- Default dryer type differs: honeybee_ph 5 (electric exhaust), PHX 4 (condensation).

## Plan

Stages are ordered so each lands on its own. Stages 1 and 2 need nothing from honeybee_ph,
because the PHX model's `dryer_type` is a plain int.

### Stage 1: PHX METr writer, per-type `refED` / `rDamp`

**Implemented on branch** `fix/dryer-type-metr-01` (2026-10-24). Evidence: parametrized test
`test_dryer_type_sets_ref_ed_and_residual_dampness` over types 1–7; full suite green;
`context/METR.md` §2 dryer row updated.

`to_METr_JSON/metr_schemas.py`, dryer branch:

```python
# -- METr 'Energy demand (norm) reference' and 'Remaining dampness', by dryer type.
# -- 1/2/3 clothesline + drying closets: yearly energy (enDrY); 4/5/7: CEF; 6 gas: CEF - Gas
METR_DRYER_REF_ED = {1: 3, 2: 3, 3: 3, 4: 4, 5: 4, 6: 9, 7: 4}
METR_DRYER_RESIDUAL_DAMPNESS = 0.5
...
dev["refED"] = METR_DRYER_REF_ED.get(_d.dryer_type, 4)
if _d.dryer_type in (1, 2, 3):
    dev["rDamp"] = METR_DRYER_RESIDUAL_DAMPNESS
```

Tests (`tests/test_to_METr_JSON/test_metr_schemas.py`): one parametrized test over types 1–7
asserting `tDryer`, `refED` and `rDamp`, against the table above.

### Stage 2: PHX type 7 fallback for WUFI and PHPP

- `to_WUFI_XML/xml_schemas.py`: write `Dryer_Choice` 4 when the type is 7, log a warning naming
  the device.
- `PHPP/phpp_model/electricity_item.py`: same mapping before the `selection_options` lookup.
- One shared helper on the PHX side (e.g. `PhxDeviceClothesDryer.wufi_phpp_dryer_type`) so both
  writers use the same mapping.

Tests: WUFI writer and PHPP writer each get a type-7 case asserting `4`; a type-5 case stays `5`.

### Stage 3: honeybee_ph enum

Append `"7-HEAT PUMP DRYER"` to `PhClothesDryerType.allowed`.

Tests (`tests/test_honeybee_energy_ph/test_load/test_ph_equipment.py`): `PhClothesDryer` with
`dryer_type = 7` round-trips through `to_dict`/`from_dict`; a dict with
`"5-ELECTRIC EXHAUST AIR DRYER"` still loads as 5.

After release, PHX's honeybee-ph pin moves through the release orchestrator as usual. Add one
PHX `from_HBJSON` test that a type-7 HBPH dryer reaches the METr JSON as `tDryer 7` and the WUFI
XML as `Dryer_Choice 4`.

### Stage 4: honeybee_grasshopper_ph hover text

`honeybee_ph_rhino/gh_compo_io/program/create_elec_equip.py`, `dryer_type` description. Draft:

```
WUFI/METr 'Type of laundry-dryer' and the PHPP dryer selector. Input either -
 "1-CLOTHES LINE" (METr: Clothesline)
 "2-DRYING CLOSET (COLD!)" (METr: Drying closet (cold))
 "3-DRYING CLOSET (COLD!) IN EXTRACT AIR" (METr: Drying closet (cold) at exhaust)
 "4-CONDENSATION DRYER" (METr: Ventless: Condensation)
 "5-ELECTRIC EXHAUST AIR DRYER" (METr: Vented: Electric)
 "6-GAS EXHAUST AIR DRYER" (METr: Vented: Natural Gas)
 "7-HEAT PUMP DRYER" (METr: Ventless: Heat Pump). METr only; WUFI and PHPP receive 4.
```

Also update the dryer rows in `planning/elec-equip-input-labels.md`. Lands after the honeybee_ph
release that adds 7; before then, a `7` input raises in honeybee_ph.

## Verification

- PHX and honeybee_ph test suites green.
- Ed: export one model per dryer type 1, 2, 3, 6, 7 to METr JSON with PHX, load each in METr,
  and confirm the dryer panel shows the right type, the right "Energy demand (norm) reference",
  and no import error. Compare the dryer's result against the same type set by hand in METr.
- Ed: open a type-7 WUFI XML export in WUFI-Passive; it should show "Condensation dryer".

## Decisions (Q1–Q6, all resolved 2026-10-24)

- **Q1. Type 3 `refED`.** Resolved (METr re-save, 2026-10-24): `refED 3`, `rDamp 0.5`, same as
  types 1 and 2.
- **Q2. `rDamp` source.** Decided (Ed, 2026-10-24): fixed 0.5 for types 1–3. No new field.
- **Q3. `rDamp` in WUFI XML.** Decided (Ed, 2026-10-24): no change; the WUFI XML still omits
  `rDamp`.
- **Q4. Label for 7.** Decided (Ed, 2026-10-24): `"7-HEAT PUMP DRYER"`.
- **Q5. Fallback for 7 in WUFI/PHPP.** Decided (Ed, 2026-10-24): 4 (Condensation dryer), with a
  warning. This is the only WUFI XML change in this packet.
- **Q6. What `refED 9` reads for gas.** Resolved (METr panel, 2026-10-24): `refED 9` is
  "CEF - Combined Energy Factor (Gas)". The panel shows Gas consumption [kWh] (`GasCon`),
  Field utilization factor preselection and value, and CEF - Gas (`CEFGas`, 2.67). The electric
  CEF (`CEFef`) is not shown for the gas dryer.
