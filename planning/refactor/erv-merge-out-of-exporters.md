# Refactor: build the merged Ventilation Rooms once, read-only, instead of merging Spaces inside two exporters

- **DATE:** 2026-09-13
- **STATUS:** Scoped (plan only; no implementation authorized)
- **AUTHOR:** Ed May / Claude
- **ISSUE:** [#127](https://github.com/PH-Tools/PHX/issues/127) (split from [#107](https://github.com/PH-Tools/PHX/issues/107))
- **Predecessor:** [`bug-fix/space-merge-mutates-source-graph/`](../bug-fix/space-merge-mutates-source-graph/README.md) §5 items 1-3

## Problem

With `merge_spaces_by_erv` on (the setting the Grasshopper component sends), the WUFI and METr
exporters each merge a Zone's Spaces by Ventilation Assignment **while writing the file**:
`xml_schemas._PhxZone.wufi_spaces` and `metr_schemas._metr_spaces` both run
`reduce(operator.add, space_group)` over `PhxZone.ventilated_spaces_grouped_by_erv`. #107 stopped
that from mutating the model, but three things remain wrong:

1. The same transform is written twice, once per exporter.
2. `PhxSpace.__add__` constructs a new `PhxSpace`, so every export allocates Space ID Numbers
   outside any Identity Scope (latent: Space `id_num` is not written to WUFI or METr).
3. The single-Space branch needs a `copy()` plus rename to avoid renaming the caller's Space.

What each exporter actually needs from a merged group is one room row. WUFI's `<Room>` and METr's
room dict read the same nine values and nothing else: name, WUFI type, quantity, weighted floor
area, clear height, supply flow, extract flow, the ventilation Utilization Pattern ID Number, and
the Ventilator ID Number.

## Decisions

| # | Decision | Recommendation |
|---|---|---|
| D1 | Where the merge lives | **A read-only projection shared by both exporters**, not a conversion-time change to the model graph (the framing #127 was filed with). See below |
| D2 | What PHPP sees | **Unchanged: the unmerged Spaces.** `Addl vent` needs one row per Space; PHPP never merged |
| D3 | `PhxSpace.__add__` | **Keep it** (public API, five tests in `tests/test_model/test_spaces/test_spaces.py`), stop calling it from the exporters, and lock the projection's numbers to it with an equivalence test |
| D4 | Name of the row record | **`VentilationRoom`**, the canonical glossary term for "the aspect of a Space that carries supply/extract airflow and resolves to a Ventilator" (`context/UBIQUITOUS_LANGUAGE.md`) |
| D5 | Output | **Byte-identical** WUFI XML and METr JSON, merge on and off. This is a refactor; any output change is a defect |

### D1: why a projection, not a model change

Resolving the merge into the graph at conversion time means the model must hold **both** the
unmerged Spaces (PHPP `Addl vent`, PPP) and the merged ones (WUFI, METr). That is a second Space
list on `PhxZone`, a question of which list each consumer reads, identity allocation for the merged
Spaces, and an idempotency guarantee if conversion ever runs a transform twice. The merge is a fact
about two file formats' room lists, not about the building.

A projection has none of that. `ventilation_rooms(zone)` reads the Zone and returns frozen
`VentilationRoom` records: no `PhxSpace` is constructed, no ID Number allocated, nothing written back,
and calling it twice returns equal lists. Both exporters call the same function, so the merge rule
lives in one place. This is the same shape the `export-time-identity-scope` review recommended for
the cooling split ("Option E: don't construct model objects at all"), and it is a step toward the
Ventilation Room / Utilization Zone split tracked as #105 item 3, without taking that on.

## Design sketch

New module `PHX/model/ventilation_rooms.py` (a derived, read-only view of the model; both target
formats use it, so it does not belong under either exporter):

```python
@dataclass(frozen=True)
class VentilationRoom:
    display_name: str
    wufi_type: int
    quantity: int
    weighted_floor_area: float
    clear_height: float
    flow_supply: float
    flow_extract: float
    ventilation_pattern_id_num: int   # Space.ventilation.schedule.id_num
    ventilator_id_num: int | None     # Space.vent_unit_id_num


def ventilation_rooms(zone: PhxZone) -> list[VentilationRoom]:
    """One row per ventilated Space, or one per Ventilation Assignment when zone.merge_spaces_by_erv."""
```

Rules, each copied from today's exporter code, not re-derived:

- **Merge off:** one record per `zone.ventilated_spaces`, in that order, fields read straight off the Space.
- **Merge on:** iterate `zone.ventilated_spaces_grouped_by_erv` (unchanged). A group of one keeps the
  Space's values and takes `display_name = vent_unit_display_name`. A larger group follows
  `PhxSpace.__add__` exactly: `quantity = 1`, name from the first Space's `vent_unit_display_name`,
  summed `floor_area` / `weighted_floor_area`, area-weighted clear height via
  `area_weighted_clear_height`, flows summed through `PhxLoadVentilation.__add__`, the first Space's
  ventilation schedule, and `spaces_are_not_addable` raising the same `ValueError`. Accumulate as a
  **left fold** in group order so float sums match `reduce(operator.add, ...)` bit for bit (clear
  height needs the running floor area, as the pairwise fold computes it). Sort by
  `vent_unit_display_name`.

Writers:

- WUFI: `XML_Object("Room", room, "index", i, _schema_name="_VentilationRoom")` with a new
  `_VentilationRoom` schema function emitting the same nodes as `_PhxSpace` today, reading the
  record fields (the WUFI converter resolves schema functions by name, so this is the only hook).
- METr: `_PhxZone` builds `room_list` from `ventilation_rooms(_z)` through a `_ventilation_room`
  dict function with the same keys as today's `_PhxSpace`.
- Delete `wufi_spaces`, `_metr_spaces`, and any `reduce` / `operator` / `copy` imports they orphan.
  Remove `_PhxSpace` from either exporter only if nothing else calls it.

## Phases

### Phase 0: characterization golden files (before any code change)

No test pins WUFI XML or METr JSON for a merge-on model: `test_xml_output.py` ends in
`assert True`, and its reference cases run with the merge off.

**Finding (2026-09-13):** whole WUFI XML and METr JSON documents are **not** stable between
processes: heat pump `IdentNr` and `SupportiveDevices` order vary run to run, independent of
`PYTHONHASHSEED` and of `uuid4` (filed as [#133](https://github.com/PH-Tools/PHX/issues/133)). The
room output is stable across four runs. So the golden files hold only the sections this refactor
touches: the WUFI `<RoomsVentilation>` and `<UtilisationPatternsVentilation>` (WUFI's spelling) blocks and the METr
room lists.

Cases, from `tests/reference_files/from_grasshopper_tests/hbjson/` (chosen from a survey of every
HBJSON fixture): `Multi_Room_Complete` merge on and off (one Ventilator serving two Spaces),
`occupancy_scenarios/03_single_dwelling_set_occupancy` merge on and off (one Ventilator serving four
Spaces, exercising the left fold), `Non_Residential_Office` merge on (ventilated Spaces with no
Ventilation Assignment, each its own group). `tests/test_export/test_erv_room_merge_golden.py` asserts
exact text equality after a class-counter reset. Synthetic Honeybee models only, so the files are
public-safe.

**Verify:** the new test passes on unmodified `main`; two generations in separate processes give
identical files.

### Phase 1: `VentilationRoom` and `ventilation_rooms()`

Module plus unit tests: merge off returns one record per ventilated Space; merge on for groups of
one, two and three Spaces returns records whose fields equal the fields of
`reduce(operator.add, group)` exactly (the D3 lock); mixed WUFI types in one group raise; calling
twice returns equal lists and leaves every source Space unchanged (names, flows, `id_num`); no
`PhxSpace` is constructed (patch `allocate_identity` for the Spaces namespace and assert it is not
called).

**Verify:** new tests pass; nothing else touched.

### Phase 2: switch both exporters

Swap the writers per the design sketch and delete the exporter-local merge.

**Verify:** Phase 0 golden tests unchanged; `tests/test_export/test_export_does_not_mutate_the_model.py`
(the #107 tests) still pass; `tests/test_xl_replay/` unchanged (PHPP untouched); full suite green.

### Phase 3: docs and closeout

- `docs/dev/exporter-patterns.md`: WUFI and METr room lists come from `ventilation_rooms()`; exporters
  never construct or merge Spaces. New public module → `docs/nav.yml` plus a `ph-docs` docstring.
- `context/UBIQUITOUS_LANGUAGE.md`: relationship line that a merged **Ventilation Room** is derived per
  **Ventilation Assignment** at export and is not a **Space**; note `__add__` is no longer on the export path.
- `PhxSpace.__add__` docstring: drop the "the merge runs while an exporter is serializing" rationale.
- Retitle #127 and update its body to the D1 approach; `planning/STATUS.md`; archive
  `bug-fix/space-merge-mutates-source-graph/` (its §5 items 1-3 are then done) with an index row.

## Acceptance

- WUFI XML and METr JSON byte-identical to Phase 0 for every golden case
- No exporter calls `PhxSpace.__add__`, `copy()` on a Space, or constructs a `PhxSpace`
- Exporting one project twice, or WUFI then METr then PHPP, leaves every Space's name, flows and
  `id_num` unchanged (existing #107 tests plus the Phase 1 no-allocation test)
- xl-replay golden state unchanged; `python -m pytest tests/` green

## Out of scope

- **#105 item 3**, splitting `PhxSpace` into Ventilation Room and Utilization Zone in the model. This
  projection does not block it and should not grow into it.
- **Merged occupancy density** (a merged `PhxSpace` reports the first Space's density over the summed
  area). Inert in both targets today; the projection carries no occupancy at all.
- **PPP**, which does not merge.
- **Unassigned Spaces with merge on (to verify, not assumed).** `ventilated_spaces_grouped_by_erv` keys
  groups by `vent_unit_id_num` and sorts the keys; a mix of `None` and integer keys cannot be sorted in
  Python 3. An all-unassigned Zone works (`Non_Residential_Office`, merge on, is a Phase 0 golden case);
  a Zone mixing assigned and unassigned ventilated Spaces has not been tried. Check during Phase 1
  whether `assert_ventilation_assignments_ready` makes the mix unreachable. Preserve today's behavior
  either way and file an issue if it is reachable.

## Execution

Claude does Phase 0 (it must be captured on `main` before anything moves) and reviews; codex
(`gpt-5.6-sol`) builds Phases 1-2 in one bounded run against this doc; Claude does Phase 3.
