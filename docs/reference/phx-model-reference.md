# PHX Model Reference

PHX (Passive House Exchange) is an in-memory intermediate representation of Passive House building data. Models are created from source formats (HBJSON, WUFI XML) and consumed by exporters (WUFI XML, PHPP, PPP, METr JSON). PHX models are never serialized directly.

---

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

---

## Quick Lookup

| You want to find... | Navigate to... |
|---------------------|----------------|
| Wall/floor/roof surfaces | `PhxBuilding._components` (list of `PhxComponentOpaque`) |
| Windows in a wall | `PhxComponentOpaque.apertures` (list of `PhxComponentAperture`) |
| Construction/U-value | `PhxComponentOpaque.assembly` → `PhxConstructionOpaque` |
| Material layers | `PhxConstructionOpaque.layers` → `PhxLayer` → `PhxMaterial` |
| Window properties | `PhxComponentAperture.window_type` → `PhxConstructionWindow` |
| Room ventilation rates | `PhxSpace.ventilation` → `PhxProgramVentilation.load` → `PhxLoadVentilation` |
| Occupancy schedule | `PhxSpace.occupancy` → `PhxProgramOccupancy.schedule` |
| Thermal bridges | `PhxZone.thermal_bridges` (dict of `PhxComponentThermalBridge`) |
| HVAC devices | `PhxVariant.mech_collections` → `PhxMechanicalSystemCollection.devices` |
| Hot water piping | `PhxMechanicalSystemCollection` → `PhxPipeTrunk` / `PhxPipeBranch` |
| Electrical equipment | `PhxZone.elec_equipment_collection` → `PhxElectricDeviceCollection` |
| Climate/location | `PhxVariant.site` → `PhxSite` |
| Certification data | `PhxVariant.phius_cert` or `PhxVariant.phi_cert` |
| All assembly types | `PhxProject.assembly_types` (dict by identifier) |
| All window types | `PhxProject.window_types` (dict by identifier) |

---

## Module Map

| Module | Key Classes | Purpose |
|--------|------------|---------|
| `model/project.py` | `PhxProject`, `PhxVariant`, `PhxProjectData` | Top-level containers |
| `model/building.py` | `PhxBuilding`, `PhxZone` | Building geometry container, thermal zones |
| `model/components.py` | `PhxComponentOpaque`, `PhxComponentAperture`, `PhxComponentThermalBridge` | Surfaces, windows, thermal bridges |
| `model/constructions.py` | `PhxConstructionOpaque`, `PhxConstructionWindow`, `PhxMaterial`, `PhxLayer` | Assembly/material definitions |
| `model/geometry.py` | `PhxPolygon`, `PhxVertix`, `PhxVector`, `PhxPlane` | 3D geometry primitives |
| `model/spaces.py` | `PhxSpace` | Individual room/subzone with programs |
| `model/certification.py` | `PhxPhiCertification`, `PhxPhiusCertification`, `PhxPhBuildingData` | Passive house certification data |
| `model/elec_equip.py` | `PhxElectricDeviceCollection`, `PhxDevice*` | Household electrical devices |
| `model/ground.py` | `PhxFoundation` | Ground/foundation models |
| `model/phx_site.py` | `PhxSite` | Location and climate data |
| `model/shades.py` | `PhxWindowShade` | Window shading devices |
| `model/utilization_patterns.py` | `UtilizationPatternCollection_*` | Schedule collections |
| `model/enums/` | Various enums | `building.py`, `hvac.py`, `elec_equip.py`, `foundations.py`, `phx_site.py` |
| `model/schedules/` | `PhxScheduleVentilation`, `PhxScheduleOccupancy`, `PhxScheduleLighting` | Time-based operating patterns |
| `model/loads/` | `PhxLoadVentilation`, `PhxLoadOccupancy`, `PhxLoadLighting` | Numeric load definitions |
| `model/programs/` | `PhxProgramVentilation`, `PhxProgramOccupancy`, `PhxProgramLighting` | Load + Schedule pairs |

### HVAC Subsystem (`model/hvac/`)

| Module | Key Classes |
|--------|------------|
| `_base.py` | `PhxMechanicalDevice` (base), `PhxUsageProfile` |
| `collection.py` | `PhxMechanicalSystemCollection`, `PhxRenewableDeviceCollection`, `PhxExhaustVentilatorCollection` |
| `ventilation.py` | `PhxDeviceVentilation`, `PhxDeviceVentilator`, `PhxExhaustVentilator*` |
| `heating.py` | `PhxHeaterElectric`, `PhxHeaterBoilerFossil`, `PhxHeaterBoilerWood`, `PhxHeaterDistrictHeat` |
| `heat_pumps.py` | `PhxHeatPumpAnnual`, `PhxHeatPumpMonthly`, `PhxHeatPumpHotWater`, `PhxHeatPumpCombined` |
| `water.py` | `PhxHotWaterTank`, `PhxHotWaterDevice` |
| `piping.py` | `PhxPipeTrunk`, `PhxPipeBranch`, `PhxRecirculationParameters` |
| `ducting.py` | `PhxDuctElement` |
| `renewable_devices.py` | `PhxDevicePhotovoltaic` |
| `supportive_devices.py` | `PhxSupportiveDevice` |
| `cooling_params.py` | Cooling parameter classes |

---

## Design Patterns

