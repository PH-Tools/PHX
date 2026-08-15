# Components: `get_glazing_phpp_id_by_name` can build `None-<name>`, and cannot be bounded

**Status:** To investigate
**Opened:** 2026-08-15
**Owner:** `PHX/PHPP/sheet_io/io_components.py` → `Glazings.get_glazing_phpp_id_by_name`
**Umbrella:** [`component-id-lookup-hardening.md`](component-id-lookup-hardening.md)
**Predecessor:** [`archive/phpp-ventilator-id-lookup/`](../archive/phpp-ventilator-id-lookup/README.md)

## The exposure

Structurally identical to the ventilator defect that was fixed:

```python
def get_glazing_phpp_id_by_name(self, _name: str, _use_cache: bool = False) -> str | None:
    row = self.xl.get_row_num_of_value_in_column(
        sheet_name=self.shape.name,
        row_start=1,          # <- scans from row 1, above the entry section
        row_end=500,
        col=str(self.shape.glazings.inputs.description.column),
        find=_name,
    )
    if not row:
        return
    prefix = self.xl.get_data(..., f"{col_offset(description.column, -1)}{row}")
    name_with_id = f"{prefix}-{_name}"   # <- no guard on an empty prefix
```

Search column `II` (description); prefix read from `IH` (ID), one column left.

Pristine PHPP 10.6 `Components`, glazing block:

| Row | `IH` (ID) | `II` (Description) | If a name matched here |
|---|---|---|---|
| 6 | `◄ Contents` | `Link to 'Windows' worksheet` | `◄ Contents-<name>` |
| 7 | *(empty)* | *(empty)* | — |
| 8 | `Glazing and door panels` | *(empty)* | — |
| 9 | *(climate note)* | *(empty)* | — |
| 11 | `ID` | `Description` | `ID-<name>` |
| **12** | *(empty)* | *(empty)* | **`None-<name>`** |
| 13… | `01ud`… | *(user entries)* | correct |

The glazing block is not one list but two (pristine PHPP 10.6):

| Rows | Content | Example |
|---|---|---|
| 13–111 | 99 **user-defined** slots, IDs `01ud`…`99ud` | *(what PHX writes)* |
| 112 | `◄ Content` navigation link | — |
| 115–180 | PHI **certified-component library** | `1187gl03` = `EAGON - EAGON SUPER VIG (5/0,25 Vac/:5 Vac.)` |

So the hard-coded `1..500` spans the label rows *and* the whole certified
library. A name colliding with a library entry resolves to that entry's real
prefix (`1187gl03-<name>`) instead of the `NNud-` one PHX just wrote — a wrong
ID rather than a `None-` one, and a distinct failure worth checking separately.

## Two things that make this worse than the ventilator case

1. **It cannot be bounded by the caller.** Unlike `get_frame_phpp_id_by_name`
   and `get_constructor_phpp_id_by_name`, this method exposes **no**
   `_row_start` / `_row_end` parameters — the `1..500` span is hard-coded. Any
   fix has to change the method itself; there is no override escape hatch.
2. **It fails soft in a second way.** It returns `None` when the name is not
   found, rather than raising. So a caller can receive `None` *or*
   `"None-<name>"` — two different silent-ish failures from one method, with
   different meanings.

`Glazings` already has `self.cache` and the call site passes `_use_cache=True`,
so a bad first answer is memoized and reused for every remaining aperture.

## Blast radius

Call site: `phpp_app.py:529`, inside the window-surface write, once per aperture:

```python
phpp_id_glazing = self.components.glazings.get_glazing_phpp_id_by_name(
    phx_aperture.window_type.glazing_type_display_name, _use_cache=True
)
```

The value becomes the glazing selection on the `Windows` worksheet. Unresolvable
→ the window's U-value and g-value do not resolve → window performance is
silently wrong, in the same "no error anywhere visible" way as the ventilator
case.

## What to investigate

1. **Is row 12 (or any blank-ID row above the section) actually reachable?** For
   ventilators this was the *reported* trigger and it never reproduced — nothing
   in PHX writes the label row. Confirm the same for glazings before assuming a
   live bug: the guard is still worth adding, but the priority depends on this.
2. **Does anything write `II` above row 13?** Check `write_glazings` and the
   `Glazings.find_*` locators for the same class of off-by-one that was fixed in
   `Frames`/`Ventilators` (note `Glazings.find_section_last_entry_row` was
   already correct; `find_section_header_row` is hard-coded via
   `shape.glazings.header_start_row`, not searched — see the AppleScript-bug
   comment at the top of the class).
3. **Confirm the `None` return contract has no live callers depending on it.**
   `phpp_app.py:529` passes the result straight into `WindowRow`; check what a
   `None` does there today.

## Suggested fix

Same shape as the ventilator remedy, plus the missing parameters:

1. Add `_row_start` / `_row_end` params defaulting to `None`, resolved from
   `section_first_entry_row` / `section_last_entry_row` (both already exist on
   this class).
2. Route the ID construction through the shared builder promoted out of
   `Ventilators._build_ventilator_phpp_id`, so an empty prefix raises
   `ResolveComponentIDException` instead of formatting `None`.
3. Decide separately whether the not-found case should keep returning `None` or
   start raising — that is a behaviour change for a released package and belongs
   in the umbrella decision, not here.

## Related

- `docs/dev/exporter-patterns.md` → *Section locators and component-ID lookups*
- Sibling exposures: [`frame-id-lookup-none-exposure.md`](frame-id-lookup-none-exposure.md),
  [`constructor-id-lookup-none-exposure.md`](constructor-id-lookup-none-exposure.md)
