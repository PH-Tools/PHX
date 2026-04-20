---
title: Architecture
card_title: Developer Guide
card_description: "Architecture decisions, exporter/importer patterns, and the conventions for extending PHX."
card_index: "01"
---

# PHX Architecture

## Data Flow

```
HBJSON file ──> from_HBJSON ──> PHX Model (in-memory) ──> to_WUFI_XML  ──> .xml file
                                     |                ──> PHPP          ──> Excel (via xlwings)
                                     |                ──> to_PPP        ──> .ppp file
                                     |                ──> to_METr_JSON  ──> .json file
WUFI XML file ──> from_WUFI_XML ─────┘
```

PHX is an **in-memory-only translator** — PHX models are never serialized directly. They exist as an intermediate representation created from a source (usually HBJSON) and consumed by an output writer.

## Package Structure

```
PHX/
├── model/                  # Core PHX domain model (dataclasses)
│   ├── project.py          # PhxProject (top-level), PhxVariant, PhxProjectData
│   ├── building.py         # PhxBuilding, PhxZone
│   ├── components.py       # PhxComponentOpaque, PhxComponentAperture, PhxComponentThermalBridge
│   ├── constructions.py    # PhxConstructionOpaque, PhxConstructionWindow, PhxMaterial
│   ├── assembly_pathways.py # PhxHeatFlowPathway, ISO 6946 heat-flow pathway analysis
│   ├── geometry.py         # PhxPolygon, PhxVertix, PhxVector, PhxPlane, PhxGraphics3D
│   ├── spaces.py           # PhxSpace
│   ├── certification.py    # PhxPhiCertification, PhxPhiusCertification
│   ├── elec_equip.py       # Electrical devices (dishwasher, fridge, lighting, etc.)
│   ├── ground.py           # Ground/foundation models
│   ├── phx_site.py         # Site/climate data
│   ├── shades.py           # PhxWindowShade
│   ├── utilization_patterns.py  # Schedule collections for ventilation/occupancy/lighting
│   ├── enums/              # Enum definitions (building, elec_equip, foundations, hvac, etc.)
│   ├── hvac/               # HVAC subsystem models
│   │   ├── _base.py        # PhxMechanicalDevice base class
│   │   ├── collection.py   # PhxMechanicalSystemCollection
│   │   ├── ventilation.py  # Ventilators, exhaust devices
│   │   ├── heating.py      # Heaters (electric, boiler, district)
│   │   ├── heat_pumps.py   # Heat pump variants
│   │   ├── cooling_params.py # Cooling parameter sets
│   │   ├── water.py        # Hot water tanks/devices
│   │   ├── piping.py       # DHW piping (trunk/branch)
│   │   ├── ducting.py      # Duct elements
│   │   ├── renewable_devices.py  # PV panels
│   │   └── supportive_devices.py # Supportive devices
│   ├── schedules/          # Ventilation, occupancy, lighting schedules
│   ├── loads/              # Load definitions (ventilation, occupancy, lighting)
│   └── programs/           # Program types (ventilation, occupancy, lighting)
│
├── from_HBJSON/            # HBJSON -> PHX Model conversion
│   ├── read_HBJSON_file.py # Read and parse HBJSON files
│   ├── create_project.py   # Main entry: convert_hb_model_to_PhxProject()
│   ├── create_variant.py   # Build PhxVariant from HB model
│   ├── create_building.py  # Build PhxBuilding/PhxZone from HB rooms
│   ├── create_rooms.py     # Room-level conversion
│   ├── create_geometry.py  # Geometry conversion (faces -> polygons)
│   ├── create_assemblies.py # Construction/material conversion
│   ├── create_hvac.py      # HVAC system conversion
│   ├── create_schedules.py # Schedule conversion
│   ├── create_elec_equip.py # Electrical equipment conversion
│   ├── create_shades.py    # Shade device conversion
│   ├── create_shw_devices.py # Service hot water device conversion
│   ├── create_foundations.py # Foundation/ground conversion
│   ├── cleanup.py          # Post-conversion cleanup (vertex welding, face merging)
│   ├── cleanup_merge_faces.py # Face merging logic
│   └── _type_utils.py      # Type conversion utilities
│
├── from_WUFI_XML/          # WUFI XML -> PHX Model conversion (Pydantic v2)
│   ├── read_WUFI_XML_file.py   # Read/parse WUFI XML files (lxml XMLPullParser)
│   ├── wufi_file_schema.py     # Pydantic v2 schema for WUFI XML structure
│   ├── wufi_file_types.py      # Pydantic type definitions
│   ├── phx_schemas.py          # PHX model schema definitions
│   └── phx_converter.py        # WUFI XML data -> PHX model conversion
│
├── to_WUFI_XML/            # PHX Model -> WUFI XML export
│   ├── xml_builder.py      # Main entry: generate_WUFI_XML_from_object()
│   ├── xml_schemas.py      # XML element schemas (_ClassName() functions)
│   ├── xml_writables.py    # XML_Node, XML_List, XML_Object classes
│   ├── xml_converter.py    # Schema lookup by class name -> writable conversion
│   ├── xml_txt_to_file.py  # Write XML text to file (UTF-8)
│   └── _bug_fixes.py       # WUFI-Passive workarounds (e.g., 200kW cooling limit)
│
├── to_METr_JSON/           # PHX Model -> METr JSON export
│   ├── metr_builder.py     # Main entry: generate_metr_json_dict()
│   ├── metr_schemas.py     # JSON conversion schemas (PHX -> METr dict)
│   ├── metr_converter.py   # Schema lookup by class name -> dict conversion
│   └── metr_json_to_file.py # Write JSON text to file
│
├── PHPP/                   # PHX Model -> PHPP Excel export (via xlwings)
│   ├── phpp_app.py         # PHPPConnection - main interface to PHPP workbook
│   ├── phpp_model/         # PHPP data models (row objects per worksheet)
│   ├── sheet_io/           # Per-sheet read/write controllers
│   └── phpp_localization/  # PHPP version and language (shape file) support
│
├── to_PPP/                 # PHX Model -> PPP export
│   ├── ppp_builder.py      # Main entry: build_ppp_file()
│   ├── ppp_schemas.py      # PPP section generation functions
│   ├── ppp_sections.py     # PppSection, PppFile data structures
│   └── ppp_txt_to_file.py  # Write PPP text to file (UTF-16LE, no BOM)
│
├── xl/                     # Excel/xlwings utilities
│   ├── xl_app.py           # XLConnection wrapper
│   ├── xl_data.py          # Excel data helpers
│   └── xl_typing.py        # Protocol-based typing for xl abstraction
│
├── hbjson_to_wufi_xml.py   # CLI entry point: HBJSON -> WUFI XML
├── hbjson_to_metr_json.py  # CLI entry point: HBJSON -> METr JSON
├── hbjson_to_phpp.py       # CLI entry point: HBJSON -> PHPP
├── hbjson_to_ppp.py        # CLI entry point: HBJSON -> PPP
└── run.py                  # Python 2.7 compatibility wrapper (for Grasshopper/Rhino)
```
