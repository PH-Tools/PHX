# STATUS — phpp-vent-ducting

**Status:** Complete
**Last updated:** 2026-08-03

## Current state

Steps 1-7 complete. `VentDuctRow` maps the localized row contract, and
`PHPPConnection.write_project_vent_ducting()` now builds rows using the same global
ventilator order as the Components/Units writers. Assignments are scoped by mechanical
collection, unknown/ambiguous/>10 assignments warn and skip, duct-free models perform no
sheet reads, and overflow truncates to the located duct-section capacity. Both PHPP write
sequences are wired, focused SI/IP and builder tests pass, and the unchanged golden replay
proves the duct-free export adds no Excel interaction. A disposable PHPP 10.6 live run
verified rows 95-96, `ODA`/`EHA` type formulas, nonzero design-flow formulas, and no
`#REF`; it also exposed and closed the header/end-marker locator bugs. Public API
docstrings, field mapping, and exporter sequence documentation are current; the existing
autodoc navigation already includes both API surfaces.

## Next step

None. This packet is archived; public outcomes live in
`docs/reference/phpp-field-mapping.md` and `docs/dev/exporter-patterns.md`.

## Residual checks and limits

1. **PHPP 9 duct columns unverified.** `EN_9_6A`/`EN_9_7IP` shape data assumed identical
   to v10 (D–Z layout). No PHPP 9 workbook was on hand. Ship with the assumption,
   flag in the PR for Ed to spot-check.
2. **Shape-field rename resolved.** Repository grep confirmed the former names were
   unused outside the shape model and JSON files, so the clearer names were adopted.
3. Duct-section row capacity (20 rows in the verified 10.6 workbook) and the 10-unit assignment limit are
   handled by warn+truncate/skip. If a real multifamily model overflows this in practice,
   revisit (PHPP "Addl vent 2" overflow sheet is out of scope for now).
4. **Heat-loss delta fixture limitation.** The only repository HBJSON with ducting targets
   PHPP 9 and has zero operating airflow plus an incomplete PHPP-10 temperature chain.
   The PHPP 10.6 live run therefore verified row/formula behavior but could not demonstrate
   a nonzero conductance/heat-loss delta. Recheck with the next compatible client export;
   do not treat this as a code blocker.

## Blockers

None.

## Final verification

- `.venv/bin/python -m pytest tests/` → `776 passed, 3 skipped, 1 deselected`
- `git diff --check` → pass
- `docs/nav.yml` parsed successfully; existing `phpp_app` and `vent_ducts` API entries present
