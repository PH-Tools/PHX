# PHX

Passive House Exchange — format conversion between [Honeybee-PH](../honeybee-ph/), PHPP, and WUFI-Passive.

PHX provides an in-memory intermediate representation of Passive House building data. Models are created from source formats (HBJSON, WUFI XML) and exported to target formats (WUFI XML, PHPP Excel, PPP, METr JSON).

## Installation

```bash
pip install PHX
```

## Key Features

- Bidirectional WUFI-Passive XML read/write
- PHPP Excel export (localized field mapping)
- Complete building model: geometry, constructions, windows, HVAC, DHW, renewables, certification
- Honeybee-PH to PHX conversion pipeline

## Links

- [Source Code](https://github.com/PH-Tools/PHX)
- [PyPI](https://pypi.org/project/PHX/)
- [Model Reference](../reference/phx-model-reference.md)
