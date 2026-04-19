# PHX Exporter & Importer Patterns

Guide for understanding existing exporters/importers and adding new ones.

## Common Pipeline

All exporters share the same first two steps — read an HBJSON file into a Honeybee model, then convert it to a PHX project:

```python
from PHX.from_HBJSON import read_HBJSON_file, create_project

# 1. Read HBJSON -> Honeybee Model
hb_json_dict = read_HBJSON_file.read_hb_json_from_file(source_path)
hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)
# Note: convert_hbjson_dict_to_hb_model always normalizes the model to Meters.

# 2. Convert HB Model -> PHX Project
phx_project = create_project.convert_hb_model_to_PhxProject(
    hb_model,
    _group_components=True,        # Group components by assembly type
    _merge_faces=False,            # True | False | float (custom tolerance)
    _merge_spaces_by_erv=False,    # Merge spaces served by the same ERV
    _merge_exhaust_vent_devices=False,
)
```

**`_merge_faces`** accepts `bool | float` — when a float is passed, it is used as the merge tolerance instead of `_hb_model.tolerance`.

Each CLI entry point wires up these parameters differently:

| Entry point | `_group_components` | `_merge_faces` | `_merge_spaces_by_erv` | `_merge_exhaust_vent_devices` |
|---|---|---|---|---|
| `hbjson_to_wufi_xml.py` | CLI arg | CLI arg | CLI arg | CLI arg |
| `hbjson_to_metr_json.py` | CLI arg | CLI arg | CLI arg | CLI arg |
| `hbjson_to_phpp.py` | `True` (hardcoded) | `False` (default) | `False` (default) | `False` (default) |
| `hbjson_to_ppp.py` | `False` (hardcoded) | `False` (hardcoded) | `True` (hardcoded) | `False` (hardcoded) |

Then each exporter serializes the `PhxProject` to its target format.

---

## WUFI XML Exporter (`to_WUFI_XML/`)

**Pattern:** Schema-based recursive conversion to XML DOM

### Modules

| Module | Role |
|---|---|
| `xml_schemas.py` | Schema functions — one per PHX class — that return `list[xml_writable]` describing the XML structure |
| `xml_writables.py` | Three writable types (`XML_Node`, `XML_List`, `XML_Object`) plus a `xml_writable` type alias |
| `xml_converter.py` | Discovers schema functions by PHX class name via `getattr` on `xml_schemas` |
| `xml_builder.py` | Recursively walks the writable tree, builds an XML DOM, returns `toprettyxml()` |
| `xml_txt_to_file.py` | Writes UTF-8 XML with an optional timestamped copy |
| `_bug_fixes.py` | WUFI-Passive workarounds applied before XML generation |

### How it works

1. **Schema functions** in `xml_schemas.py` are named with a leading underscore (`_PhxProject`, `_PhxVariant`, etc.). Top-level schemas match the PHX class name; helper schemas use WUFI-centric names (e.g., `_Systems`, `_DistributionDHW`, `_PH_ClimateLocation`). Each returns a `list[xml_writable]`.

2. **Writable types** (`xml_writables.py`):
    - `XML_Node` — leaf element with a text/numeric value and an optional attribute
    - `XML_List` — container whose `count` attribute is auto-computed from `len(node_items)` (overridable)
    - `XML_Object` — references a PHX object; optionally accepts `_schema_name` to override the default class-name lookup

3. **Schema lookup** (`xml_converter.py`): `get_PHX_object_conversion_schema()` constructs `f"_{_phx_object.__class__.__name__}"` by default, or uses an explicit `_schema_name` from `XML_Object`. Looks up via `getattr(xml_schemas, name)`. Raises `NoXMLSchemaFoundError` if not found.

4. **Builder** (`xml_builder.py`): `generate_WUFI_XML_from_object()` recursively walks the writable tree using duck-typing (`hasattr` checks for `node_object`, `node_items`), builds a `minidom` XML DOM, and returns `doc.toprettyxml()`.

    ```python
    def generate_WUFI_XML_from_object(
        _phx_object: Any,
        _header: str = "WUFIplusProject",
        _schema_name: str | None = None,
    ) -> str:
    ```