### ClassVar Counters
Every model class has `_count: ClassVar[int] = 0` auto-incremented in `__post_init__` or `__init__`, assigning `id_num`. Tests must reset these for predictable IDs.

### UUID + id_num Dual Identity
Constructions and devices carry both a `uuid.UUID | str` identifier and an integer `id_num`. The UUID is for lookup/deduplication; `id_num` is for sequential output numbering.

### `__add__` Merging
`PhxComponentOpaque`, `PhxComponentAperture`, `PhxSpace`, `PhxLoadVentilation`, `PhxUsageProfile`, `PhxMechanicalDevice` all support `+` for consolidation (merging coplanar surfaces, combining spaces by ERV, etc.).

### Program = Load + Schedule
Ventilation, occupancy, and lighting each follow: `PhxProgram* = PhxLoad* + PhxSchedule*`. The load holds numeric values (airflow, people, watts); the schedule holds operating periods and hours.

### Dict-Keyed vs List Collections
- **Dict-keyed** (by identifier/key): `assembly_types`, `window_types`, `devices`, `thermal_bridges` — O(1) lookup
- **List-ordered**: `variants`, `zones`, `spaces`, `_components` — ordered iteration

### Component Classes Use `__init__` (not dataclass)
`PhxComponentBase` subclasses (`PhxComponentOpaque`, `PhxComponentAperture`) use plain `__init__`, unlike most other model classes which use `@dataclass`.

### Library References
Constructions/windows live in project-level dicts; components reference them by identifier, not by embedding.

---

## Honeybee to PHX Concept Mapping

| Honeybee | PHX | Notes |
|----------|-----|-------|
| `Model` | `PhxProject` | Top-level container. One HB Model → one PhxProject. |
| `Room` | `PhxZone` (via `PhxBuilding`) | HB Rooms grouped by `ph_bldg_segment` into zones. |
| `Room` (sub-space) | `PhxSpace` | Each HB Room → one or more PhxSpaces within a zone. |
| `Face` (Wall/Floor/Roof) | `PhxComponentOpaque` | Each HB Face → component with geometry + assembly ref. |
| `Aperture` | `PhxComponentAperture` / `PhxApertureElement` | Windows within opaque components. |
| `OpaqueConstruction` | `PhxConstructionOpaque` | Reusable assembly in `PhxProject.assembly_types`. |
| `WindowConstruction` | `PhxConstructionWindow` | Reusable window type in `PhxProject.window_types`. |
| `EnergyMaterial` | `PhxMaterial` | Part of construction layers. |
| `IdealAirSystem` / HVAC | `PhxMechanicalSystemCollection` | HB HVAC → PHX device collections. |
| `Schedule` | `PhxSchedule*` | Operating patterns with utilization periods. |
| `ph_bldg_segment` | `PhxVariant` | Rooms sharing a segment become one variant. |

### Key Structural Differences

**Libraries vs inline:** Honeybee stores constructions/schedules inline on rooms and faces. PHX extracts them into project-level libraries and components reference by identifier.

**Room → Zone + Space split:** A single HB Room may become one PhxZone with one PhxSpace, or multiple rooms may be grouped into a single zone with multiple spaces (grouped by `ph_bldg_segment`).

**Program composition:** HB stores loads and schedules separately. PHX pairs them: `PhxProgramVentilation` = `PhxLoadVentilation` + `PhxScheduleVentilation`.

**HVAC disaggregation:** HB uses high-level `IdealAirSystem`. PHX disaggregates into specific device types (ventilators, heaters, heat pumps, hot water tanks, piping) with usage profiles specifying coverage percentages.

### Conversion Entry Points

The PHX repo's `from_HBJSON/` package handles Honeybee → PHX conversion:

- `create_project.convert_hb_model_to_PhxProject()` — main entry point
- `create_building.py`, `create_rooms.py`, `create_geometry.py` — geometry conversion
- `create_assemblies.py` — construction/material conversion
- `create_hvac.py` — HVAC device conversion
- `create_schedules.py` — schedule conversion
- `cleanup.py` — post-conversion cleanup (vertex welding, face merging, component grouping)

---

## Testing Patterns

### Class Counter Reset

Tests **must** reset `_count` ClassVars for predictable IDs:

```python
@pytest.fixture
def reset_class_counters():
    _reset_phx_class_counters()
    try:
        yield
    finally:
        _reset_phx_class_counters()
```

When adding a new model class with `_count`, add it to `_reset_phx_class_counters()` in `conftest.py`.

### Test Organization

Tests mirror the source structure under `tests/`:

| Directory | Coverage |
|-----------|----------|
| `test_model/` | Unit tests for model classes (building, components, constructions, geometry, hvac, spaces, etc.) |
| `test_from_HBJSON/` | HBJSON → PHX conversion tests |
| `test_to_WUFI_xml/` | PHX → XML export tests (includes end-to-end reference cases) |
| `test_from_WUFI/` | XML → PHX reverse conversion tests |
| `test_PHPP/` | PHPP Excel export tests |
| `test_to_PPP/` | PPP export tests |

### Writing New Tests

1. Place tests in the directory that mirrors the source module path
2. Use `reset_class_counters` fixture for any test that creates model objects
3. Test `__str__`/`__repr__` to catch serialization issues early
4. Test `__add__` if the class supports merging
5. Test `unique_key` if the class supports grouping
6. For new HVAC device types, test both standalone creation and addition to `PhxMechanicalSystemCollection`
