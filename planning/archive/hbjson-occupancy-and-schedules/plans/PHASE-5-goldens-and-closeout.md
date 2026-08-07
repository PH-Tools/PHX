# Phase 5 — Golden re-record, validation, documentation, closeout

**Status:** Complete — targeted goldens, validations, docs, bug filing, and archive finished.
**Depends on:** Phases 0-4 all landed and green.

---

## Step 1 — re-record the reference files

Re-generate the affected files under `tests/reference_files/`.

**Review the diff field by field.** Every changed value must map to a row in the table below or
to a requirement in `../PRD.md`. Anything unexplained is a bug in the change, not in the golden
file — do not accept the diff wholesale.

| field | fixture(s) | expected change | from |
|---|---|---|---|
| ventilation flows | `Multi_Room_Complete` | large increase (0.4 ACH now counted) | Phase 0 |
| `NumberOccupants` / `lPersZ[].nOcc` | `Non_Residential_Office` | `0.0` → nonzero | Phase 2 |
| `NumberOccupants` / `lPersZ[].nOcc` | residential fixtures | **unchanged at `0.0`** | Phase 2 |
| `RelativeAbsenteeism` / `relAbs` | all | `0.0` → annual mean | Phase 3 |
| `BeginUtilization` / `EndUtilization` | all | unchanged at `0` / `24` | Phase 3 |
| `AnnualUtilizationDays` / `aUtil` | all | unchanged at `365` | Phase 3 |
| `LightingFullLoadHours` / `lFLoadH` | all | `8760` → EFLH | Phase 4 |
| `OccupantQuantityUserDef` / `loadsZ.nOcc` | all | **unchanged** | — |
| `NumberBedrooms` / `nBedR` | all | **unchanged** | — |

The last two are the zone-level channel. If they move, something in Phases 2-4 reached into
Channel A and must be reverted.

---

## Step 2 — negative checks

```bash
python -m pytest tests/test_xl_replay/ -v     # MUST be byte-identical to pre-Phase-0
python -m pytest tests/test_to_PPP/ -v
python -m pytest tests/
```

`test_xl_replay` records exact Excel cell writes for the PHPP path. The PHPP and PPP writers
were verified during planning to consume neither Space occupancy nor these schedules
(`grep` over `PHX/PHPP/`, `PHX/to_PPP/`: 0 hits). Any movement means something unexpected is
coupled and the change needs re-scoping.

---

## Step 3 — WUFI-XML round-trip (R14)

`from_WUFI_XML` → PHX → `to_WUFI_XML` on `tests/reference_files/from_WUFI/wufi_xml/_ridgeway.xml`
and `_la_mora.xml`. These are real 206-space and 4-space residential models saved by WUFI itself.

`from_WUFI_XML/phx_schemas.py:1392` already sets `peak_occupancy` on import, so their
`NumberOccupants=0.0` should round-trip unchanged. If it does not, the import and export paths
now disagree about the field.

---

## Step 4 — real-project validation

Re-export `2616 {IA} 39 15th St` and confirm end to end:

```
-FLOOR_01_default_space   peak_occ=  15.04
-FLOOR_02_default_space   peak_occ=  13.91
-FLOOR_03_default_space   peak_occ=  29.25
-FLOOR_04_default_space   peak_occ=  22.23
-FLOOR_05_default_space   peak_occ=   1.88
                          TOTAL      82.31
```

Open the METr JSON in METr and confirm the UI reads the occupant quantities and the utilization
pattern — this is the exact screen that reported `Occupant quantity = 0` and started the packet.

> METr currently errors on some models over a **pre-existing, unrelated foundations issue**. If
> that blocks the check, verify against the WUFI XML instead and note it.

---

## Step 5 — documentation

`docs/reference/phx-model-reference.md`:

- the two occupancy channels (explicit zone-level vs derived per-space) and which exporter field
  each feeds
- the mutual-exclusion invariant
- the gating rule, including *why* it is per dwelling group
- the EFLH convention for lighting full-load hours

`docs/dev/exporter-patterns.md`: the PH-style / HB-style schedule fallback pattern, if it
generalizes beyond these three schedule types.

> **Restate the reasoning, do not just link.** When this packet is archived,
> `phius-correspondance-background/` goes with it. The public docs must carry the *why* for the
> EFLH convention on their own — it is the least obvious decision in the whole change and the
> one most likely to be "corrected" by a future contributor.

No `docs/nav.yml` change expected — no new public API surface.

---

## Step 6 — file the adjacent bugs

Four were found during planning and deliberately not fixed here. Full detail in
`../STATUS.md` → "Adjacent bugs to file".

| # | Bug | Repo | State |
|---|---|---|---|
| 1 | `get_dwelling_obj()` breaks across HBJSON round-trip | `honeybee_ph` | **filed** |
| 2 | `_num_people` list padding repeats the last value | `honeybee_grasshopper_ph` | **filed** |
| 3 | `Infiltration from ACH` 50Pa output unit mismatch | `honeybee_grasshopper_ph_plus` | **written up** |
| 4 | `FloorAreaUtilizationZone`: WUFI writes `floor_area`, METr writes `weighted_floor_area` | PHX | **filed** |

Bug 3 already has a note at
`honeybee_grasshopper_ph_plus/planning/bug-fixes/infiltration-from-ach-units.md`.

Worth flagging in bug 1 and 3's write-ups: they share a root cause with Phase 0 — **a function
returning bare floats whose units live only in a docstring, unpacked into a local whose name
contradicts them.** `NamedTuple` returns with unit-bearing field names would make the class of
bug unwritable. Suggested, not scheduled.

---

## Step 7 — archive the packet

1. Fold the durable outcomes into `context/` (or the `docs/` deep-dives) — plans are
   provisional, `context/` is canonical.
2. Delete `scenario_harness.py` and `scenario_harness_sfh.py`. They were planning prototypes;
   their logic now lives in the layer-1 and layer-3 tests.
3. Decide what to keep: `HBJSON/` and `grasshopper-model/` are the reason the gate is testable
   at all, and `phius-correspondance-background/` is the sole record of the EFLH protocol.
   Consider promoting all three somewhere durable rather than archiving them out of sight.
4. Move the folder to `planning/archive/hbjson-occupancy-and-schedules/`.
5. Add a row to `planning/archive/README.md`.
6. Update `planning/STATUS.md` — move the item from Active to Completed.

---

## Definition of done

- [x] Reference files re-recorded; every changed field explained by the Step 1 table
- [x] Zone-level channel fields unchanged in every fixture
- [x] `tests/test_xl_replay/` byte-identical; `test_to_PPP` green
- [x] Round-trip stable on `_ridgeway` / `_la_mora`
- [x] Real project exports 82.31 occupants and reads correctly in METr (or WUFI, if METr is
      blocked by the foundations issue)
- [x] `python -m pytest tests/` fully green
- [x] Public docs carry the occupancy channels, the gating rule, and the EFLH reasoning
- [x] Four adjacent bugs filed
- [x] Harness scripts deleted; packet archived; both indexes updated

## Commit

```
test(reference): re-record WUFI-XML and METr-JSON goldens for Space loads and utilization patterns
```
