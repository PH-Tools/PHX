# Status — PHPP writer input gaps

**Status:** Requested — filed 2026-08-15, not started. No PHX code changed.

## Where this came from

Found in the OpenPH workspace while rebuilding the `native_reference` golden
case's PHPP reference workbook. That workbook is produced by handing a
`PhxProject` to `PHX.hbjson_to_phpp.write_phx_project_to_phpp` — the canonical
sequence, deliberately, rather than a bespoke write order — and then
recalculating in Excel. So the gaps below are exactly what a PHX user gets.

Full account, with every measurement and cell trace:
`openph-workspace/planning/archive/dated/2026-08-15/cooling-demand-alignment/STATUS.md`.

Headline from that packet: annual useful cooling read **648.410 kWh against the
workbook's 191.115** (a factor of 3.4). None of it was a calculation error. Gaps
2 and 3 below account for most of it, and gap 1 for a large piece of the
remainder.

## Evidence each gap is real

Every claim in `PRD.md` was measured against a recalculated PHPP 10.6 workbook,
not inferred. The method, if it needs repeating:

1. Build the workbook from `PHPP_EN_V10.6_Empty.xlsx` via the canonical
   sequence, recalculate in Excel, save.
2. Read back with `openpyxl` and compare every `Heating` and `Cooling` row
   against the model.
3. For each disagreeing row, read the PHPP formula (not the value) and walk it
   back to its inputs.

Steps 2 and 3 are what a PHX export has no equivalent of, which is the
underlying point of this packet.

## Interim workaround in place downstream

OpenPH's `tools/write_native_reference_phpp.py` patches all five after PHX's
write sequence returns, sourcing each from the PHX variant. That file is a
reasonable reference implementation for the mapping — in particular the
`SummVent` option semantics and the wind-class lookup — and it audits the
observable consequence of each patch afterwards. It is a fixture tool, not a
product path; the patches should not stay there.

## Open questions

1. **Where does the dwelling count come from on a multi-variant project?**
   `Verification!F29` is a single cell and PHPP is single-building. The other
   four are per-variant too. Worth settling once for the whole packet rather
   than per writer.

2. **Does `Ground` want its own packet?** It is the only one of the five that is
   a whole worksheet with four mutually exclusive type-specific input blocks,
   rather than one or two cells. The other four are small and share a shape.

3. **Is the ventilator label-row clobber still live?**
   `archive/phpp-ventilator-id-lookup/` is complete, and the ID lookup is indeed
   fixed — an export observed on 2026-08-15 resolved `01ud-REF-HRV` correctly on
   its own, where it previously produced `None-REF-HRV`. But that packet's
   subject was the *lookup*. The originally-reported trigger was a stray write
   into the `Components` ventilator-units **label** row (row 12, which holds
   "%", "%", "Wh/m³"), and it is not clear whether that write still happens now
   that the lookup no longer reads row 12. If it does, the workbook carries
   three overwritten unit labels — cosmetic, but it is also the thing that made
   the lookup bug reachable. One export against a blank template and a read of
   `Components!LR12:LW12` settles it.

## Next step

Scope decision from the PHX maintainer: one packet for all five, or split
`Ground` out. Then `PRD.md` acceptance criterion 5 (round-trip against a blank
template, per gap) is the natural first phase — it fails for all five today and
is the regression guard for whatever follows.
