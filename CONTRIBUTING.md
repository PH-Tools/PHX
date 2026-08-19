Contributing
------------
We welcome contributions from anyone, even if you are new to open source we will be happy to help you to get started.

### Code contribution
This project follows PH-Tools contributing guideline. See [contributing to PH-Tools projects](https://github.com/PH-Tools/contributing).

---

## A few things specific to this repository

PHX is the **converter**. It reads an HBJSON (or an existing PHPP / WUFI XML) into a
normalized in-memory model, then writes that model out to a PHPP workbook, WUFI-Passive
XML, or METr JSON. It is the last stop before a real certification file, so mistakes here
show up directly in a project someone is certifying.

**PHX is modern Python 3 — the IronPython 2.7 rule does not apply here.** f-strings,
`dataclasses`, `pathlib`, `openpyxl` are all fine and used throughout. (The one exception is
`PHX/run.py`, a Grasshopper shim that must stay Py2.7-safe, and it is excluded from
formatting.)

**The PHX model is transient.** Data comes in through a `from_*` family and leaves through a
`to_*` family; the model in the middle is a normalized contract, not a storage format.
Please do not add serialization to the model itself.

**Commit messages are load-bearing here.** PHX releases via **semantic-release**, which
parses [Conventional Commits](https://www.conventionalcommits.org/) to compute the next
version. `fix(scope):` / `feat(scope):` / `chore(scope):` — a missing or wrong prefix means a
missing or wrong release. This is stricter than the rest of the organization; if you are
unsure which prefix fits, use `fix(...)` and say so in the PR, and we will adjust it.

For the full house rules see `context/CODING_STANDARDS.md` and `context/ARCHITECTURE.md`.

### Changes here usually have a partner change upstream

PHX can only write what the model gives it. If a value is missing from a PHPP export, the
cause is often that `honeybee_ph` never stored it, or a Grasshopper component never offered
it. Before starting, read
[Changes that span repositories](https://github.com/PH-Tools/contributing#changes-that-span-repositories)
in the main guide.

### Selector / drop-down values write in two places

This catches people, so it is worth spelling out. A PHPP drop-down value needs **both**:

1. **The enum member** in `PHX/model/enums/…` — e.g. `PhiCertIHGType`, where the member's
   *value* is the number PHPP decodes from the cell.
2. **The number-to-string mapping** in every relevant
   `PHX/PHPP/phpp_localization/EN_*.json` — the `options` dict under the input name.

```json
"phi_building_ihg_type": {
  "locator_col": "R",
  "locator_string": "Building use",
  "input_column": "T",
  "input_row_offset": 4,
  "options": {
    "2": "2-Standard",
    "3": "3-PHPP-calculation ('IHG' worksheet)"
  }
}
```

The **string on the right is written verbatim into the cell**, and those cells carry Excel
data validation. If the text does not match PHPP's own drop-down entry exactly — including
capitalization, hyphens, and the quote characters — PHPP will reject it. Copy the string out
of the workbook rather than retyping it, and remember there is a separate JSON per PHPP
version and per unit system (`EN_10_6.json`, `EN_10_6IP.json`, `EN_10_4A.json`, …). Adding a
value to only one of them is the usual way this goes wrong.

### Tests

`python -m pytest tests/` before opening a PR. This repo runs a **100% coverage floor**
(`fail_under = 100`), so new code needs tests with it.

One thing to know: any change to *how* cells are written must still reproduce the golden
cell-state in `tests/test_xl_replay/`. If that test fails, treat it as a real finding first.
Only re-record the fixture (`scripts/perf/record_replay_fixture.py`) when the output is
*supposed* to have changed — never to make the test go green.
