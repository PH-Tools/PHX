# Components: `get_frame_phpp_id_by_name` can build `None-<name>`

**Status:** To investigate — lowest-risk of the three, and the closest analogue to the fixed ventilator case
**Opened:** 2026-08-15
**Owner:** `PHX/PHPP/sheet_io/io_components.py` → `Frames.get_frame_phpp_id_by_name`
**Umbrella:** [`component-id-lookup-hardening.md`](component-id-lookup-hardening.md)
**Predecessor:** [`archive/phpp-ventilator-id-lookup/`](../archive/phpp-ventilator-id-lookup/README.md)

## The exposure

This is the ventilator defect, verbatim, in the neighbouring section of the same
worksheet:

```python
def get_frame_phpp_id_by_name(
    self, _name: str, _row_start: int = 1, _row_end: int = 500, _use_cache: bool = False
) -> str:
    ...
    row = self.xl.get_row_num_of_value_in_column(
        sheet_name=self.shape.name,
        row_start=_row_start,     # <- defaults to 1, above the entry section
        row_end=_row_end,
        col=str(self.shape.frames.inputs.description.column),
        find=_name,
    )
    if not row:
        raise Exception(...)
    prefix = self.xl.get_data(..., f"{col_offset(description.column, -1)}{row}")
    name_with_id = f"{prefix}-{_name}"    # <- no guard on an empty prefix
```

Search column `IP` (description); prefix read from `IO` (ID), one column left.

Pristine PHPP 10.6 `Components`, frame block — the same layout as the ventilator
block that produced the original report:

| Row | `IO` (ID) | `IP` (Description) | If a name matched here |
|---|---|---|---|
| 6 | `◄ Contents` | `Link to 'Windows' worksheet` | `◄ Contents-<name>` |
| 8 | `Window and door frames` | *(empty)* | — |
| 11 | `ID` | `Description` | `ID-<name>` |
| **12** | *(empty)* | *(empty)* | **`None-<name>`** |
| 13… | `01ud`… | *(user entries)* | correct |

Row 12 is the exact analogue of `Components!LR12`, the cell that produced
`None-REF-HRV` in the original ventilator report.

## Why this is the lowest-risk of the three

- It **raises** when the name is not found, so only the empty-prefix path is
  silent — one failure mode, not two (contrast the glazing lookup, which also
  returns bare `None`).
- It **accepts explicit bounds** already, so a caller can work around it without
  a library change.
- Its entry section is contiguous and locatable: `section_first_entry_row` /
  `section_last_entry_row` both exist and, after the ventilator fix, are both
  correct (`Frames.find_section_last_entry_row` had the same recursion off-by-one
  as `Ventilators` and was fixed in commit `8f156f3`).

So the remedy is mechanical — the same three lines applied to the ventilator
lookup.

## Blast radius

Call site: `phpp_app.py:525`, once per aperture, with `_use_cache=True`:

```python
phpp_id_frame = self.components.frames.get_frame_phpp_id_by_name(
    phx_aperture.window_type.frame_type_display_name, _use_cache=True
)
```

Feeds the frame selection on the `Windows` worksheet. Unresolvable → the frame
U-value and Ψ-install do not resolve for that window. Because the call site
caches, one bad resolution applies to every aperture using that frame type.

## What to investigate

1. **Is row 12 reachable in practice?** For ventilators it was the *reported*
   trigger and never reproduced — nothing in PHX writes the label row. Confirm
   the same for `write_frames` before treating this as live rather than latent.
2. **The `500` reaches into PHI's certified-component library.** The frame block
   is not one list but two (verified in pristine PHPP 10.6 `Components`):

   | Rows | Content | Example |
   |---|---|---|
   | 13–111 | 99 **user-defined** slots, IDs `01ud`…`99ud` | *(what PHX writes)* |
   | 112 | `◄ Content` navigation link | — |
   | 116–720 | PHI **certified-component library** | `1194ws02` = `ENERsign - ENERsign primus` |

   So `row_start=1, row_end=500` spans the label rows *and* ~380 rows of the
   certified library. A name colliding with a library entry resolves to that
   entry's real prefix (`1194ws02-<name>`) rather than the user-defined
   `NNud-<name>` PHX just wrote — a wrong ID, not a `None-` one, and a distinct
   failure worth checking for separately.

   Note this cuts the other way too: bounding to the user block is right for PHX
   precisely because PHX **writes the frame itself immediately before looking it
   up**, so the target is always in rows 13–111. A lookup intended to resolve a
   *certified* component would need the wider range on purpose.

## Suggested fix

1. Default `_row_start` / `_row_end` to `None`, resolved from
   `section_first_entry_row` / `section_last_entry_row`, keeping the explicit
   parameters for backwards compatibility — exactly as
   `get_ventilator_phpp_id_by_name` now does.
2. Route ID construction through the shared builder promoted out of
   `Ventilators._build_ventilator_phpp_id` so an empty prefix raises
   `ResolveComponentIDException`.
3. Keep the existing not-found `raise`; only the message needs the same cleanup
   the ventilator one got (it currently reads `"...named: "X" in" "column IP?"`
   — a missing space from the f-string concatenation).

## Related

- `docs/dev/exporter-patterns.md` → *Section locators and component-ID lookups*
- Sibling exposures: [`glazing-id-lookup-none-exposure.md`](glazing-id-lookup-none-exposure.md),
  [`constructor-id-lookup-none-exposure.md`](constructor-id-lookup-none-exposure.md)
