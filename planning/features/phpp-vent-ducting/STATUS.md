# STATUS — phpp-vent-ducting

**Status:** In progress
**Last updated:** 2026-08-03

## Current state

Steps 1-2 complete. `VentDuctRow` now maps round or rectangular geometry, weighted
insulation properties, duct length, the supply/exhaust flag, and one validated unit
assignment to localized `XlItem` objects. All seven shapes carry the corrected column
contract; the three IP shapes also use the valid `HR-FT2-F/BTU-IN` conductivity unit.
Focused SI/IP row tests pass, including actual IP conversion.

## Next step

Implement `PHPPConnection.write_project_vent_ducting()` in `PLAN.md` step 3.

## Open questions

1. **PHPP 9 duct columns unverified.** `EN_9_6A`/`EN_9_7IP` shape data assumed identical
   to v10 (D–Z layout). No PHPP 9 workbook was on hand. Ship with the assumption,
   flag in the PR for Ed to spot-check.
2. **Shape-field rename resolved.** Repository grep confirmed the former names were
   unused outside the shape model and JSON files, so the clearer names were adopted.
3. Duct-section row capacity (~15 rows in 10.6) and the 10-unit assignment limit are
   handled by warn+truncate/skip. If a real multifamily model overflows this in practice,
   revisit (PHPP "Addl vent 2" overflow sheet is out of scope for now).

## Blockers

None.
