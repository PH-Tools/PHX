# METr: is `sel=2` ("Detect Automatically") valid for slab U-values?

**Status:** `Blocked` — external. Asked the METr dev team 2026-03-30; no answer as of
2026-08-25.

## The question

`PHX/to_METr_JSON/metr_schemas.py` (`_PhxFoundation`, the `PhxSlabOnGrade` branch) writes
`sel=2` for `slabFlU` / `bmentFlU` when `floor_slab_u_value is None`, mirroring the WUFI XML
exporter's "Detect Automatically" behaviour:

```python
if _f.floor_slab_u_value is None:
    slab_u_sel = 2   # "Detect Automatically"
else:
    slab_u_sel = 6
```

Ed could not find a "Detect Automatically" option in the METr UI for this field, which
suggests METr may not accept `sel=2` here — in which case exported files would carry a
selector METr cannot interpret, silently or otherwise.

## Resolution paths

1. METr team confirms `sel=2` is supported → close, no change.
2. Not supported → either pick the correct selector, or compute the U-value in PHX and write
   it with `sel=6`.

Either way this needs a round-trip check: write a slab-on-grade model with no user U-value,
open it in METr, confirm what the field shows.

## Related

The sibling `lrtb*` array-order question from the same era is **resolved** — METr stores
those arrays in GUI order (Left, Right, Top, Bottom), verified 2026-08-03 with an asymmetric
save; see the comment at `metr_schemas.py:220` and the assertions in
`tests/test_to_METr_JSON/test_metr_schemas.py`.
