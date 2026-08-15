# PHPP export: ventilator ID could resolve to `None-<name>`, silently zeroing heat recovery

**Status:** **Fixed** — implemented, verified, archived
**Opened:** 2026-08-15
**Closed:** 2026-08-15
**Branch:** `bug-fix/phpp-ventilator-id-lookup-bounds`
**Owners:** `PHX/PHPP/sheet_io/io_components.py`, `io_addnl_vent.py`, `io_areas.py`, `io_elec_non_res.py`
**Originally found by:** OpenPH `native_reference` golden fixture
(`openph-workspace`, `planning/archive/dated/2026-08-15/native-pipeline-reference-case/`)

> **Outcome:** the reported *failure mode* was real and is fixed; the reported
> *trigger* (PHX double-writing the ventilator into the `Components` label row)
> never reproduced and was not the cause. See [Not reproduced](#not-reproduced)
> and [Residual follow-ups](#residual-follow-ups).

---

## Summary

`Components.Ventilators.get_ventilator_phpp_id_by_name` builds the PHPP
ventilator ID by scanning **column `LR` from row 1** for the ventilator's
display-name, then reading the ID prefix from one column left (`LQ`). If the
first match lands anywhere above the entry section — a label row, a header row,
a stray note — the prefix cell is empty and the method returns the string
`"None-<name>"` instead of `"01ud-<name>"`.

Nothing raises. PHPP cannot resolve that name against `Components!LQ13:MF914`,
so `Addl vent` reports `#N/A` for the unit's application range and specific
electric power, and **`Ventilation!L32` (effective heat recovery efficiency)
falls to `0`** — the workbook models a balanced HRV with no heat recovery, and
the resulting heating demand stays entirely plausible.

**The failure mechanism is real and reproducible. The originally-reported
trigger is not.** The first version of this ticket claimed PHX writes the
ventilator into the `Components` units *label* row (12) as well as the first
entry row (13), and that the row-12 write is what the name-scan matches. That
double write does not happen — see [Not reproduced](#not-reproduced). Something
put `REF-HRV` into `LR12` during the OpenPH run, but it was not
`write_project_ventilation_components`.

What is left is still worth fixing: a lookup that silently produces a
structurally invalid ID, plus three confirmed off-by-one defects in the section
locators. Together they turn "the workbook is wrong" into "the workbook is
wrong and no one finds out".

---

## Investigation evidence

How the original report was checked. Seeded the repo's in-memory `FakeXLFramework`
(`tests/test_xl_replay/fake_xl_framework.py`) with the **actual pristine cell
values** read out of `PHPP_EN_V10.6_Empty.xlsx` — the template
`openph-workspace/tools/write_native_reference_phpp.py:73` really uses — then ran
the production `PHPPConnection.write_project_ventilation_components` path
against it.

Pristine `Components` ventilator block (PHPP 10.6 EN):

| Row | LQ | LR | LS | LT | LW | MB |
|---|---|---|---|---|---|---|
| 8 | `Ventilation units` | | | | | |
| 11 | `ID` | `Description` | `Heat recovery efficiency` | `Humidity recovery efficiency hERV` | `Specific electric power` | `Frost protection necessary` |
| 12 | *(empty)* | *(empty)* | `%` | `%` | `Wh/m³` | *(empty)* |
| 13 | `01ud` | *(empty)* | | | | |
| 14…42 | `02ud`…`30ud` | *(empty)* | | | | |

### Confirmed

**C1 — `Ventilators.find_section_header_row` returns an index, not a row.**
`io_components.py:411` uses `enumerate(xl_data)` (0-based) over data that begins
at `_row_start` (default `1`). With the header on `LQ8` it returns **7**.
The same 0-based `enumerate` appears in `Frames.find_section_header_row`
(`io_components.py:233`) and `Spaces.find_section_header_row`
(`io_addnl_vent.py:38`).

Currently **latent**: all three consumers (`find_section_first_entry_row`) pass
`section_header_row` as both the read start *and* the `enumerate` start, so the
shift cancels — `section_first_entry_row` correctly resolves to `13`. The raw
value is otherwise only assigned to `section_start_row`
(`io_addnl_vent.py:77,250,253,383`), which is **never read**. It is a
loaded gun with nothing currently in front of the barrel.

**C2 — the `None-` failure mode is real and silent.** Seeding `LR12 = "REF-HRV"`
and running the real path:

```
id_by_name('REF-HRV') -> 'None-REF-HRV'
```

No exception. `f"{prefix}-{_name}"` formats `None` into the string, so the
lookup "succeeds" and `write_project_ventilators` writes the bad selection to
`Addl vent`.

**C3 — the scan is unbounded upward.** `_row_start: int = 1`
(`io_components.py:456`). Any `LR` cell above the entry section is a candidate
match. `get_ventilator_phpp_id_by_row_num` reads both cells from one row and
does not have this failure mode.

**C4 — `Ventilators.find_section_last_entry_row` has a second off-by-one, on the
recursion path.** `io_components.py:396` enumerates with
`start=self.section_first_entry_row` while reading from `_start_row`. On the
first call those agree; on the recursive call (`_start_row = _row_end`) they
diverge by 500 rows. Latent today — the first 500-row window always finds an
empty cell in a real PHPP — but it becomes live the moment
`section_last_entry_row` is used to bound anything (which the fix below does).

**C5 — no test coverage.** `grep` finds no test touching
`Ventilators.find_section_header_row`, `find_section_first_entry_row`,
`find_section_last_entry_row`, or `get_ventilator_phpp_id_by_name`. Worse, the
golden replay fixture's model (`tests/test_xl_replay/fixtures/Single_Zone.hbjson`)
has **zero ventilation devices**, so the whole ventilator write path sits
outside the `test_xl_replay` invariant. `golden_writes` contains no `Components`
sheet at all.

### Not reproduced

**N1 — PHX does not write the label row.** `section_first_entry_row` resolves
correctly to `13`, and `write_ventilators` writes only entry rows. Cells written
for a single ventilator:

```
LR13='REF-HRV'  LS13=0.75  LT13=0.6  LW13=0.45  MB13='yes'
```

Also tried: two variants with one ventilator each (→ rows 13, 14), and the same
device registered twice in one mech collection (→ rows 13, 14). Never row 12.
Both root-cause candidates in the original ticket are ruled out — a duplicate
yield produces `start`/`start+1` = 13/14, not 12/13, and the locator off-by-one
cancels.

**N2 — the original evidence table is not from the run that found the bug.**
Three independent signals:

- It cites `PHPP_EN_V10.4a_Example.xlsx`; the harness uses
  `PHPP_EN_V10.6_Empty.xlsx`. The claimed "pristine" row 13
  (`Heat recovery unit` / `0.83`) does not exist in the template actually used —
  row 13 is empty there.
- `VentilatorRow.create_xl_items` always emits **five** cells including `MB`
  (frost protection). The reported row-12 write lists four.
- `_repair_ventilator_registration` restores only `LR12/LS12/LT12/LW12`. Had PHX
  written row 12, `MB12` would still read `'yes'` in the output. In
  `sample_files/native_reference/native_reference_260814.xlsx`, `MB12` is empty.

**Open question — deliberately out of scope for this fix.** Something wrote
`LR12`. Once C2/C3 are fixed, that condition raises loudly instead of silently
producing a bad workbook, which is the point: the next occurrence will identify
itself. Do **not** delete
`write_native_reference_phpp.py::_repair_ventilator_registration` on the
strength of this fix alone — re-run the OpenPH reference case with the repair
removed and confirm it stays green first.

---

## Defects fixed

| # | Location | Defect |
|---|---|---|
| **D1** | `io_components.py:411` (`Ventilators`)<br>`io_components.py:233` (`Frames`)<br>`io_addnl_vent.py:38` (`Spaces`) | `enumerate(xl_data)` returns an index; data starts at `_row_start` |
| **D2** | `io_components.py:472-476` | `f"{prefix}-{_name}"` formats `None` rather than failing |
| **D3** | `io_components.py:456` | Name scan starts at row 1, unbounded by the entry section |
| **D4** | `io_components.py:396` | `find_section_last_entry_row` recursion enumerates from the wrong base |
| **D5** | `io_areas.py:102`<br>`io_elec_non_res.py:55` | `enumerate(xl_data, start=1)` — correct only while `_row_start` defaults to `1` |

### Deliberate deviation from the original suggestion list

The original ticket's fix #4 proposed a post-write assertion that every
`Addl vent` unit selection matches `^\d+ud-`. **Dropped.** With D2 and D3 in
place, an unresolvable ID raises at *lookup* time — before anything reaches
`Addl vent` — so the post-write check is redundant, and a hardcoded `\d+ud`
regex bakes an EN-locale PHPP convention into code that is otherwise driven
entirely by the `phpp_localization/*.json` shape files. Structural bounding
(D3) achieves the same guarantee without the locale assumption.

---

## Backwards compatibility

| Change | Risk | Assessment |
|---|---|---|
| `find_section_header_row` return value shifts **+1** for `Ventilators`, `Frames`, `Spaces` | Public method on a documented autodoc module | **Low.** All in-repo consumers are invariant under the shift (they use the value as both read-start and enumerate-start). `section_start_row` is assigned and never read. `grep` across `openph-workspace`, `honeybee_ph`, `CarbonCheck`, `ph-navigator` finds **no external caller** — only a prose comment. |
| `get_ventilator_phpp_id_by_name` default bounds change from `1..500` to the entry section | Signature is public | **None if done as specified.** Keep `_row_start`/`_row_end` as parameters, change their defaults to `None`, resolve to section bounds when omitted. Callers passing explicit values keep today's behaviour exactly. |
| Empty prefix now raises instead of returning `"None-<name>"` | Behavioural change | **Intended, and it is the fix.** Exports that previously "succeeded" against a malformed `Components` sheet will now fail loudly. There is no valid workbook in which the old behaviour was correct. Call it out in the commit body. |
| `find_section_last_entry_row` recursion base corrected | Latent path | **None.** The recursion is unreachable in any real PHPP (a 500-row window always finds the section end). Fixed because D3 makes the method load-bearing. |
| `io_areas` / `io_elec_non_res` hardening | Both call with defaults today | **None.** `start=1` and `start=_row_start` are identical while `_row_start == 1`. |

**Golden-state invariant:** the `tests/test_xl_replay/` fixture model has no
ventilation devices (C5), so none of this touches the recorded cell state.
`test_replay_invariant` must stay green **without re-recording** — if it goes
red, the change reached further than intended. Re-recording requires live Excel
plus a licensed PHPP and is already a blocked item in `planning/STATUS.md`; it
is not an option here and must not be used to "make the test pass".

**Localization:** no `phpp_localization/*.json` shape file changes. All seven
locales share the same `ventilators` locator strings (`Ventilation units` /
`01ud`) and columns (`LQ`/`LR`/`LS`/`LT`/`LW`/`MB`), verified.

**Docs:** `io_components` and `io_addnl_vent` are already in `docs/nav.yml`
(autodoc spoke). No nav changes. Keep docstrings in the `ph-docs` format; if a
new exception class lands in `io_exceptions.py`, that module is already listed
too.

---

## What was done

Six commits on `bug-fix/phpp-ventilator-id-lookup-bounds`, strict red-green TDD —
every phase wrote a failing test first and confirmed it failed for the stated
reason before the fix landed.

| Commit | Defect | Change |
|---|---|---|
| `f85da2a` | D1 | `find_section_header_row` now `enumerate(..., start=_row_start)` in `Ventilators`, `Frames`, `Spaces`. Also resets the three `PhxElevator` counters in the test conftest (see below). |
| `8f156f3` | D4 | `find_section_last_entry_row` recursion now enumerates from `_start_row`, in `Ventilators` **and** `Frames` (`Glazings` was already correct). |
| `961ad6c` | D2 + D3 | `get_ventilator_phpp_id_by_name` defaults its bounds to the entry section; both ID builders share `_build_ventilator_phpp_id`, which raises `ResolveComponentIDException` rather than formatting an empty prefix. |
| `4bfbedf` | D5 | `Areas.Surfaces` and `ElecNonRes.Lighting` header locators honour `_row_start`. |
| `b2c425d` | coverage | End-to-end write-path tests against a fake workbook seeded from the real pristine PHPP 10.6 `Components` **and** `Addl vent` blocks. |
| `d75d30c` | review | Ventilator ID lookups gain the `_use_cache` pattern its sibling lookups already had; test dedupe and a shared `sheet_io` conftest. |

### Deviations from the plan as written

- **D1 and D4 were each wider than filed.** `Frames.find_section_last_entry_row`
  had the same recursion defect as `Ventilators`, and unlike the ventilator copy
  it was already **live** via `first_empty_frame_row_num`. Fixed in the same pass.
- **The post-write `^\d+ud-` assertion was dropped**, as the plan proposed: with
  D2/D3 in place an unresolvable ID raises at lookup time, before anything
  reaches `Addl vent`, and a hardcoded regex would bake an EN-locale convention
  into otherwise shape-file-driven code.
- **A pre-existing test-fixture bug was fixed.** `_reset_phx_class_counters` in
  `tests/conftest.py` omitted the three `PhxElevator` classes. Every
  `PHPPConnection` constructs them via `get_device_type_map()`, so they leak like
  any other counter; the elevator `id_num` tests passed only because
  `test_model/` happens to sort before `test_xl_replay/`. Adding a
  `PHPPConnection`-building test module anywhere would have broken them.
- **A caching gap was closed.** `Ventilators` was the only component-lookup class
  without the `_use_cache` / `self.cache` pattern that `Glazings`, `Frames`,
  `Surfaces` and `Constructors` all have, while `write_project_spaces` resolves a
  ventilator ID **once per room**. On a 200-500 unit multifamily project that is
  hundreds of redundant worksheet reads for a handful of distinct names — and on
  macOS each can degrade to a per-cell interop scan (xlwings #1924 guard,
  `xl_app.py:324-331`). The `Components` section is fully written before that
  pass and does not change during it, so the cache is safe there.

## Verification

- `python -m pytest tests/` → **971 passed, 3 skipped, 1 deselected**
  (baseline before this work: 933 passed, 3 skipped, 1 deselected).
- `tests/test_xl_replay/test_replay_invariant.py` green throughout, **without
  re-recording** the golden fixture.
- The regression tests were confirmed red against the pre-fix code by restoring
  `io_components.py` from `8f156f3`: 5 failed, including
  `test_full_ventilator_round_trip_survives_a_name_in_the_label_row`, which
  wrote `"None-REF-HRV"` into the `Addl vent` unit selection exactly as reported.
- The original reproduction now yields `01ud-REF-HRV`.

### Corpus cross-check

The `phi-rules` PHPP 10 teardowns independently confirm the mechanism and the
fix's semantics:

- `calculators/phpp-components/rules.md` — ventilation units occupy `LQ:MF`,
  `Components!LQ8:MF13`: header row 8, first entry row 13. Matches the workbook.
- `calculators/phpp-addl-vent/rules.md` — `Addl vent!F70` is a data-validation
  selection whose performance lookups read `Components!$LQ$13:$MF$914`
  "by the selected unit prefix". **PHPP itself resolves only against the entry
  rows**, which is why bounding the search there is the correct semantic rather
  than a defensive guard.
- The corpus also records (2026-08-15) that entry-block row positions vary by
  *file*, not by version — the `Addl vent` unit table sits at row 70, 97, and 65
  in three different workbooks, two of them the same PHPP release. This is why
  the locators search for marker strings, and why the locator off-by-ones
  mattered.

## Residual follow-ups

1. **Re-run the OpenPH `native_reference` case with
   `_repair_ventilator_registration` removed** (`openph-workspace/tools/write_native_reference_phpp.py`).
   Nothing in PHX writes `Components!LR12`, and that was never reproduced — so
   the workaround may already be unnecessary. **Do not delete it on the strength
   of this fix alone**; run the case first. If something still writes that row, it
   will now fail loudly and identify itself.
2. **The same silent-`None` exposure remains in three sibling lookups** —
   `get_glazing_phpp_id_by_name`, `get_frame_phpp_id_by_name`, and
   `get_constructor_phpp_id_by_name` all scan from row 1 and build
   `f"{prefix}-{_name}"` unguarded. Deliberately left out of scope here (this
   ticket was ventilator-scoped and each carries its own behaviour-change risk on
   a released package). Filed as
   [`bug-fix/component-id-lookup-hardening.md`](../../bug-fix/component-id-lookup-hardening.md).
3. **Extract the shared marker-scan helper.** Eight `find_section_header_row`-family
   methods across four files re-implement "read a column block, scan for a marker,
   return its row". This bug had to be fixed in five of those copies. A single
   `find_row_of_marker(...)` helper would make the off-by-one unrepresentable.
   Behaviour-preserving refactor; deliberately deferred off a bug-fix branch.
4. **The replay fixture still has no ventilation devices.** Adding one needs live
   Excel plus a licensed PHPP — the same blocker already tracked for the
   aperture-psi-install fixture. The unit-level tests added here cover the path
   meanwhile.

The invariants behind (2) and (3) are written up in
`docs/dev/exporter-patterns.md` → *Section locators and component-ID lookups*.

---

## Scope

Affects the PHPP export path only — WUFI XML and METr JSON do not use this
lookup. Any project whose ventilator name matches somewhere above the entry
section is affected, and the failure is silent, so **previously exported PHPP
files are worth spot-checking**: `Ventilation!L32` reading `0` with a balanced
HRV assigned is the signature, and `Addl vent` showing `#N/A` for the unit's
application range confirms it.

