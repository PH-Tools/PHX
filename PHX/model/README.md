# PHX Model:
The PHX (Passive House Exchange) model is a generic Passive-House data model which can be used 
to represent a Passive House building independently of any specific software platform. This model is used to standardize the input / output and translation across different platforms (PHPP, WUFI, C3RRO, Ladybug, etc.).

# PHX Class Behavior:
All PHX classes are used only to store and organize object data / attributes. Class behavior should be limited to data storage, cleaning, and validation of input/output data. All software specific specific behavior and references should be moved to separate modules and packages such as the [Honeybee-PH](https://github.com/PH-Tools/honeybee_ph) libraries.

# PHX Class Usage:
The PHX model classes are not designed to be 'run' on their own. These classes are data classes which are used by other interfaces (Rhino, WUFI, PHPP, etc.) and processes.

# PHX Model Structure:
Ths primary structure / nesting of a full PHX model would look like the following:
(note: Many object attribute fields and details omitted for clarity)
```
Project
├─ Project Data
├─ Assembly Types
│   └── Layers
│         └── Materials
├─ Window Types
│   ├─ Frame
│   └─ Glass
├─ Utilization Patterns
└─ Building Segments
    ├─ Passive House Certification Data
    ├─ Location / Climate
    ├─ Mechanical System <Collection>
    │   ├─ Heating System(s)
    │   ├─ Cooling System(s)
    │   └─ Hot-Water System(s)
    └─ Building
        ├─ Components (Opaque)
        │   ├─ Polygons
        │   └─ Components (Apertures)
        │       └─ Polygons
        └─ Zones
            ├─ Interior Spaces
            └─ Electrical Equipment / Appliances

```

# PHX Python Version:
All PHX Classes should be written to comply with Python 3.7 format. In the Rhino use-case, these PHX classes are used from the Ladybug-Tools standard python interpreter and so should ensure compatibility with the python version installed by the Ladybug Tools plugin.

Note: It is recommended to include type hints on all PHX classes for documentation purposes.