5. **File writer** (`xml_txt_to_file.py`): `write_XML_text_file(_file_address, _xml_text, _write_copy=True)` writes UTF-8 XML. When `_write_copy=True` (default), also writes a timestamped copy (`{stem}_{M}_{D}_{h}_{m}_{s}{ext}`). On `PermissionError` (e.g., file locked by WUFI), writes only the timestamped copy.

6. **Bug fixes** (`_bug_fixes.py`): `split_cooling_into_multiple_systems()` works around a WUFI-Passive v3.x limitation where a single cooling device cannot exceed 200 kW. If total heat-pump cooling capacity exceeds 200 kW, it splits across multiple mechanical system collections. This runs in the WUFI XML CLI entry point *after* the common pipeline and *before* XML generation.

### Usage

```python
from PHX.to_WUFI_XML import xml_builder, xml_txt_to_file

xml_txt = xml_builder.generate_WUFI_XML_from_object(phx_project)
xml_txt_to_file.write_XML_text_file(target_path, xml_txt)
```

---

## METr JSON Exporter (`to_METr_JSON/`)

**Pattern:** Schema-based class-name dispatch to plain dicts, serialized as JSON

### Modules

| Module | Role |
|---|---|
| `metr_schemas.py` | Schema functions — one per PHX class — that accept a PHX object and return a `dict` |
| `metr_converter.py` | Discovers schema functions by PHX class name via `getattr` on `metr_schemas` |
| `metr_builder.py` | Walks the PHX object graph using the converter, builds a nested dict |
| `metr_json_to_file.py` | Writes UTF-8 JSON |

### How it works

Follows the same class-name dispatch pattern as the WUFI XML exporter, but simpler:

1. **Schema functions** (`metr_schemas.py`) are plain functions named `_ClassName` that accept a PHX object and return a `dict`. No intermediate writable types.

2. **Schema lookup** (`metr_converter.py`): `get_schema_function()` constructs `f"_{_phx_object.__class__.__name__}"` by default, or uses an explicit `_schema_name`. Raises `NoMETrSchemaFoundError` if not found.

3. **Builder** (`metr_builder.py`) provides two entry points:
    - `generate_metr_json_dict(_phx_object, _schema_name=None) -> dict`
    - `generate_metr_json_text(_phx_object, _schema_name=None) -> str` — wraps the above with `json.dumps(indent=2, ensure_ascii=False)`

4. **File writer** (`metr_json_to_file.py`): `write_metr_json_file(_file_path, _json_text)` writes UTF-8 text.

### Usage

```python
from PHX.to_METr_JSON import metr_builder, metr_json_to_file

metr_dict = metr_builder.generate_metr_json_dict(phx_project)
metr_text = metr_builder.generate_metr_json_text(phx_project)
metr_json_to_file.write_metr_json_file(target_path, metr_text)
```

---

## PHPP Exporter (`PHPP/`)

**Pattern:** Sheet-by-sheet Excel writing via xlwings

### Modules

| Module/Package | Role |
|---|---|
| `phpp_app.py` | `PHPPConnection` — main interface to a PHPP workbook; orchestrates all write operations |
| `sheet_io/` | 24 per-sheet read/write controllers (`io_areas.py`, `io_climate.py`, `io_windows.py`, etc.) plus `io_exceptions.py` |
| `phpp_model/` | Data classes representing PHPP rows; generate `XlItem` objects for writing |
| `phpp_localization/` | PHPP version and language detection; shape-file JSON for cell-address mapping |

### How it works

1. **`PHPPConnection`** (`phpp_app.py`) wraps an `XLConnection` (from `PHX/xl/xl_app.py`). On init, it auto-detects the PHPP version and language from the Data worksheet, loads the matching shape file, and instantiates all sheet controller objects as attributes.

2. **Sheet controllers** (`sheet_io/`) handle per-worksheet read/write. 24 controllers cover: Areas, Climate, Components, Verification, U-Values, Windows, Shading, Ventilation, AddnlVent, DHW+Distribution, Electricity, Variants, Overview, PER, SolarDHW, SolarPV, CoolingDemand, CoolingPeakLoad, CoolingUnits, HeatingDemand, HeatingPeakLoad, IHG-NonRes, Use-NonRes, Elec-NonRes.

