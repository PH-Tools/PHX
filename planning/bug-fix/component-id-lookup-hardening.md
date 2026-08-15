# PHPP: the same silent `None-<name>` exposure remains in three component-ID lookups

**Status:** Filed — needs a scope decision before implementing
**Opened:** 2026-08-15
**Owners:** `PHX/PHPP/sheet_io/io_components.py`, `PHX/PHPP/sheet_io/io_u_values.py`, `PHX/PHPP/sheet_io/io_areas.py`
**Predecessor:** [`archive/phpp-ventilator-id-lookup/`](../archive/phpp-ventilator-id-lookup/README.md)

## What

The ventilator fix bounded `get_ventilator_phpp_id_by_name` to its entry section
and made an empty ID cell raise `ResolveComponentIDException` instead of
producing the PHPP-unresolvable string `"None-<name>"`.

**Three sibling lookups still have the identical exposure** — unbounded scan from
row 1, then an unguarded `f"{prefix}-{_name}"`:

| Method | Location | Current bounds |
|---|---|---|
| `Glazings.get_glazing_phpp_id_by_name` | `io_components.py` | `row_start=1, row_end=500` (hard-coded) |
| `Frames.get_frame_phpp_id_by_name` | `io_components.py` | `_row_start=1, _row_end=500` |
| `get_constructor_phpp_id_by_name` | `io_u_values.py` | `_row_start=1, _row_end=1730` |

`Surfaces.get_surface_phpp_id_by_name` (`io_areas.py`) has the same unbounded
scan but happens to fail loudly today because it forces the prefix through
`int()`, which throws on an empty cell. That is an accident of the surface ID
being numeric, not a designed guard — worth making explicit.

**Per-lookup investigation writeups** (each grounded in the pristine and a real
populated workbook):

| Lookup | Writeup | Priority |
|---|---|---|
| `get_constructor_phpp_id_by_name` | [`constructor-id-lookup-none-exposure.md`](constructor-id-lookup-none-exposure.md) | **Highest** — the searched column holds material-layer names too, so the collision needs no contrivance |
| `get_glazing_phpp_id_by_name` | [`glazing-id-lookup-none-exposure.md`](glazing-id-lookup-none-exposure.md) | Medium — hard-coded bounds, no override; two silent failure modes |
| `get_frame_phpp_id_by_name` | [`frame-id-lookup-none-exposure.md`](frame-id-lookup-none-exposure.md) | Lowest — exact analogue of the fixed ventilator case; mechanical remedy |

## A second, distinct failure the same scans expose

Every `Components` component block is **two lists, not one** (verified in
pristine PHPP 10.6):

| Rows | Content |
|---|---|
| 13–111 | 99 **user-defined** slots, IDs `01ud`…`99ud` — what PHX writes |
| 112 | `◄ Content` navigation link |
| ~115–720 | PHI's **certified-component library**, IDs like `1187gl03`, `1194ws02`, `2088vs03` |

PHPP's own lookups deliberately span both (`Components!LQ13:MF914`) — a user may
select either a self-entered component or a certified one. **PHX's lookups
should not**, because PHX writes the component into the user block and then
resolves the name it just wrote. A scan from row 1 to 500 reaches ~380 rows of
certified library, where a name collision resolves to a real-but-wrong prefix
(`1194ws02-<name>`) rather than `None-<name>`.

So the bounding fix addresses two failures at once, and the ventilator fix
already shipped with the correct narrower bound (user block only).

## Why it was not folded into the ventilator fix

Deliberate scope call, not an oversight:

- That ticket was ventilator-scoped, and it was already widened once (to `Frames`
  and `Spaces`) for the locator off-by-one.
- The behaviour change is not free. These three lookups currently *succeed*
  (`get_glazing_phpp_id_by_name` even returns `None` rather than raising when the
  name is absent — a different contract from the ventilator method). Making them
  raise converts silent-wrong into hard-fail on a **released PyPI package**, and
  any workbook that currently exports would start erroring. That is a decision
  worth making on purpose rather than as a side effect of a bug fix.

## Why it is probably still worth doing

The defect class is certification-adjacent and silent end-to-end: PHPP shows
`#N/A` on a sheet nobody opens, the dependent result cell reads a clean `0`, and
the energy demand stays plausible. For the ventilator case that was a 67% error
in annual heating demand, caught only by comparison against an independently
computed reference. Glazing U-values, frame psi-values and construction
assemblies feed the same kind of result.

## Suggested approach

1. Promote `Ventilators._build_ventilator_phpp_id` to a shared component-ID
   builder (module-level helper or a small mixin) — it is already generic; only
   its name and location are ventilator-specific.
2. Default each lookup's `_row_start`/`_row_end` to that class's
   `section_first_entry_row` / `section_last_entry_row`, keeping the explicit
   parameters for backwards compatibility exactly as the ventilator method does.
3. Decide per-method whether "name not found" keeps its current contract
   (`Glazings` returns `None`; the others raise). The **empty-prefix** case
   should raise in all of them; the **not-found** case is a separate question.
4. Clone `tests/test_PHPP/test_sheet_io/test_io_components_ventilators.py` as the
   test template — it already has the fake-workbook + pristine-block pattern.

Red-green TDD, same as the predecessor. `tests/test_xl_replay/` must stay green
without re-recording.

## Open question for the decision

Do we want the hard-fail on all four, or only the bounding (which fixes the
realistic trigger without changing the failure contract)? Bounding alone is
strictly lower risk and removes the whole class of "matched a label row"; the
raise is the belt-and-braces half.

## Related

- `docs/dev/exporter-patterns.md` → *Section locators and component-ID lookups*
  documents the invariant both halves of this rest on.
- The eight-copy `find_section_header_row` duplication noted in the predecessor's
  follow-up 3 touches the same files; consider sequencing them together.
