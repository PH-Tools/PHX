# FloorAreaUtilizationZone exporter inconsistency

**Status:** Requested — reproduced, not implemented
**Opened:** 2026-08-06
**Owners:** `to_WUFI_XML/xml_schemas.py`, `to_METr_JSON/metr_schemas.py`

## Defect

The WUFI XML and METr JSON exporters emit different areas for the same utilization-zone field:

- WUFI XML `FloorAreaUtilizationZone` uses `PhxSpace.floor_area`.
- METr JSON `flAUZone` uses `PhxSpace.weighted_floor_area`.

The current reference fixtures all use a 100% Space weighting factor, so the values happen to
match. They diverge as soon as a Space has an iCFA/TFA weighting below 100%. WUFI derives its
displayed average occupancy area per person from `NumberOccupants` and
`FloorAreaUtilizationZone`, so this can also change the reported occupant density.

## Decision required

Confirm the target-format definition of utilization-zone floor area and choose one PHX source
for both exporters. Do not resolve this from the existing equal-area fixtures. Check WUFI and
METr behavior with a Space whose weighting factor is materially below 1.0, and confirm whether
the field represents geometric floor area or weighted iCFA/TFA.

## Verification

- Add a fixture with `floor_area != weighted_floor_area`.
- WUFI XML and METr JSON emit the same intended value.
- `NumberOccupants` remains unchanged; only the area denominator moves if the selected contract
  differs from one exporter's current behavior.
- Existing 100%-weighted fixtures remain byte-identical for this field.