3. **PHPP data models** (`phpp_model/`) are dataclasses that generate `XlItem` objects. `XlItem` (defined in `PHX/xl/xl_data.py`) carries a sheet name, cell address, write value, optional SI/IP unit conversion, and optional cell/font color.

4. **Localization** (`phpp_localization/`) provides shape-file JSON that maps logical field names to cell addresses for a given PHPP version. Currently ships with **English-only** shape files for PHPP v9 (9.6A, 9.7IP) and v10 (10.3, 10.4A, 10.4IP, 10.6, 10.6IP). The version detection code recognizes German (DE) and Spanish (ES) worksheet names for navigation, but no DE/ES shape files are provided.

5. **`PHPPConnection` exposes 20 `write_*` methods** — 17 functional write operations plus 3 non-residential stubs (`write_non_res_utilization_profiles`, `write_non_res_space_lighting`, `write_non_res_IHG`).

### Usage

```python
from PHX.xl import xl_app
from PHX.PHPP import phpp_app

xl = xl_app.XLConnection(xl_framework=xw, output=print)
phpp_conn = phpp_app.PHPPConnection(xl)
with phpp_conn.xl.in_silent_mode():
    phpp_conn.write_certification_config(phx_project)
    phpp_conn.write_climate_data(phx_project)
    phpp_conn.write_project_constructions(phx_project)
    # ... 14 more write operations
```

`in_silent_mode()` is a context manager on `XLConnection` that disables screen updating, display alerts, and sets calculation to manual on enter; restores all three and triggers recalculation on exit.

---

## PPP Exporter (`to_PPP/`)

**Pattern:** Section-based text serialization

### Modules

| Module | Role |
|---|---|
| `ppp_sections.py` | `PppSection` and `PppFile` dataclasses |
| `ppp_schemas.py` | Schema functions that return `list[PppSection]` for each domain area |
| `ppp_builder.py` | Orchestrates section generation with cross-reference maps |
| `ppp_txt_to_file.py` | Writes UTF-16LE text (no BOM) |

### How it works

1. **Data structures** (`ppp_sections.py`):
    - `PppSection` — `name: str`, `rows: int`, `cols: int`, `values: list[str]`; has `to_lines()` method
    - `PppFile` — `sections: list[PppSection]`; has `to_lines()` method that injects `END_MARKER` after designated sections

2. **Schema functions** (`ppp_schemas.py`) return `list[PppSection]` and cover: meta, EBF, surfaces, thermal bridges, windows, shading, ventilation, U-values, user components, and overbuilt sections. The module also defines slot-limit constants (`MAX_SURFACES=100`, `MAX_WINDOWS=152`, etc.) and cross-reference map type aliases (`AssemblyMap`, `GlazingMap`, `FrameMap`, `SurfaceIndexMap`).

3. **Builder** (`ppp_builder.py`): `build_ppp_file(project: PhxProject) -> PppFile` builds four cross-reference maps (assembly, glazing, frame, surface-index) mapping identifiers to PPP slot indices, then calls each schema function in sequence to produce the `PppFile`.

4. **File writer** (`ppp_txt_to_file.py`): `write_ppp_file(_filepath, _ppp_file)` writes UTF-16LE encoded text with no BOM.

### Usage

```python
from PHX.to_PPP import ppp_builder, ppp_txt_to_file

ppp_file = ppp_builder.build_ppp_file(phx_project)
ppp_txt_to_file.write_ppp_file(target_path, ppp_file)
```

---

## WUFI XML Importer (`from_WUFI_XML/`)

**Pattern:** lxml parsing -> Pydantic v2 validation -> PHX builder functions

### Modules

