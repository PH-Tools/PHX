---
DATE: 2026-07-15
STATUS: CANONICAL
---

# PHX — Tech Stack

## Runtime

- **CPython ≥ 3.10** (`requires-python = ">=3.10"`). PHX runs as a normal Python library / CLI, not inside Rhino — with one exception: `PHX/run.py` is a Python-2.7 shim for invocation from Grasshopper/Rhino.

## Dependencies

Runtime (`pyproject.toml [project] dependencies`):

- `honeybee-core`, `honeybee-energy`, `honeybee-ph` — source model classes + PH extensions.
- `pydantic>=2.0` — WUFI XML schema parsing (`from_WUFI_XML/`).
- `PH-units` — unit conversion.
- `xlwings` — Excel/PHPP interop.
- `lxml` — XML parsing/writing.
- `rich` — console output.

Dev extras: `black`, `isort`, `coverage`, `pytest`, `openpyxl`, etc.

## Packaging

- setuptools + wheel; published to PyPI as **`PHX`**.

## Testing

- **pytest** — `python -m pytest tests/`. Tests mirror the source layout (`test_model/`, `test_from_HBJSON/`, `test_to_WUFI_xml/`, …).
- **Fixtures/invariants:**
  - `reset_class_counters` — resets `_count` ClassVars for predictable ID numbering.
  - `to_xml_reference_cases` — parametrized end-to-end HBJSON-in → expected-XML-out comparisons.
  - `tests/test_xl_replay/` — record/replay golden cell-state for the PHPP write path (re-record only via `scripts/perf/record_replay_fixture.py` when output legitimately changes).
  - Reference files in `tests/reference_files/` (by source: `from_grasshopper_tests/`, `from_hb_json_tests/`, `from_WUFI/`).
  - `live_excel`-marked tests drive a real Excel app and are deselected by default (`pytest -m live_excel`).

## Formatting & style

- **Black** + **isort** (`profile="black"`), line length **120**. **Ruff** (target py310). `PHX/run.py` excluded from formatting.

## CI & release

- **Conventional commits** (`feat(scope):`, `fix(scope):`) → **semantic-release** auto-publishes to PyPI on merge to `main`.
- GitHub Actions runs pytest on Python 3.10; `.github/workflows/notify-hub.yml` triggers a ph-docs rebuild on doc changes.

## Docs

- `docs/` is a **spoke** in the ph-docs Astro hub (docs.passivehousetools.com). It also carries hand-authored `dev/` and `reference/` deep-dives that are the authoritative architecture docs. Do not restructure `docs/`; keep `docs/nav.yml` current. See `docs/.instructions.md`.

## Scratch / working area

- `plans/` is **gitignored** — dated working notes plus licensed PHPP fixtures and perf scratch, referenced by `scripts/perf/`. Not part of the package; not the tracked planning surface (that's `planning/`).
