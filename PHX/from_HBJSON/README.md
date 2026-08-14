# from_HBJSON

These modules implement Honeybee → PHX conversion and provide the file-reading
helpers used by HBJSON-oriented workflows. New callers with an existing live
Honeybee model should use the stable public facade:

```python
from PHX.conversion import from_honeybee

phx_project = from_honeybee(hb_model)
```

The legacy `create_project.convert_hb_model_to_PhxProject()` entry point remains
available for backwards compatibility.
