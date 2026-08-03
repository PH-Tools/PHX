# STATUS — phpp-vent-ducting

**Status:** In progress
**Last updated:** 2026-08-03

## Current state

Step 1 complete. All seven localization files now map round diameter to E and ventilator
assignment 9 to Y. The three misleading length/type fields are renamed to
`duct_length`, `is_supply_flag`, and `is_exhaust_flag`; the two type flags are raw,
unitless inputs.

## Next step

Implement the `VentDuctRow` model in `PLAN.md` step 2.

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
