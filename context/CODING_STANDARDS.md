---
DATE: 2026-07-15
STATUS: CANONICAL ENGINEERING STANDARD
---

# PHX — Coding Standards

## 1. The PHX model is transient

PHX models are in-memory only. Do not add serialization/persistence to the PHX model itself. Data enters via `from_*` and leaves via `to_*`; the model in the middle is a normalized contract, not a storage format.

## 2. Commit conventions are load-bearing

Use **conventional commits**: `feat(scope):`, `fix(scope):`, `chore(scope):`, etc. **semantic-release** parses them to compute the next version and auto-publish to PyPI on merge to `main`. A wrong or missing prefix means a wrong or missing release.

## 3. Formatting & style

- **Black** + **isort** (`profile="black"`), line length **120**; **Ruff** targeting py310.
- **Intentional exceptions — do not "fix":**
  - PascalCase in `to_WUFI_XML/xml_schemas.py` and `xml_writables.py` mirrors the WUFI XML / C# structure.
  - `PHX/run.py` is a Python-2.7 Grasshopper shim and is excluded from formatting — keep it Py2.7-safe.

## 4. Adding importers/exporters

Follow the established family patterns in `docs/dev/exporter-patterns.md`. A new source is a `from_<format>/` family that populates the `model/`; a new target is a `to_<format>/` family that reads the `model/`. Keep the model as the only thing the two sides share.

## 5. Testing

- **pytest** — `python -m pytest tests/`; tests mirror the source layout.
- Use `reset_class_counters` where deterministic IDs matter.
- **PHPP write path:** any change to *how* cells are written must reproduce the `tests/test_xl_replay/` golden cell-state. Re-record (via `scripts/perf/record_replay_fixture.py`) only when the intended output legitimately changes — never to "make the test pass".
- Add end-to-end reference cases (`to_xml_reference_cases`) for new conversion behavior.

## 6. Docstrings & docs

Docstrings feed the autodoc site — keep them in the `ph-docs` format (`docs/.instructions.md`). New/renamed public API → update `docs/nav.yml`.

## Closeout checklist

- [ ] Conventional-commit message with the right `feat/fix/…` prefix and scope.
- [ ] `python -m pytest tests/` passes (incl. `test_xl_replay` for PHPP-write changes).
- [ ] Black + isort clean; intentional exceptions untouched.
- [ ] No serialization added to the PHX model.
- [ ] `docs/nav.yml` + docstrings updated for any new/renamed public API.
