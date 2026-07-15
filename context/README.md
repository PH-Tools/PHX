# context/ — canonical repo documentation

Stable, ground-truth documentation for PHX: scope, orientation, and the rules for changing it. Distinct from `planning/` (in-flight work) and `docs/` (the public site published by the ph-docs hub).

Note the split for PHX: the **deep reference** (full architecture, model graph, exporter patterns) already lives in the public `docs/` spoke and is authoritative there — `context/` does not duplicate it, it points to it. `context/` holds scope, a short orientation, and the engineering rules.

## Index

| Doc | Read when you need… |
|-----|---------------------|
| [`PRD.md`](PRD.md) | What PHX is for, who uses it, what belongs here and what does not |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Short orientation + pointers to the authoritative deep docs |
| [`TECH_STACK.md`](TECH_STACK.md) | Runtime, deps, packaging, testing, CI, release |
| [`CODING_STANDARDS.md`](CODING_STANDARDS.md) | Style, commit conventions, and the testing invariants |
| [`AUTODOC.md`](AUTODOC.md) | Feature spec for the automated API-doc generator feeding ph-docs |

Authoritative deep docs (in the public spoke):
- `../docs/dev/architecture.md` — full data flow + package/module map
- `../docs/reference/phx-model-reference.md` — PHX object graph, patterns, HB→PHX mappings
- `../docs/dev/exporter-patterns.md` — how each `from_*`/`to_*` works
- `../docs/reference/wufi-xml-schema.md`, `../docs/reference/phpp-field-mapping.md`

## Maintenance rule

When a design decision changes how PHX works, update the relevant doc (here or in `docs/`, wherever that topic is authoritative). Don't let the two drift.
