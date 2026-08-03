# STATUS — phpp-vent-ducting

**Status:** In progress
**Last updated:** 2026-08-03

## Current state

Steps 1-3 complete. `VentDuctRow` maps the localized row contract, and
`PHPPConnection.write_project_vent_ducting()` now builds rows using the same global
ventilator order as the Components/Units writers. Assignments are scoped by mechanical
collection, unknown/ambiguous/>10 assignments warn and skip, duct-free models perform no
sheet reads, and overflow truncates to the located duct-section capacity.

## Next step

Wire the builder into both PHPP write sequences in `PLAN.md` step 4.

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
