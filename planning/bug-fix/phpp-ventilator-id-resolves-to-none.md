# PHPP export: ventilator ID can resolve to `None-<name>`, silently zeroing heat recovery

**Status:** Verified (partially) — implementation plan ready, not yet started
**Opened:** 2026-08-15
**Re-verified:** 2026-08-15 (see [Verification](#verification))
**Owners:** `PHX/PHPP/sheet_io/io_components.py`, `PHX/PHPP/sheet_io/io_addnl_vent.py`
**Originally found by:** OpenPH `native_reference` golden fixture
(`openph-workspace`, `planning/archive/dated/2026-08-15/native-pipeline-reference-case/`)

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

## Verification

Method: seeded the repo's in-memory `FakeXLFramework`
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

## Defects to fix

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

## Implementation plan

Strict red-green TDD: **every phase writes a failing test first, confirms it
fails for the stated reason, then makes it pass.** Full suite green at the end
of each phase before starting the next.

Baseline to beat: `python -m pytest tests/` → **933 passed, 3 skipped,
1 deselected**.

### Phase 0 — test scaffolding

No production code. Create `tests/test_PHPP/test_sheet_io/test_io_components_ventilators.py`
following the conventions already in `test_io_addnl_vent_ducts.py`
(shape loaded from `PHX/PHPP/phpp_localization/*.json`, `unittest.mock.Mock()`
for the `xl` connection, one parametrized sweep over all seven locale files).

Add a module-level constant holding the pristine PHPP 10.6 `Components`
ventilator block exactly as tabulated in [Verification](#verification), plus a
helper that builds a `FakeXLFramework` seeded with it for the integration-level
tests in Phases 3 and 5. Seed the full `sheet_names` list and base `seed` from
`tests/test_xl_replay/fixtures/single_zone_replay.json` so `PHPPConnection`
constructs (it needs `Data` and `Areas` to initialise).

**Gate:** `pytest tests/` still 933 passed.

### Phase 1 — D1: header row is a row number

**RED.** Three tests, one per class, asserting the true row:

```python
def test_ventilator_header_row_is_a_row_number_not_an_index():
    shape = _load_components_shape("EN_10_6.json")
    xl = Mock()
    xl.get_single_column_data.return_value = [None] * 7 + ["Ventilation units"]
    assert Ventilators(xl, shape).find_section_header_row() == 8   # currently 7
```

Plus one test proving the bug is not masked by a non-default start:

```python
def test_ventilator_header_row_honours_a_non_default_row_start():
    xl.get_single_column_data.return_value = ["Ventilation units"]
    assert Ventilators(xl, shape).find_section_header_row(_row_start=50) == 50   # currently 0
```

Confirm all four fail with the index value.

**GREEN.** In each of the three methods:

```python
for i, val in enumerate(xl_data, start=_row_start):
```

**Also add a characterization test that must stay green throughout**, pinning
the invariant that actually matters downstream:

```python
def test_first_entry_row_is_13_in_a_pristine_phpp_10_6():
    # holds both before and after the D1 fix - the shift cancels
    assert Ventilators(xl, shape).find_section_first_entry_row() == 13
```

**Gate:** full suite green; `test_replay_invariant` green without re-recording.

### Phase 2 — D4: `find_section_last_entry_row` recursion base

**RED.** Force the recursion by returning a full 501-value window first:

```python
def test_last_entry_row_is_correct_when_the_section_exceeds_one_read_block():
    xl.get_single_column_data.side_effect = (
        ["01ud"] * 501,                 # rows 13..513, no empty -> recurse
        ["01ud"] * 10 + [None] * 491,   # rows 513..1013, empty at 523
    )
    assert Ventilators(xl, shape).find_section_last_entry_row() == 522
```

Confirm it fails (returns `22`, off by the 500-row block).

**GREEN.** `enumerate(xl_data, start=_start_row)` at `io_components.py:396`.
`_start_row` is already resolved to `section_first_entry_row` at the top of the
method, so the first-pass behaviour is unchanged by construction.

**Gate:** full suite green.

### Phase 3 — D2 + D3: make the lookup structurally sound

This is the fix that closes the reported defect. Do D3 first (it is the
structural cure), then D2 (the belt-and-braces raise), in two red-green cycles
within the phase.

**RED (D3).** The exact reported scenario, at integration level against the
seeded `FakeXLFramework`:

```python
def test_ventilator_id_ignores_a_name_in_the_label_row():
    # LR12 is the units label row - above the entry section.
    fake, conn, phpp = _connect(extra_components={"LR12": "REF-HRV", "LR13": "REF-HRV"})
    assert phpp.components.ventilators.get_ventilator_phpp_id_by_name("REF-HRV") == "01ud-REF-HRV"
```

Currently returns `'None-REF-HRV'`.

**GREEN (D3).** Resolve the default bounds from the section, preserving the
existing parameters:

```python
def get_ventilator_phpp_id_by_name(
    self, _name: str, _row_start: int | None = None, _row_end: int | None = None
) -> str:
    """Return the PHPP ID ("01ud-MyVentilator") of a Ventilator component by name.

    The search is bounded to the ventilator entry section so that a matching
    string in a header, label, or note row can never be mistaken for an entry.
    """
    row_start = _row_start or self.section_first_entry_row
    row_end = _row_end or self.section_last_entry_row
    ...
```

Note this newly activates `find_section_last_entry_row` on the live path —
which is exactly why D4 lands first.

**RED (D2).** Prove the residual case still fails loudly rather than silently:

```python
def test_ventilator_id_raises_when_the_id_cell_is_empty():
    # A name inside the entry section whose ID cell was cleared.
    fake, conn, phpp = _connect(extra_components={"LQ13": None, "LR13": "REF-HRV"})
    with pytest.raises(VentilatorIDNotFoundError):
        phpp.components.ventilators.get_ventilator_phpp_id_by_name("REF-HRV")


def test_ventilator_id_never_formats_none_into_the_string():
    # regression guard on the exact reported symptom
    ...
    assert "None-" not in phpp.components.ventilators.get_ventilator_phpp_id_by_name("REF-HRV")
```

**GREEN (D2).** Add `VentilatorIDNotFoundError` to
`PHX/PHPP/sheet_io/io_exceptions.py` (follow the existing constructor style —
message built in `__init__`, `super().__init__(self.msg)`), and raise it when
the prefix cell reads `None` or empty. Keep the existing not-found exception for
the "name is absent entirely" case; the message should name the sheet, the cell
address, and the ventilator, and say that an unresolvable component ID is never
a valid export.

Apply the same treatment to `get_ventilator_phpp_id_by_row_num` — it has the
same `f"{id_num}-{id_name}"` formatting and the same `None` exposure, even
though nothing currently reaches it with an empty cell.

**Gate:** full suite green; `test_replay_invariant` green without re-recording.

### Phase 4 — D5: close the latent `start=1` trap

**RED.** For `io_areas` and `io_elec_non_res`, one test each calling
`find_section_header_row(_row_start=N)` with `N != 1` and asserting the true row.

**GREEN.** `enumerate(xl_data, start=_row_start)`.

**Gate:** full suite green.

### Phase 5 — close the coverage gap that let this through

**RED / regression.** The test that would have caught the original report as
filed — and that pins N1 so nobody re-files it:

```python
def test_ventilator_write_touches_only_entry_rows():
    """Regression: the ventilator must never be written into the label row (12)."""
    fake, conn, phpp = _connect()
    with conn.in_silent_mode():
        phpp.write_project_ventilation_components(_project_with_ventilators(["REF-HRV"]))
    written = fake.written_state()["Components"]
    assert {_row_of(a) for a in written} == {13}
    assert set(written) == {"LR13", "LS13", "LT13", "LW13", "MB13"}
```

Parametrize over one ventilator, two variants × one ventilator, and one
collection with two devices (expected row sets `{13}`, `{13, 14}`, `{13, 14}`).
Add the end-to-end pairing that the OpenPH case exercised:

```python
def test_full_ventilator_round_trip_produces_a_resolvable_phpp_id():
    """write components -> look the name back up -> write the Addl vent selection."""
```

These pass on the fixed code; they are the regression net, not a red step.

**Gate:** full suite green. Expected total: 933 + ~20 new tests, 0 failures.

### Phase 6 — closeout

1. `python -m pytest tests/` — must be green, `test_xl_replay` included and
   **not** re-recorded.
2. Docstrings updated in `ph-docs` format on every touched public method
   (`io_components.py`, `io_addnl_vent.py`, `io_areas.py`,
   `io_elec_non_res.py`, `io_exceptions.py`). No `docs/nav.yml` change needed.
3. Update `planning/STATUS.md`: this row moves to **Fixed**, with the OpenPH
   re-run left as the open follow-up.
4. Conventional commit — the user-visible behaviour change is the loud failure,
   so:

   ```
   fix(phpp): bound the ventilator ID lookup to the entry section

   get_ventilator_phpp_id_by_name scanned column LR from row 1 and read the
   ID prefix one column left, so a name matched above the entry section
   produced "None-<name>". PHPP cannot resolve it, Ventilation!L32 falls to
   0, and the workbook silently models a balanced HRV with no heat recovery.

   Bounds the search to the entry section and raises when the ID cell is
   empty. Also fixes three 0-based enumerate() off-by-ones in the section
   locators (Ventilators/Frames/Spaces header rows, and the
   find_section_last_entry_row recursion base) that returned indices rather
   than row numbers.

   BEHAVIOUR CHANGE: an unresolvable ventilator ID now raises at export time
   instead of writing a bad selection to 'Addl vent'.
   ```

### Follow-ups (not this ticket)

- **Re-run the OpenPH `native_reference` case with
  `_repair_ventilator_registration` removed.** If it stays green, delete the
  workaround and the `LR12` mystery is closed. If it fails, it will now fail
  *loudly* and point at whatever really writes that row.
- **The replay fixture has no ventilation devices.** Adding one requires live
  Excel plus a licensed PHPP (`scripts/perf/record_replay_fixture.py`) —
  the same blocker as the aperture-psi-install fixture already tracked in
  `planning/STATUS.md`. Phase 5's unit-level tests cover the path meanwhile;
  fold this into that existing blocked item rather than opening a new one.
- **`Ventilators.find_first_empty_row` (`io_components.py:438`) is dead code** —
  never called. Noted, not removed (out of scope per the surgical-change rule).

---

## Scope

Affects the PHPP export path only — WUFI XML and METr JSON do not use this
lookup. Any project whose ventilator name matches somewhere above the entry
section is affected, and the failure is silent, so **previously exported PHPP
files are worth spot-checking**: `Ventilation!L32` reading `0` with a balanced
HRV assigned is the signature, and `Addl vent` showing `#N/A` for the unit's
application range confirms it.
