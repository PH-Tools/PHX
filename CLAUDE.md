# PHX (Passive House Exchange)

A Python library that converts building energy model data between [Honeybee](https://github.com/ladybug-tools/honeybee-core) (HBJSON) and Passive House formats (WUFI-Passive XML, PHPP Excel, PPP, METr JSON). Published on PyPI as `PHX`. Source: https://github.com/PH-Tools/PHX

> **Key idea:** PHX models are **in-memory only** — never serialized directly. A PHX model is the intermediate representation between a *source* format (usually HBJSON) and a *target* format (PHPP/WUFI/…). Everything is `from_*` → `model` → `to_*`.

## What this repo is

| Package | Role |
|---------|------|
| `PHX/model/` | The in-memory PHX object graph (building, components, constructions, hvac, loads, geometry, certification) |
| `PHX/from_HBJSON/` | Build a PHX model from a Honeybee-PH HBJSON file (the primary source path) |
| `PHX/from_WUFI_XML/` | Build a PHX model from a WUFI-Passive XML file (pydantic schema parsing) |
| `PHX/from_PHPP/` | Build a PHX model from a PHPP file |
| `PHX/to_WUFI_XML/` | Write a PHX model to WUFI-Passive XML |
| `PHX/to_PPP/`, `PHX/to_METr_JSON/` | Write PPP / METr-JSON targets |
| `PHX/PHPP/`, `PHX/xl/` | PHPP Excel write path and the Excel-interop layer |

Top-level `PHX/hbjson_to_*.py` are the end-to-end CLI entry points (e.g. `hbjson_to_wufi_xml.py`).

## Where things live — read before working

| Working on… | Read |
|-------------|------|
| Product scope, what belongs here | `context/PRD.md` |
| Orientation + where the deep docs are | `context/ARCHITECTURE.md` |
| **Full** data flow / package map (authoritative) | `docs/dev/architecture.md` |
| PHX object graph, design patterns, HB→PHX mappings | `docs/reference/phx-model-reference.md` |
| Adding/changing an exporter or importer | `docs/dev/exporter-patterns.md` |
| Code rules (style, commits, testing invariants) | `context/CODING_STANDARDS.md` |
| Deps, packaging, CI, release | `context/TECH_STACK.md` |
| Current / in-flight work | `planning/STATUS.md` |
| The public docs site (autodoc spoke — do not restructure) | `docs/.instructions.md` |

Full context index: `context/README.md`. (The rich dev/reference deep-dives live in the public `docs/` spoke, not `context/` — `context/` holds scope, orientation, and rules; `docs/` holds the published reference.)

## Hard rules

1. **The PHX model is transient.** No serialization of the PHX model itself — build it `from_*`, write it `to_*`. Don't add a "save PHX model" path.
2. **Conventional commits drive releases.** `feat(scope):` / `fix(scope):` — semantic-release auto-publishes to PyPI on merge to `main`. Commit messages are load-bearing.
3. **Some code is deliberately non-idiomatic.** PascalCase in `xml_schemas.py` / `xml_writables.py` mirrors the WUFI XML / C# structure — keep it. `PHX/run.py` is a Python-2.7 Grasshopper shim, excluded from formatting.
4. **The PHPP write path has a golden-state invariant.** `tests/test_xl_replay/` record/replays exact cell writes; any change to *how* cells are written must reproduce the recorded golden state (re-record via `scripts/perf/record_replay_fixture.py` only when the output legitimately changes).
5. **Docs are an autodoc spoke.** New/renamed public API → update `docs/nav.yml` + docstrings in the `ph-docs` format (`docs/.instructions.md`). Never restructure `docs/`.
6. **Verify before closeout:** `python -m pytest tests/`.

## Ecosystem

- Upstream source: **honeybee-ph** (produces the HBJSON PHX consumes).
- PHX is used by the **honeybee_grasshopper_ph** workflow and any tool that needs to reach PHPP/WUFI.
