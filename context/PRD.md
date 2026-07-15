---
DATE: 2026-07-15
STATUS: CANONICAL PRD
---

# PHX — Product Requirements

## 1. Goal

Move building-model data into and out of the proprietary Passive House calculators (PHPP Excel, WUFI-Passive XML) — and related targets (PPP, METr JSON) — without the user re-entering anything. PHX is the **converter** in the middle: it ingests a source model (usually a Honeybee-PH HBJSON), builds a normalized in-memory PHX model, and writes the target format.

## 2. Who uses it

- The **honeybee_grasshopper_ph** workflow — the main way practitioners produce the HBJSON PHX consumes and trigger exports.
- Python users driving the CLIs (`PHX/hbjson_to_wufi_xml.py`, `hbjson_to_phpp.py`, …) or the library directly (`pip install PHX`).

## 3. What belongs here

- `from_*` importers that build a PHX model from a source format.
- The `model/` object graph.
- `to_*` exporters that write a PHX model to a target format.
- The PHPP Excel-interop layer (`PHPP/`, `xl/`) and WUFI XML schema handling.

## 4. Non-goals

- **No persistence of the PHX model.** It is a transient middle step — there is intentionally no serialize/deserialize of a PHX model. If you want to store building data, store the source (HBJSON) or the target file.
- **No data authoring.** PHX converts existing model data; it does not add new PH attributes to models — that is `honeybee-ph`.
- **No UI.** Grasshopper components live in `honeybee_grasshopper_ph`.

## 5. Success criteria

- HBJSON → WUFI XML and HBJSON → PHPP produce files that open cleanly in the target applications and match reference/golden outputs.
- Round-trips that are supposed to be lossless (e.g. via `from_WUFI_XML`) preserve the data they claim to.
- The PHPP write path reproduces its recorded golden cell-state (the `test_xl_replay` invariant) unless output legitimately changed.

## 6. Direction

- Active work tracked in `planning/STATUS.md`; the gitignored `plans/` folder holds dated working notes, licensed PHPP fixtures, and perf scratch (referenced by `scripts/perf/`).
