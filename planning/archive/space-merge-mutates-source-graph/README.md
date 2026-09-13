# `PhxSpace.__add__` mutates the source model during serialization

**Issue:** [#107](https://github.com/PH-Tools/PHX/issues/107)

**Status:** **Fixed** on branch `bug-fix/space-merge-mutates-source-graph` (2026-08-25). 10 new tests; 1062 green after merging `main`. The deeper restructure — moving the ERV merge out of serialization and into conversion (§5 item 1) — is **not** done and remains the right follow-up.
**Opened:** 2026-08-25
**Kind:** Long-standing latent defect (not a recent regression)
**Introduced:** `45765b9` (2024-06-05, *"feat(wufi): Add new merge-spaces option"*), first released in **v1.45.0**
**Owner files:** `PHX/model/spaces.py`, `PHX/to_WUFI_XML/xml_schemas.py`, `PHX/to_METr_JSON/metr_schemas.py`
**Found during:** [`export-time-identity-scope`](../export-time-identity-scope/README.md) review (site #2 of that ticket's §10 inventory)

---

## TL;DR

`PhxSpace.__add__` hands the new merged space a **reference** to the first source
space's ventilation program, then writes the summed load through it. The ERV merge
runs at **serialization time**, so exporting a `PhxProject` mutates it. Export the
same project twice and the ventilation flow rates compound.

The first export is correct. Everything after it is not.

```
BEFORE:  101-Room_3 = 53.24 m³/h    102-Room_4 = 53.24 m³/h
AFTER 1: 101-Room_3 = 106.48        102-Room_4 = 53.24      <- XML correct (106.48 = the merged pair)
AFTER 2: 101-Room_3 = 159.72        102-Room_4 = 53.24      <- XML wrong
```

## 1. Reproduction

Stock fixture, stock `main`, no modifications:

```python
p = create_project.convert_hb_model_to_PhxProject(
    hb_model, _group_components=True, _merge_faces=True, _merge_spaces_by_erv=True)

x1 = xml_builder.generate_WUFI_XML_from_object(p)
x2 = xml_builder.generate_WUFI_XML_from_object(p)
```

`tests/reference_files/from_grasshopper_tests/hbjson/Multi_Room_Complete.hbjson`:

```
BEFORE:  [('101-Room_3', 53.24, 53.24), ('102-Room_4', 53.24, 53.24)]
AFTER 1: [('101-Room_3', 106.48, 106.48), ('102-Room_4', 53.24, 53.24)]
AFTER 2: [('101-Room_3', 159.72, 159.72), ('102-Room_4', 53.24, 53.24)]
```

The two XML documents differ — 9 diff lines, all of them the merged room's flows:

```diff
                                 <ClearRoomHeight unit="m">2.75</ClearRoomHeight>
-                                <DesignVolumeFlowRateSupply unit="m³/h">106.48</DesignVolumeFlowRateSupply>
-                                <DesignVolumeFlowRateExhaust unit="m³/h">106.48</DesignVolumeFlowRateExhaust>
+                                <DesignVolumeFlowRateSupply unit="m³/h">159.72</DesignVolumeFlowRateSupply>
+                                <DesignVolumeFlowRateExhaust unit="m³/h">159.72</DesignVolumeFlowRateExhaust>
                             </Room>
```

**Trigger:** `_merge_spaces_by_erv=True` **and** at least one ERV serving ≥2 spaces.
That is the setting the Grasshopper `write_wufi_xml` component sends.

## 2. Root cause

`PHX/model/spaces.py:131-158`:

```python
new_space = PhxSpace(
    ...
    ventilation=self.ventilation,      # <-- SHARED reference, not a copy
    occupancy=self.occupancy,          # <-- shared
    lighting=self.lighting,            # <-- shared
)
new_space.ventilation.load = self.ventilation.load + other.ventilation.load
```

`new_space.ventilation` **is** `self.ventilation`. The last line therefore writes
the summed load back into the first source space's own program object.

`PhxLoadVentilation.__add__` (`loads/ventilation.py:29-35`) is clean — it returns a
new object. The defect is entirely the shared program reference plus the write-back.

### Why it compounds

`reduce(operator.add, space_group)` over `[a, b]`:

1. `a + b` → the new space, **and** `a.ventilation.load = a + b`.
2. Next export re-reduces the *same source list*, which now reads `[a+b, b]`
   → `a + 2b`. Then `a + 3b`. Linear growth, one increment per export.

For a group of 3+ the intermediate results feed the same shared object, so the
first space in each ERV group accumulates the whole group total.

### Why it runs at serialization time

Both exporters do the ERV merge **while writing the file**, not during conversion:

| | |
|---|---|
| `to_WUFI_XML/xml_schemas.py:208` | `new_space = reduce(operator.add, space_group)` inside `_PhxZone` |
| `to_METr_JSON/metr_schemas.py:970` | same, inside `_metr_spaces` |

Both are downstream of `validate_project_export_readiness`, so no gate sees it.

### A second, smaller mutation on the same lines

The single-space branch (`xml_schemas.py:212-214`, `metr_schemas.py:973-975`)
does `new_space.display_name = new_space.vent_unit_display_name` on the **source**
space. Idempotent, so it never compounds, but the exporter is still renaming the
caller's model objects as a side effect of writing a file.

## 3. Impact

| Scenario | Outcome |
|---|---|
| `hbjson_to_wufi_xml.py` CLI (one export, one process) | **Correct.** The one file written is right; the process then exits. |
| Grasshopper `write_wufi_xml` component | **Correct** — `PHX/run.py` shells out to the CLI, so it is always a fresh process. |
| Same `PhxProject` exported to WUFI **twice** | Second file has inflated flows |
| Same `PhxProject` exported to WUFI **then METr** (or the reverse) | Second file has inflated flows |
| Same `PhxProject` exported to WUFI **then PHPP** | **PHPP writes the inflated value.** `phpp_app.py:738` iterates `zone.spaces` directly — the *unmerged source* spaces — and `phpp_model/vent_space.py:101-113` reads `ventilation.load.flow_supply` / `flow_extract` / `flow_transfer` straight off them. |
| POC web service holding a converted project and serving multiple exports | Flows grow with every request |
| Notebook / batch loop re-exporting one project | Same |

So the **shipped Grasshopper and CLI workflows are unaffected** — which is why this
has survived since v1.45.0 (June 2024). It bites exactly the multi-target and
long-lived-process usage the library is moving toward.

The PHPP row is the one that matters most: PHPP `Addl vent` supply/extract airflow
feeds the ventilation heat-loss calculation, and it is a PHI certification input.

## 4. Why nothing catches it

- No validator covers it. `validate_project_export_readiness` is an *identity*
  validator — duplicate and dangling integer references — and the merge happens
  after it runs anyway.
- `tests/test_to_WUFI_xml/test_reference_cases/test_xml_output.py:25` is
  `assert True  # new_xml_txt == ref_xml_text`. A byte comparison against a golden
  file is the natural detector and it is switched off. No other test in the repo
  pins WUFI XML bytes.
- No test exports the same `PhxProject` twice and compares. (`test_project_identity_isolation.py`
  compares two XML documents, but from two *independent* conversions.)

## 5. Proposed fix

Give the merged space its **own** program object, keep the schedule shared:

```python
new_space.ventilation = PhxProgramVentilation(
    display_name=self.ventilation.display_name,
    load=self.ventilation.load + other.ventilation.load,   # already a fresh object
    schedule=self.ventilation.schedule,                    # shared ON PURPOSE - see below
)
```

> ### ⚠️ Do **not** `deepcopy` the ventilation program
>
> `PhxScheduleVentilation` objects are **project-registered utilization patterns**,
> referenced from the exported file by `id_num`
> (`xml_schemas.py:935` `IdentNrUtilizationPatternVent`, `metr_schemas.py:1055`
> `idUPatV`), and validated against
> `project.utilization_patterns_ventilation` (`identity_validation.py:262-268`).
> A deep copy produces an **unregistered** pattern and therefore a dangling
> reference in the output.
>
> That is not hypothetical — it is the exact bug fixed in
> [`wufi-import-space-reconciliation`](../../bug-fix/wufi-import-space-reconciliation/README.md)
> (PR #90), where Spaces held an unregistered Occupancy Pattern and the exporters
> wrote a dangling `IdentNrUtilizationPattern`. Sharing the schedule reference is
> correct; sharing the mutable `load` is the bug.

The docstring already states the intended contract — *"the occupancy, lighting, and
ventilation schedules are NOT merged, however the ventilation loads ARE added
together"* — so this change makes the code match the documented behaviour rather
than changing it.

### Also worth deciding in the same pass

1. **Do the merge during conversion, not during serialization.** The deeper problem
   is that two exporters independently mutate the model while writing it. If
   `merge_spaces_by_erv` resolved into the graph at conversion time, both exporters
   would read a settled model, the transform would be gated by the validator, and
   the identity allocation below would happen inside the conversion scope. Larger
   change; the right one.
2. **`PhxSpace()` inside `__add__` allocates an ID outside any identity scope**
   (site #2 in [`export-time-identity-scope`](../export-time-identity-scope/README.md) §10).
   Space `id_num` is not written to WUFI or METr, so this is latent today — but it
   consumes the legacy counter during serialization. Item 1 fixes it for free.
3. **Fix the single-space `display_name` write-back** (§2) — assign to a copy, or
   set the name on the emitted record rather than the model object.

### Open question — not part of this fix

The merged space carries `floor_area = a + b` but the **first** space's occupancy
and lighting programs by reference. `peak_occupancy` (`spaces.py:115`) is
`people_per_m2 * floor_area`, so a merged space would report the first space's
density over the combined area. Neither exporter's per-room record reads occupancy
or lighting — WUFI's `<Room>` (`xml_schemas.py:931-955`) and METr's room dict
(`metr_schemas.py:1044-1057`) write only name/type/quantity/area/height, the two
flows, the vent schedule ID and the vent unit ID — so this is **inert in both
targets today**. Verify before changing anything; it may be deliberate.

## 6. Verification — done 2026-08-25

Original reproduction, after the fix:

```
flows before any export:   [53.24, 53.24]
flows after WUFI export 1: [53.24, 53.24]
flows after WUFI export 2: [53.24, 53.24]
two exports byte-identical? True
```

The merge itself still does its job — the emitted `<Room>` carries the summed
`106.48` while the source Spaces stay at `53.24`, so the exported file is
unchanged from what a first export always produced. No reference fixture moved.

```
python -m pytest tests/    ->  1062 passed, 3 skipped, 1 deselected  (with main merged in)
python -m black  --check . ->  clean
python -m isort  --check . ->  clean
```

### What shipped

- `PhxSpace.__add__` builds its own `PhxProgramVentilation` with the summed load
  and a **shared** `schedule` (a copy would be an unregistered pattern).
  Neither source Space is touched.
- Both exporters' single-space branch now renames a `copy()` rather than the
  source Space (`xml_schemas.py`, `metr_schemas.py`).

### Tests added

`tests/test_model/test_spaces/test_spaces.py` — sums the load, mutates neither
source, is repeatable, does not share the program object, keeps the registered
schedule object.

`tests/test_export/test_export_does_not_mutate_the_model.py` — WUFI and METr
exports leave the airflows alone, WUFI export is byte-repeatable, METr-then-WUFI
matches WUFI alone, and no source Space gets renamed.

### Original plan (kept for reference)

Red tests first:

1. **Idempotent export.** Convert a fixture with `_merge_spaces_by_erv=True`,
   export to WUFI twice, assert the two documents are byte-identical.
   *Red:* 9 diff lines.
2. **No source mutation.** Snapshot every
   `space.ventilation.load.{flow_supply, flow_extract, flow_transfer}` before
   export; assert unchanged after. *Red:* 53.24 → 106.48.
3. **Cross-target.** Export to WUFI then METr from one project; assert the METr
   room flows equal the WUFI room flows. *Red.*
4. **Merge is still correct.** The merged room's flow equals the sum of its group —
   the behaviour that must not regress. *Green today, must stay green.*
5. **Schedule still resolves.** After the merge, the merged space's
   `ventilation.schedule.id_num` is present in
   `project.utilization_patterns_ventilation` — the guard against fixing this with
   a `deepcopy`.

Then `python -m pytest tests/` (baseline 1032 passed, 3 skipped) and `black --check`.

**Strongly recommended alongside:** re-arm
`test_xml_output.py:25`. It is the only thing in the repo that would have caught
this, and it would catch the next one.

## 7. Related

- [`export-time-identity-scope/`](../export-time-identity-scope/README.md) — the
  sibling ticket; this is site #2 of its §10 inventory of unscoped/ungated
  export-time model construction. Its §8.3 is site #3.
- [`wufi-import-space-reconciliation/`](../../bug-fix/wufi-import-space-reconciliation/README.md)
  — the unregistered-pattern defect that rules out a `deepcopy` fix.
