# phpp-vent-ducting

Write ventilation ducting from the PHX model to the PHPP **"Addl vent"** worksheet
("Data entries for duct sections between the ventilation unit and the thermal envelope").
Today the PHPP export writes the spaces (Rooms section) and ventilators (Units section)
but silently drops all ducting — even though the data is in the PHX model and is already
exported by the WUFI-XML and METr-JSON writers.

## Read order

1. [`PRD.md`](PRD.md) — what/why, PHPP worksheet semantics (verified against a real PHPP 10.6), data mapping.
2. [`PLAN.md`](PLAN.md) — implementation sequence, file-by-file, with the two pre-existing shape-file bugs to fix.
3. [`STATUS.md`](STATUS.md) — current state, open questions.

## Scope in one line

New `VentDuctRow` model class + builder method `write_project_vent_ducting()` in
`phpp_app.py`, wired into the canonical write sequence — plus fixing two column
errors in the (never-before-used) `ducts` block of the localization shape files.

Out of scope: reading ducts *from* PHPP (`from_PHPP`), the "Addl vent 2" overflow
worksheet, exterior-unit installation-room temperature (row 84), and any change to
the WUFI/METr duct exports.
