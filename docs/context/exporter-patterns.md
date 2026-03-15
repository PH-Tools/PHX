# PHX Exporter Patterns

Guide for understanding existing exporters and adding new ones.

## Common Pipeline

All exporters follow the same first two steps:

```python
from PHX.from_HBJSON import read_HBJSON_file, create_project

# 1. Read HBJSON → Honeybee Model
hb_json_dict = read_HBJSON_file.read_hb_json_from_file(source_path)
hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

# 2. Convert HB Model → PHX Project
phx_project = create_project.convert_hb_model_to_PhxProject(
    hb_model,
    _group_components=True,
    _merge_faces=False,          # True | False | float tolerance
    _merge_spaces_by_erv=False,
    _merge_exhaust_vent_devices=False,
)
```

Then each exporter serializes `PhxProject` to its target format.

## WUFI XML Exporter (`to_WUFI_XML/`)

**Pattern:** Schema-based recursive conversion

1. `xml_schemas.py` defines `_ClassName()` functions (leading underscore + PascalCase matching the PHX class name) that return lists of `xml_writable` objects (`XML_Node`, `XML_List`, `XML_Object`)
2. `xml_converter.py` discovers schema functions by class name: `PhxProject` → `_PhxProject()`
3. `xml_builder.py` recursively walks the writable tree → builds XML DOM → `toprettyxml()`
4. `xml_txt_to_file.py` writes UTF-8 XML with optional timestamped backup

```python
from PHX.to_WUFI_XML import xml_builder, xml_txt_to_file
xml_txt = xml_builder.generate_WUFI_XML_from_object(phx_project)
xml_txt_to_file.write_XML_text_file(target_path, xml_txt)
```

## PHPP Exporter (`PHPP/`)

**Pattern:** Sheet-by-sheet Excel writing via xlwings

1. `phpp_app.PHPPConnection` connects to an open Excel workbook
2. Sheet controllers in `sheet_io/` (28 files) handle per-worksheet read/write
3. `phpp_model/` data classes represent PHPP rows, generating `XlItem` objects (cell address + value)
4. `phpp_localization/` handles PHPP version (v9/v10) and language (EN/DE/ES) differences

```python
from PHX.xl import xl_app
from PHX.PHPP import phpp_app
xl = xl_app.XLConnection(xl_framework=xw, output=print)
phpp_conn = phpp_app.PHPPConnection(xl)
with phpp_conn.xl.in_silent_mode():
    phpp_conn.write_certification_config(phx_project)
    phpp_conn.write_climate_data(phx_project)
    # ... 15+ write operations
```

## PPP Exporter (`to_PPP/`)

**Pattern:** Section-based text serialization

1. `ppp_schemas.py` defines functions that generate `PppSection` objects (name, rows, cols, values)
2. `ppp_builder.py` orchestrates section generation with cross-reference maps (assembly IDs → PPP indices)
3. `ppp_txt_to_file.py` writes UTF-16LE text (no BOM)

```python
from PHX.to_PPP import ppp_builder, ppp_txt_to_file
ppp_file = ppp_builder.build_ppp_file(phx_project)
ppp_txt_to_file.write_ppp_file(target_path, ppp_file)
```

## Adding a New Exporter

To add a new export target (e.g., `to_METr_JSON/`):

1. Create a new package under `PHX/` following the naming convention `to_<FORMAT>/`
2. Implement a schema/converter layer that walks the `PhxProject` object graph
3. Implement a builder that orchestrates the conversion
4. Implement a file writer for the target encoding/format
5. Create a CLI entry point script (e.g., `hbjson_to_metr.py`)
6. Add tests in `tests/test_to_<format>/` with reference output files
