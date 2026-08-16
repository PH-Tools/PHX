# Foundation model shape for PHPP 10.x `Ground` — cross-repo (honeybee-ph primary)

**Status:** Scoped — 2026-08-15. No code changed. Blocks the `Ground` writer
([`../../bug-fix/phpp-writer-input-gaps/05-ground-worksheet-writer.md`](../../bug-fix/phpp-writer-input-gaps/05-ground-worksheet-writer.md))
and OpenPH's foundation work.
**Filed from:** OpenPH `planning/features/ground-degree-hours-alignment/` (Root 1 of the
`native_reference` ground gap), on Ed's call 2026-08-15: *"we want to properly build out
the right objects to properly support the PHPP `Ground` worksheet correctly … PHX currently
matches the WUFI-Passive shape … push those changes upstream to PHX (and honeybee-ph)
before we continue any work on foundations."*

## Read order

1. [`PRD.md`](PRD.md) — the field-by-field gap between the honeybee-ph/PHX
   foundation model and PHPP 10.6 `Ground`, and the required model changes.
2. [`STATUS.md`](STATUS.md) — state, decisions still open, next step.
3. [`../../bug-fix/phpp-writer-input-gaps/05-ground-worksheet-writer.md`](../../bug-fix/phpp-writer-input-gaps/05-ground-worksheet-writer.md)
   — the writer that consumes the finished shape; its cell map is the
   PHPP-side reference and is **not** repeated here.

## One-paragraph summary

`PhxFoundation` and its four subclasses (`model/ground.py`), and their
honeybee-ph twins (`honeybee_ph/foundations.py`), were shaped from
WUFI-Passive's `FoundationInterface`. PHPP 10.x's `Ground` sheet asks for
**seven inputs WUFI does not**: the *"interior wall towards heated"* area/U pair
on three of the four types (`H28/P28`, `H36/P36`, `H44/P44`), the crawl-space
*wind shield factor* (`P43`), and — arguably — an explicit below-grade wall
*area* where WUFI takes a *depth*. Everything else PHPP needs is present or
cleanly derivable. This packet adds the missing fields to honeybee-ph (primary),
`honeybee-ph-schema`, `honeybee_grasshopper_ph`, and PHX, fixes three small
model defects found on the way, and only then lets the `Ground` writer and
OpenPH's foundation objects proceed on a shape that is PHPP-complete.

## Repos and order

| Order | Repo | Change | Doc |
|---|---|---|---|
| 1 | `honeybee_ph` | fields on the four `PhFoundation` subclasses; defaults; `to_dict/from_dict/duplicate/__eq__` | this packet (PRD §4) + `honeybee_ph/planning/STATUS.md` cross-repo row |
| 2 | `honeybee-ph-schema` | pydantic schema fields; regenerate | PRD §4 |
| 3 | `honeybee_grasshopper_ph` / `honeybee_ph_rhino` | `foundations_create.get_component_inputs` gains the inputs | PRD §4 |
| 4 | **PHX** | `model/ground.py` fields; `from_HBJSON/create_foundations.py` (generic copy — verify new attrs flow); `to_WUFI_XML` (no target, skip); `from_WUFI_XML` (defaults) | PRD §5 |
| 5 | PHX | `Ground` writer (`05`) proceeds, mapping the new fields instead of "template default" | `05` |
| 6 | OpenPH | `OpPhFoundation*` classes for all four types read the PHPP-complete shape | OpenPH packet |
