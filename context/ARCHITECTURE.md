---
DATE: 2026-07-15
STATUS: ORIENTATION (deep docs are authoritative — see below)
---

# PHX — Architecture (orientation)

This is a short map. The **authoritative** deep architecture lives in the public docs spoke:

- [`../docs/dev/architecture.md`](../docs/dev/architecture.md) — full data flow + package/module map
- [`../docs/reference/phx-model-reference.md`](../docs/reference/phx-model-reference.md) — the PHX object graph, design patterns, Honeybee→PHX concept mappings
- [`../docs/dev/exporter-patterns.md`](../docs/dev/exporter-patterns.md) — how each importer/exporter is built, and how to add one

## The one-line shape

```
source file ──from_*──►  PHX model (in-memory)  ──to_*──►  target file
 (HBJSON, WUFI XML,        PHX/model/*             (WUFI XML, PHPP xlsx,
  PHPP)                                             PPP, METr JSON)
```

The PHX model is normalized and transient. Importers and exporters are symmetric families; the model in the middle is the contract between them.

## Package families

- **`PHX/model/`** — the object graph: `building.py`, `components.py`, `constructions.py`, `geometry.py`, `spaces.py`, `certification.py`, `elec_equip.py`, plus subpackages `hvac/`, `loads/`, `programs/`, `schedules/`, `enums/`.
- **`from_HBJSON/`** — the primary source path; a family of `create_*.py` modules (building, geometry, hvac, rooms, assemblies, shw, shades, …) that read a Honeybee-PH model and populate the PHX model.
- **`from_WUFI_XML/`** — reads WUFI XML using **pydantic v2** schemas (`phx_schemas.py`, `wufi_file_schema.py`).
- **`to_WUFI_XML/`** — writes WUFI XML via `xml_builder.py` / `xml_converter.py` / `xml_writables.py` (PascalCase mirrors the WUFI/C# schema).
- **`PHPP/` + `xl/`** — the PHPP Excel write path and Excel-interop layer (`xlwings`).
- **`to_PPP/`, `to_METr_JSON/`, `from_PHPP/`** — additional target/source families.

## Entry points

`PHX/hbjson_to_wufi_xml.py`, `hbjson_to_phpp.py`, `hbjson_to_ppp.py`, `hbjson_to_metr_json.py` — end-to-end CLIs wiring a `from_*` to a `to_*`.

## Cross-cutting notes

- **ID numbering:** many model classes carry a `_count` ClassVar; the `reset_class_counters` test fixture resets them for deterministic IDs.
- **Non-idiomatic-on-purpose:** `xml_schemas.py` / `xml_writables.py` PascalCase; `PHX/run.py` Py2.7 shim. See `CODING_STANDARDS.md`.
- **Room grouping:** HB-Rooms are grouped into variants by `room.properties.ph.ph_bldg_segment.identifier` (`create_project.sort_hb_rooms_by_bldg_segment`), then merged to a single HB-Room per segment by `cleanup.merge_rooms()` — so each segment yields one `PhxVariant` / `PhxZone`. The caller's Room subdivision is otherwise invisible to PHX.
- **Dwelling counting:** comes from `PhDwellings` *object identity*, via `honeybee_energy_ph.dwellings.total_dwelling_count()` — a dwelling spanning several Rooms is counted once. Flows to `PhxZone.res_number_dwellings` and `ph_building_data.num_of_units`, then out as WUFI `NumberUnits`, PHPP `num_of_units`, METr `nUnits`, PPP `num_units`. `cleanup.merge_occupancies()` floors the total at `max(total, 1)` so non-residential segments still report one unit.
- **`Room.zone` is NOT consumed by PHX** — deliberately. honeybee-energy reads it as an EnergyPlus thermal-zone instruction; it carries no Passive-House meaning. See honeybee-ph decision [0002](https://github.com/PH-Tools/honeybee_ph/blob/main/context/decisions/0002-dwelling-identity-not-room-zone.md). A `grep -rn "\.zone\b" PHX/` returning anything is a regression.
