# U-Values: `get_constructor_phpp_id_by_name` can match a material layer and build `None-<name>`

**Status:** To investigate — highest-priority of the three sibling exposures
**Opened:** 2026-08-15
**Owner:** `PHX/PHPP/sheet_io/io_u_values.py` → `get_constructor_phpp_id_by_name`
**Umbrella:** [`component-id-lookup-hardening.md`](component-id-lookup-hardening.md)
**Predecessor:** [`archive/phpp-ventilator-id-lookup/`](../archive/phpp-ventilator-id-lookup/README.md)

## Why this one is different

The ventilator defect needed a name to collide with a *label* row — contrived,
and it never actually reproduced. This one does not need a contrivance, because
**the searched column holds two different kinds of name.**

`get_constructor_phpp_id_by_name` searches `shape.constructor.inputs.display_name.column`
= **`L`**, and reads the ID prefix from `L + phpp_id_num_col_offset(5)` = **`Q`**.

But `U-values!L` is also `sec_1_description` — the **material-layer name column**.
The `U-values` worksheet is not a flat table; it is a repeating ~21-row block per
assembly, and within each block column `L` carries:

- the **assembly** name, at `name_row_offset` into the block — the row whose `Q`
  cell holds `01ud`, `02ud`, …
- every **material layer** name of that assembly, on the rows below — whose `Q`
  cells are **empty**.

Verified against `openph-workspace/sample_files/linde_home/linde_home_260702.xlsx`
(a real exported project):

| Row | `L` | `Q` |
|---|---|---|
| 7 | `Description of building assembly` | `Assembly no.` |
| **8** | **`W-CS (Crawlspace)`** ← assembly | **`01ud`** |
| 12 | `Area section 1` | `l [W/(mK)]` |
| **13** | **`Concrete (Heavily Reinforced) [ 8.0 in]`** ← layer | **`None`** |
| **14** | **`Roxul Comforboard IS [ 3.0 in]`** ← layer | **`None`** |
| **15** | **`Roxul SmartRock [ 2.0 in]`** ← layer | **`None`** |
| 29 | *(assembly 2 name)* | `02ud` |

## The failure

`get_constructor_phpp_id_by_name` scans `L` **from row 1** and takes the first
match. So:

> If an assembly's `display_name` equals the `display_name` of **any material**
> that appears in an earlier block, the scan matches the **material row** first,
> reads an empty `Q` cell, and returns `"None-<assembly name>"`.

Both strings are free text and both are written verbatim by PHX
(`phpp_model/uvalues_constructor.py`): the assembly name via
`f"'{self.phx_construction.display_name}"`, each layer via
`f"'{material.display_name}"`. Nothing decorates, namespaces, or disambiguates
them. An assembly named `Concrete` in a model that also has a material named
`Concrete` is ordinary modelling, not a pathological case.

**This has not been demonstrated live — that is the investigation.** What is
demonstrated is that the two name kinds share one column, that layer rows have
empty ID cells, and that the search is unbounded upward.

## Blast radius — the worst of the three

Call site: `phpp_app.py:445`, inside `write_project_opaque_surfaces`, once per
opaque polygon:

```python
self.u_values.get_constructor_phpp_id_by_name(
    opaque_component.assembly.display_name, _use_cache=True
)
```

The result becomes the **assembly selection on the `Areas` worksheet**. An
unresolvable selection means the surface resolves no U-value — an envelope
element silently drops out of the heat-loss calculation. That is a larger error
than the ventilator case that motivated all of this.

`_use_cache=True` makes it worse: the first bad answer is memoized under that
name and reused for **every** surface with that assembly for the rest of the
export. One collision poisons the whole assembly.

## What to investigate

1. **Reproduce it.** Build a `PhxProject` with an assembly and a material sharing
   a `display_name`, where the material's assembly sorts first. Write to a
   fake/real workbook and inspect the `Areas` assembly selection. Use
   `tests/test_PHPP/test_sheet_io/test_io_components_ventilators.py` as the
   harness template.
2. **Check the real-world frequency.** Grep recent project HBJSONs / PHPPs for
   assembly names that equal a material name. If it is common, this is not a
   latent bug.
3. **Confirm the `Q`-column offset assumption** holds in the 9.x shapes too
   (`phpp_id_num_col_offset` is shape-driven; only 10.6 was inspected here).
4. **Decide the not-found contract.** This method currently returns `None`
   (no raise) when the name is absent — a *third* contract, different again from
   the glazing and frame lookups. See the umbrella doc.

## Suggested fix

Bounding to the entry section — the ventilator remedy — **does not work here**,
because the assembly rows are not a contiguous entry block; they are one row per
21-row stride, interleaved with the layer rows that cause the collision.

Two options worth weighing:

- **Match on the ID column, not the name column.** Walk `Q` for the `NNud`
  markers to get the assembly rows, then compare `L` only on those rows. This
  makes the layer rows structurally unreachable and is the closest analogue to
  "bound the search to the entries".
- **Step by the block stride.** Use `name_row_offset` and the block pitch to
  visit only assembly-name rows.

Either way: never format an empty prefix into an ID — raise
`ResolveComponentIDException` (`PHX/PHPP/sheet_io/io_exceptions.py`), as
`Ventilators._build_ventilator_phpp_id` now does.

## Related

- `docs/dev/exporter-patterns.md` → *Section locators and component-ID lookups*
- Sibling exposures: [`glazing-id-lookup-none-exposure.md`](glazing-id-lookup-none-exposure.md),
  [`frame-id-lookup-none-exposure.md`](frame-id-lookup-none-exposure.md)
