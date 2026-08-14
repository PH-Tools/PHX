# PHX (Passive House Exchange):

### The Passive House Exchange (PHX) package enables users to move building model data into and out of the Passive House energy modeling software platforms (PHPP or WUFI-Passive).

PHX converts live Honeybee models carrying honeybee-ph data into 'PH-Style' objects and then manages data input to proprietary PH calculators such as PHPP and WUFI-Passive. File-oriented workflows may first read a [HBJSON](https://github.com/ladybug-tools/honeybee-schema/wiki) file into that Honeybee model.

PHX itself does not have serialization / deserialization, and is not intended to be stored or written directly: it is an in-memory-only model which is created as a middle-step when moving the building data from the source (usually a HBJSON file) to the destination (PHPP, WUFI-Passive).

This library is designed to be used as part of the [Honeybee-PH plugin](https://github.com/PH-Tools/honeybee_ph) workflow, or other similar tools which require interfacing with the Passive House modeling platforms.

```python
from PHX.conversion import from_honeybee

phx_project = from_honeybee(hb_model)
```

<img width="1692" alt="Screen Shot 2023-10-28 at 11 53 01 AM" src="https://github.com/PH-Tools/PHX/assets/69652712/03ff5cfa-4a81-4077-b475-e35b39190640">

## Packages:

- **conversion:** Public live Honeybee / honeybee-ph `Model` → transient `PhxProject` API.

- **from_HBJSON:** Honeybee conversion implementation and HBJSON file-reading helpers retained for existing workflows.

- **from_WUFI_XML:** Modules used to create a new PHX model from an existing WUFI-Passive XML file.

- **from_PHPP:** Modules used to create a new PHX model from an existing PHPP file.'

- **model:** The PHX model classes and structures. These objects are designed to be built by one of the 'from\_\*' libraries above.

- **to_PHPP:** Libraries to allow for the export of PHX data to a PHPP Microsoft Excel spreadsheet.

- **to_WUFI_XML:** Libraries to allow for the export of a WUFI-Passive XML file with all of the PHX model data. This XML file can then be opened from within the WUFI-Passive application.

- **to_PPP / to_METr_JSON:** Additional exporters for the PPP and METr-JSON target formats.

## Development:

- **Python:** 3.10+ (CPython). Runs as a library/CLI, not inside Rhino (except the `PHX/run.py` Grasshopper shim).
- **Tests:** `python -m pytest tests/`.
- **Commits:** conventional commits (`feat(scope):` / `fix(scope):`) drive semantic-release auto-publishing to PyPI.
- **Agent/contributor orientation:** [`CLAUDE.md`](CLAUDE.md), the [`context/`](context/) folder, and the deep architecture docs under [`docs/dev/`](docs/dev/) and [`docs/reference/`](docs/reference/).

# More Information:

For more information on the use of these tools, check out the the Passive House Tools website:
https://passivehousetools.com/

![Tests](https://github.com/PH-Tools/PHX/actions/workflows/ci.yml/badge.svg)
![versions](https://img.shields.io/pypi/pyversions/PHX.svg)
