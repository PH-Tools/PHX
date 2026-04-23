---
title: Packages
card_title: Packages
card_description: "The importers, exporters, and model packages that make up PHX."
---

# Packages

PHX is organized around a central in-memory model with importers that read source
formats into that model and exporters that write it out to target formats.

## model

The PHX model classes and structures. These objects are an intermediate representation
of Passive House building data — geometry, constructions, windows, HVAC, DHW, renewables,
certification settings, and more. Models are not written directly but are created by one
of the importers below.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/model)

## from_HBJSON

Creates a new PHX model from an existing HBJSON file produced by
[Honeybee-PH](https://github.com/PH-Tools/honeybee_ph). This is the primary import
path for most workflows.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/from_HBJSON)

## from_WUFI_XML

Creates a new PHX model from an existing WUFI-Passive XML file, enabling round-trip
editing of WUFI models.

[Source](https://github.com/PH-Tools/PHX/tree/main/PHX/from_WUFI_XML)

## from_PHPP

Creates a new PHX model from an existing PHPP Excel file.

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
