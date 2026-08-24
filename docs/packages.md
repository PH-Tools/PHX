---
title: Packages
card_title: Packages
card_description: "The importers, exporters, and model packages that make up PHX."
---

# Packages

PHX is organized around a central in-memory model with importers that read source
formats into that model and exporters that write it out to target formats.

## conversion

The public live-object API. `PHX.conversion.from_honeybee()` converts an already
constructed Honeybee `Model` carrying honeybee-ph extensions into a transient
`PhxProject`, without file I/O or serialization.

[Source](https://github.com/PH-Tools/PHX/blob/main/PHX/conversion.py)

## model

The PHX model classes and structures. These objects are an intermediate representation
of Passive House building data — geometry, constructions, windows, HVAC, DHW, renewables,
certification settings, and more. Models are not written directly but are created by one
of the importers below.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/model)

## from_HBJSON

Contains the established Honeybee → PHX conversion implementation plus helpers
for reading HBJSON files produced by
[Honeybee-PH](https://github.com/PH-Tools/honeybee_ph). New live-object callers
should use `PHX.conversion.from_honeybee()`; file-oriented workflows compose the
HBJSON reader with that public facade.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/from_HBJSON)

## from_WUFI_XML

Creates a new PHX model from an existing WUFI-Passive XML file, enabling round-trip
editing of WUFI models.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/from_WUFI_XML)

## from_PHPP

Reads a **closed** PHPP Excel file without Excel (openpyxl, read-only, cached values):
sniffs whether the file is a PHPP and which version/language, reads the headline
results (`Verification` + `PER` + `Cooling load`) into a typed `ResultsRecord` — every
value with its source cell and the caption read beside it — and reports stale-cache
signals (`fresh` / `suspect` / `empty`). Anything it cannot read is named in a
`ReadReport`; unsupported files yield a typed `Refusal`, never an exception. It does
not (yet) build a PHX model.

```python
from PHX.from_PHPP import read_results

r = read_results("path/to/project.xlsx")
if r.ok:
    print(r.record.get("heating_demand"), r.record.values["heating_demand"].source)
    print(r.record.freshness.verdict)
else:
    print(r.refusal)  # Refused (blank_template): PHPP 10.6 EN with TFA 0 ...
```

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/from_PHPP)

## to_WUFI_XML

Exports a PHX model as a WUFI-Passive XML file that can be opened directly
in the WUFI-Passive application.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/to_WUFI_XML)

## to_PHPP

Exports PHX model data to a PHPP Microsoft Excel spreadsheet using localized
field mapping.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/to_PHPP)

## to_PPP

Exports a PHX model as a PPP file.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/to_PPP)

## to_METr_JSON

Exports a PHX model as a METr JSON file for the next-generation WUFI platform.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/to_METr_JSON)

## PHPP

Manages the connection to a live PHPP Excel workbook — localization, sheet I/O,
and the data model for PHPP rows and fields.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/PHPP)

## xl

Low-level Excel utilities (xlwings wrappers) used by the PHPP exporter.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/xl)