| Module | Role |
|---|---|
| `read_WUFI_XML_file.py` | Parses WUFI XML into a nested Python dict of `Tag` objects via lxml `XMLPullParser` |
| `wufi_file_types.py` | Pydantic v2 custom types with built-in SI unit conversion (e.g., `Watts`, `M`, `DegreeC`) |
| `wufi_file_schema.py` | Pydantic v2 `BaseModel` classes mirroring the WUFI XML structure |
| `phx_schemas.py` | Builder functions that convert Pydantic WUFI objects into PHX model objects |
| `phx_converter.py` | Single-function entry point: `convert_WUFI_XML_to_PHX_project()` |

### How it works

1. **XML parsing** (`read_WUFI_XML_file.py`): `get_WUFI_XML_file_as_dict()` reads the XML file in 1024-byte chunks via `lxml.etree.XMLPullParser(recover=True, encoding="utf-8")`, then recursively converts the element tree into a nested dict using `xml_to_dict()`. Leaf values become `Tag(text, tag, attrib)` dataclass instances. List-like nodes (detected by a `count` XML attribute or specific tag names) become Python lists.

2. **Unit types** (`wufi_file_types.py`): Custom types (subclassing `float` or `int`) that implement `__get_pydantic_core_schema__` for Pydantic v2. Two base classes:
    - `BaseConverter` — for values with a `unit` attribute; converts to SI via `ph_units.convert()`
    - `BaseCaster` — for values needing type-cast only; handles `None`/`"NONE"` strings

    Concrete types cover power (`Watts`, `KiloWatt`), energy (`kWh`, `kWh_per_M2`), length (`M`, `MM`), temperature (`DegreeC`, `DegreeDeltaK`), airflow (`M3_per_Hour`, `ACH`), and many more.

3. **Pydantic schema** (`wufi_file_schema.py`): `WufiBaseModel` applies a `@model_validator(mode="before")` that calls `unpack_xml_tag()` on every field — converting `Tag` objects into either bare strings or `{"value": ..., "unit_type": ...}` dicts that the unit types understand. The root model is `WUFIplusProject`. Key sub-models include `WufiVariant`, `WufiBuilding`, `WufiZone`, `WufiComponent`, `WufiAssembly`, `WufiWindowType`, `WufiSystem`, `WufiDevice`, `WufiFoundationInterface`, and many more.

4. **PHX builders** (`phx_schemas.py`): Functions named `_PhxClassName` (or `_WufiClassName` for WUFI-specific types) that consume Pydantic objects and produce PHX model objects. A central dispatcher `as_phx_obj(_model, _schema_name, **kwargs)` looks up builders via `getattr` on the module. Type libraries (windows, assemblies, shades, schedules) are built first, then each variant's building, certification, and HVAC systems.

5. **Entry point** (`phx_converter.py`): `convert_WUFI_XML_to_PHX_project(_wufi_xml_project: WUFIplusProject) -> PhxProject` — a thin wrapper that calls `_PhxProject()` from `phx_schemas`.

### Full pipeline

```
WUFI XML file (UTF-8)
    |  get_WUFI_XML_file_as_dict()
    v
dict[str, Tag | list | dict]
    |  WUFIplusProject.model_validate(data)
    |    unpack_xml_tag() -> unit type validation -> SI values
    v
WUFIplusProject (Pydantic, fully typed, all SI)
    |  convert_WUFI_XML_to_PHX_project()
    |    _PhxProject() -> type libraries first, then variants
    v
PhxProject (in-memory PHX model)
```

---

## Adding a New Exporter

To add a new export target (e.g., `to_NewFormat/`):

1. **Create a new package** under `PHX/` following the naming convention `to_<FORMAT>/`
2. **Choose a schema pattern:**
    - For tree-structured outputs (XML, JSON): class-name dispatch with schema functions (see `to_WUFI_XML/` or `to_METr_JSON/`)
    - For flat/tabular outputs: section-based builders (see `to_PPP/`)
3. **Implement the layers:**
    - Schema module — functions that describe how each PHX class maps to the target format
    - Converter module — `getattr`-based schema lookup by PHX class name
    - Builder module — entry point that walks the `PhxProject` object graph
    - File writer — handles target encoding and file I/O
4. **Create a CLI entry point** (e.g., `hbjson_to_newformat.py`) that wires up the common pipeline parameters
5. **Add tests** in `tests/test_to_<format>/` with reference output files
