# PHX (Passive House Exchange)

A Python library that converts building energy model data between [Honeybee](https://github.com/ladybug-tools/honeybee-core) (HBJSON) and Passive House formats (WUFI-Passive XML, PHPP Excel, PPP). PHX models are **in-memory only** — never serialized directly. They are an intermediate representation between source and target formats.

- **Repo:** https://github.com/PH-Tools/PHX | **PyPI:** https://pypi.org/project/PHX/
- **License:** GPL-3.0+ | **Python:** 3.10+
- **Ecosystem:** [honeybee-ph](https://github.com/PH-Tools/honeybee_ph), [Ladybug Tools](https://github.com/ladybug-tools)

## Detailed Context (read these when working on specific areas)

- [`context/architecture.md`](context/architecture.md) — Data flow, full package/module map
- [`context/model-hierarchy.md`](context/model-hierarchy.md) — PHX object graph, design patterns, Honeybee→PHX concept mappings
- [`context/exporter-patterns.md`](context/exporter-patterns.md) — How each exporter works, patterns for adding new ones

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r dev-requirements.txt
python -m pytest tests/
```

### Code Style
- **Line length:** 120 | **Formatter:** Black + isort (profile="black") | **Linter:** Ruff (target py310)
- PascalCase is intentional in `xml_schemas.py` / `xml_writables.py` (matches WUFI XML/C# structure)
- `PHX/run.py` is excluded from formatting — it's a Python 2.7 shim for Grasshopper/Rhino

### Commits & CI
- **Conventional commits** (`feat(scope):`, `fix(scope):`) — semantic-release auto-publishes to PyPI
- GitHub Actions runs `pytest` on Python 3.10; deploys on merge to `main`

### Testing
- `python -m pytest tests/` — mirrors source structure (`test_model/`, `test_from_HBJSON/`, `test_to_WUFI_xml/`, etc.)
- `reset_class_counters` fixture resets all `_count` ClassVars for predictable ID numbering
- `to_xml_reference_cases` parametrizes end-to-end (HBJSON input → expected XML output) comparisons
- Reference files in `tests/reference_files/` (organized by source: `from_grasshopper_tests/`, `from_hb_json_tests/`, `from_WUFI/`)

### Key Dependencies
- `honeybee-core`, `honeybee-energy`, `honeybee-ph` — Honeybee model classes + PH extensions
- `pydantic>=2.0` — WUFI XML schema parsing (`from_WUFI_XML/`)
- `PH-units` — Unit conversion | `xlwings` — Excel/PHPP | `lxml` — XML parsing | `rich` — Console output
