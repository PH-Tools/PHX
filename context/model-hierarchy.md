# PHX Model Hierarchy

## Object Graph

```
PhxProject
├── assembly_types: dict[str, PhxConstructionOpaque]
│   └── layers: list[PhxLayer]
│       └── material: PhxMaterial
│           └── divisions: PhxLayerDivisionGrid (optional, for composite layers)
├── window_types: dict[str, PhxConstructionWindow]
├── shade_types: dict[str, PhxWindowShade]
├── utilization_patterns (ventilation, occupancy, lighting collections)
├── project_data: PhxProjectData (customer, owner, designer agents)
└── variants: list[PhxVariant]
    ├── building: PhxBuilding
    │   ├── _components: list[PhxComponentOpaque]
    │   │   ├── assembly → PhxConstructionOpaque
    │   │   ├── polygons: list[PhxPolygon]
    │   │   │   └── vertices: list[PhxVertix]
    │   │   └── apertures: list[PhxComponentAperture]
    │   │       ├── window_type → PhxConstructionWindow
    │   │       └── elements: list[PhxApertureElement]
    │   │           ├── polygon: PhxPolygon
    │   │           └── shading_dimensions: PhxApertureShadingDimensions
    │   └── zones: list[PhxZone]
    │       ├── spaces: list[PhxSpace]
    │       │   ├── ventilation: PhxProgramVentilation (load + schedule)
    │       │   ├── occupancy: PhxProgramOccupancy (load + schedule)
    │       │   └── lighting: PhxProgramLighting (load + schedule)
    │       ├── thermal_bridges: dict[str, PhxComponentThermalBridge]
    │       ├── elec_equipment_collection: PhxElectricDeviceCollection
    │       └── exhaust_ventilator_collection: PhxExhaustVentilatorCollection
    ├── site: PhxSite (location, climate data)
    ├── phius_cert: PhxPhiusCertification
    │   └── ph_building_data: PhxPhBuildingData
    │       └── foundations: list[PhxFoundation]
    ├── phi_cert: PhxPhiCertification
    └── mech_collections: list[PhxMechanicalSystemCollection]
        ├── devices: dict[str, PhxMechanicalDevice]
        │   (ventilators, heaters, heat pumps, hot water devices, etc.)
        ├── supportive_devices: PhxSupportiveDeviceCollection
        └── renewable_devices: PhxRenewableDeviceCollection (PV)
```

## Design Patterns

- **Dataclasses** with `ClassVar[int]` counters for auto-incrementing `id_num` fields
- **Component classes** (`PhxComponentBase` subclasses) use plain `__init__` instead of dataclass
- **UUID identifiers** on constructions and devices (`uuid.UUID | str`) alongside `id_num`
- **`__add__` merging** on `PhxComponentOpaque`, `PhxComponentAperture`, `PhxSpace`, `PhxLoadVentilation`, `PhxUsageProfile`, `PhxMechanicalDevice` — used for consolidation during cleanup
- **Program = Load + Schedule** composition pattern for ventilation, occupancy, lighting
- **Dict-keyed collections** for lookups (assemblies, windows, devices); list collections for ordered access (zones, spaces, variants)

## Key Concept Mappings (Honeybee → PHX)

| Honeybee | PHX |
|----------|-----|
| Model | PhxProject |
| Room | PhxZone (via PhxBuilding) |
| Room (sub-space) | PhxSpace |
| Face (Wall/Floor/Roof) | PhxComponentOpaque |
| Aperture | PhxComponentAperture / PhxApertureElement |
| OpaqueConstruction | PhxConstructionOpaque |
| WindowConstruction | PhxConstructionWindow |
| EnergyMaterial | PhxMaterial |
| IdealAirSystem / HVAC | PhxMechanicalSystemCollection |
| Schedule | PhxScheduleVentilation / PhxScheduleOccupancy / PhxScheduleLighting |
