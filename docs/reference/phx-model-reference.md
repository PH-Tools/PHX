# PHX Model Reference

PHX (Passive House Exchange) is an in-memory intermediate representation of Passive House building data. Models are created from source formats (HBJSON, WUFI XML) and consumed by exporters (WUFI XML, PHPP, PPP, METr JSON). PHX models are never serialized directly.

---

## Object Graph

```
PhxProject
├── assembly_types: dict[str, PhxConstructionOpaque]
│   └── layers: list[PhxLayer]
│       ├── material: PhxMaterial
│       └── divisions: PhxLayerDivisionGrid (optional, for composite layers)
│           └── cells: list[PhxLayerDivisionCell]
├── window_types: dict[str, PhxConstructionWindow]
│   ├── frame_top/right/bottom/left: PhxWindowFrameElement
│   └── _id_num_shade → PhxWindowShade
├── shade_types: dict[str, PhxWindowShade]
├── utilization_patterns_ventilation: UtilizationPatternCollection_Ventilation
├── utilization_patterns_occupancy: UtilizationPatternCollection_Occupancy
├── utilization_patterns_lighting: UtilizationPatternCollection_Lighting
├── project_data: PhxProjectData
│   ├── customer: ProjectData_Agent
│   ├── building: ProjectData_Agent
│   ├── owner: ProjectData_Agent
│   ├── designer: ProjectData_Agent
│   └── project_date: PhxProjectDate
└── variants: list[PhxVariant]
    ├── building: PhxBuilding
    │   ├── _components: list[PhxComponentOpaque]
    │   │   ├── assembly → PhxConstructionOpaque (ref by identifier)
    │   │   ├── polygons: list[PhxPolygon]
    │   │   │   └── vertices: list[PhxVertix]
    │   │   └── apertures: list[PhxComponentAperture]
    │   │       ├── window_type → PhxConstructionWindow (ref by identifier)
    │   │       └── elements: list[PhxApertureElement]
    │   │           ├── polygon: PhxPolygonRectangular | PhxPolygon | None
    │   │           └── shading_dimensions: PhxApertureShadingDimensions
    │   └── zones: list[PhxZone]
    │       ├── spaces: list[PhxSpace]
    │       │   ├── ventilation: PhxProgramVentilation (load + schedule)
    │       │   ├── occupancy: PhxProgramOccupancy (load + schedule)
    │       │   └── lighting: PhxProgramLighting (load + schedule)
    │       ├── _thermal_bridges: dict[str, PhxComponentThermalBridge]
    │       ├── elec_equipment_collection: PhxElectricDeviceCollection
    │       │   └── _devices: dict[str, PhxElectricalDevice subclass]
    │       └── exhaust_ventilator_collection: PhxExhaustVentilatorCollection
    ├── site: PhxSite
    │   ├── location: PhxLocation
    │   ├── climate: PhxClimate
    │   │   └── peak_heating/cooling: PhxClimatePeakLoad
    │   ├── ground: PhxGround
    │   ├── phpp_codes: PhxPHPPCodes
    │   └── energy_factors: PhxSiteEnergyFactors
    │       ├── pe_factors: dict[str, PhxPEFactor]
    │       └── co2_factors: dict[str, PhxCO2Factor]
    ├── phius_cert: PhxPhiusCertification
    │   ├── phius_certification_criteria: PhxPhiusCertificationCriteria
    │   ├── phius_certification_settings: PhxPhiusCertificationSettings
    │   └── ph_building_data: PhxPhBuildingData
    │       ├── setpoints: PhxSetpoints
    │       ├── summer_ventilation: PhxSummerVentilation
    │       └── foundations: list[PhxFoundation]
    │           (subtypes: PhxHeatedBasement, PhxUnHeatedBasement,
    │            PhxSlabOnGrade, PhxVentedCrawlspace)
    ├── phi_cert: PhxPhiCertification
    │   └── phi_certification_settings: PhxPhiCertificationSettings
    └── _mech_collections: list[PhxMechanicalSystemCollection]
        ├── _devices: dict[str, AnyMechDevice]
        │   (PhxDeviceVentilator, PhxHeater*, PhxHeatPump*, PhxHotWaterTank)
        ├── _distribution_piping_trunks: dict[str, PhxPipeTrunk]
        │   └── branches: list[PhxPipeBranch]
        │       └── fixtures: list[PhxPipeElement]
        │           └── segments: dict[str, PhxPipeSegment]
        ├── _distribution_piping_recirc: dict[str, PhxPipeElement]
        ├── _distribution_ducting: dict[str, PhxDuctElement]
        │   └── segments: dict[str, PhxDuctSegment]
        ├── supportive_devices: PhxSupportiveDeviceCollection
        │   └── _devices: dict[str, PhxSupportiveDevice]
        └── renewable_devices: PhxRenewableDeviceCollection
            └── _devices: dict[str, PhxDevicePhotovoltaic]
```

---

## Quick Lookup

| You want to find... | Navigate to... |
|---------------------|----------------|
| Wall/floor/roof surfaces | `PhxBuilding._components` (list of `PhxComponentOpaque`) |
| Windows in a wall | `PhxComponentOpaque.apertures` (list of `PhxComponentAperture`) |
| Construction/U-value | `PhxComponentOpaque.assembly` → `PhxConstructionOpaque` |
| Material layers | `PhxConstructionOpaque.layers` → `PhxLayer` → `PhxMaterial` |
| Mixed-material layers | `PhxLayer.divisions` → `PhxLayerDivisionGrid` → `PhxLayerDivisionCell` |
| Heat-flow pathways | `PhxConstructionOpaque.heat_flow_pathways` → `list[PhxHeatFlowPathway]` |
| Window properties | `PhxComponentAperture.window_type` → `PhxConstructionWindow` |
| Window frames | `PhxConstructionWindow.frame_top/right/bottom/left` → `PhxWindowFrameElement` |
| Room ventilation rates | `PhxSpace.ventilation` → `PhxProgramVentilation.load` → `PhxLoadVentilation` |
| Occupancy schedule | `PhxSpace.occupancy` → `PhxProgramOccupancy.schedule` → `PhxScheduleOccupancy` |
| Thermal bridges | `PhxZone.thermal_bridges` (returns `ValuesView[PhxComponentThermalBridge]`) |
| HVAC devices | `PhxVariant.mech_collections` → `PhxMechanicalSystemCollection.devices` |
| Hot water piping | `PhxMechanicalSystemCollection.dhw_distribution_trunks` → `PhxPipeTrunk` → `PhxPipeBranch` |
| Recirculation piping | `PhxMechanicalSystemCollection.dhw_recirc_piping` → `list[PhxPipeElement]` |
| Ventilation ducting | `PhxMechanicalSystemCollection.vent_ducting` → `list[PhxDuctElement]` |
| Electrical equipment | `PhxZone.elec_equipment_collection` → `PhxElectricDeviceCollection` |
| Exhaust ventilators | `PhxZone.exhaust_ventilator_collection` → `PhxExhaustVentilatorCollection` |
| Supportive devices | `PhxMechanicalSystemCollection.supportive_devices` → `PhxSupportiveDeviceCollection` |
| Renewable energy (PV) | `PhxMechanicalSystemCollection.renewable_devices` → `PhxRenewableDeviceCollection` |
| Climate/location | `PhxVariant.site` → `PhxSite` → `.location`, `.climate` |
| Certification data | `PhxVariant.phius_cert` or `PhxVariant.phi_cert` |
| Foundation data | `PhxVariant.phius_cert.ph_building_data.foundations` |
| All assembly types | `PhxProject.assembly_types` (dict by identifier) |
| All window types | `PhxProject.window_types` (dict by identifier) |
| All shade types | `PhxProject.shade_types` (dict by identifier) |

---

## Module Map

| Module | Key Classes | Purpose |
|--------|------------|---------|
| `model/project.py` | `PhxProject`, `PhxVariant`, `PhxProjectData`, `ProjectData_Agent`, `PhxProjectDate`, `WufiPlugin` | Top-level containers |
| `model/building.py` | `PhxBuilding`, `PhxZone` | Building geometry container, thermal zones |
| `model/components.py` | `PhxComponentBase`, `PhxComponentOpaque`, `PhxComponentAperture`, `PhxApertureElement`, `PhxApertureShadingDimensions`, `PhxComponentThermalBridge` | Surfaces, windows, thermal bridges |
| `model/constructions.py` | `PhxConstructionOpaque`, `PhxConstructionWindow`, `PhxWindowFrameElement`, `PhxLayer`, `PhxLayerDivisionGrid`, `PhxLayerDivisionCell`, `PhxMaterial`, `PhxColor` | Assembly/material definitions |
| `model/assembly_pathways.py` | `PhxHeatFlowPathway`, `identify_heat_flow_pathways()`, `compute_r_value_from_pathways()` | ISO 6946 heat-flow pathway analysis for composite assemblies |
| `model/geometry.py` | `PhxPolygon`, `PhxPolygonRectangular`, `PhxVertix`, `PhxVertix2D`, `PhxVector`, `PhxPlane`, `PhxLineSegment`, `PhxGraphics3D` | 3D geometry primitives |
| `model/spaces.py` | `PhxSpace` | Individual room/subzone with programs |
| `model/certification.py` | `PhxPhiCertification`, `PhxPhiCertificationSettings`, `PhxPhiusCertification`, `PhxPhiusCertificationCriteria`, `PhxPhiusCertificationSettings`, `PhxPhBuildingData`, `PhxSetpoints`, `PhxSummerVentilation` | Passive house certification data |
| `model/elec_equip.py` | `PhxElectricalDevice` (base), `PhxElectricDeviceCollection`, + device subclasses (see below) | Household electrical devices |
| `model/ground.py` | `PhxFoundation` (base), `PhxHeatedBasement`, `PhxUnHeatedBasement`, `PhxSlabOnGrade`, `PhxVentedCrawlspace` | Ground/foundation models |
| `model/phx_site.py` | `PhxSite`, `PhxLocation`, `PhxClimate`, `PhxClimatePeakLoad`, `PhxClimateIterOutput`, `PhxGround`, `PhxPEFactor`, `PhxCO2Factor`, `PhxSiteEnergyFactors`, `PhxPHPPCodes` | Location and climate data |
| `model/shades.py` | `PhxWindowShade` | Window shading devices |
| `model/utilization_patterns.py` | `UtilizationPatternCollection_Ventilation`, `UtilizationPatternCollection_Occupancy`, `UtilizationPatternCollection_Lighting` | Schedule collections |
| `model/enums/` | Various enums | `building.py`, `hvac.py`, `elec_equip.py`, `foundations.py`, `phx_site.py`, `phi_certification_phpp_9.py`, `phi_certification_phpp_10.py`, `phius_certification.py` |
| `model/schedules/` | `PhxScheduleVentilation` (+ `Vent_UtilPeriods`, `Vent_OperatingPeriod`), `PhxScheduleOccupancy`, `PhxScheduleLighting` | Time-based operating patterns |
| `model/loads/` | `PhxLoadVentilation`, `PhxLoadOccupancy`, `PhxLoadLighting` | Numeric load definitions |
| `model/programs/` | `PhxProgramVentilation`, `PhxProgramOccupancy`, `PhxProgramLighting` | Load + Schedule pairs |

### Electrical Equipment Devices (`model/elec_equip.py`)

All subclass `PhxElectricalDevice`:

| Class | Device Type |
|-------|------------|
| `PhxDeviceDishwasher` | Kitchen dishwasher |
| `PhxDeviceClothesWasher` | Laundry washer |
| `PhxDeviceClothesDryer` | Laundry dryer |
| `PhxDeviceRefrigerator` | Refrigerator |
| `PhxDeviceFreezer` | Freezer |
| `PhxDeviceFridgeFreezer` | Fridge/freezer combo |
| `PhxDeviceCooktop` | Kitchen cooking |
| `PhxDeviceMEL` | Misc. electric loads |
| `PhxDeviceLightingInterior` | Interior lighting |
| `PhxDeviceLightingExterior` | Exterior lighting |
| `PhxDeviceLightingGarage` | Garage lighting |
| `PhxDeviceCustomElec` | User-defined electric |
| `PhxDeviceCustomLighting` | User-defined lighting |
| `PhxDeviceCustomMEL` | User-defined MEL |
| `PhxElevatorHydraulic` | Hydraulic elevator |
| `PhxElevatorGearedTraction` | Geared traction elevator |
| `PhxElevatorGearlessTraction` | Gearless traction elevator |

### HVAC Subsystem (`model/hvac/`)

| Module | Key Classes |
|--------|------------|
| `_base.py` | `PhxMechanicalDevice` (base), `PhxMechanicalDeviceParams` (base), `PhxUsageProfile` |
| `collection.py` | `PhxMechanicalSystemCollection`, `PhxExhaustVentilatorCollection`, `PhxSupportiveDeviceCollection`, `PhxRenewableDeviceCollection`, `PhxZoneCoverage` |
| `ventilation.py` | `PhxDeviceVentilation` (base), `PhxDeviceVentilator`, `PhxDeviceVentilatorParams`, `PhxExhaustVentilatorBase`, `PhxExhaustVentilatorRangeHood`, `PhxExhaustVentilatorDryer`, `PhxExhaustVentilatorUserDefined`, `PhxExhaustVentilatorParams` |
| `heating.py` | `PhxHeatingDevice` (base), `PhxHeaterElectric`, `PhxHeaterBoilerFossil`, `PhxHeaterBoilerWood`, `PhxHeaterDistrictHeat`, + corresponding `*Params` classes |
| `heat_pumps.py` | `PhxHeatPumpDevice` (base), `PhxHeatPumpAnnual`, `PhxHeatPumpMonthly`, `PhxHeatPumpHotWater`, `PhxHeatPumpCombined`, + corresponding `*Params` classes |
| `water.py` | `PhxHotWaterDevice` (base), `PhxHotWaterTank`, `PhxHotWaterTankParams` |
| `piping.py` | `PhxPipeTrunk`, `PhxPipeBranch`, `PhxPipeElement`, `PhxPipeSegment`, `PhxRecirculationParameters` |
| `ducting.py` | `PhxDuctElement`, `PhxDuctSegment` |
| `renewable_devices.py` | `PhxDevicePhotovoltaic`, `PhxDevicePhotovoltaicParams` |
| `supportive_devices.py` | `PhxSupportiveDevice`, `PhxSupportiveDeviceParams` |
| `cooling_params.py` | `PhxCoolingParams` (collection), `PhxCoolingVentilationParams`, `PhxCoolingRecirculationParams`, `PhxCoolingDehumidificationParams`, `PhxCoolingPanelParams` |

---

## Design Patterns

### ClassVar Counters
Every model class has `_count: ClassVar[int] = 0` auto-incremented in `__post_init__` or `__init__`, assigning `id_num`. Tests must reset these for predictable IDs.

### UUID + id_num Dual Identity
Constructions and devices carry both a `uuid.UUID | str` identifier and an integer `id_num`. The UUID is for lookup/deduplication; `id_num` is for sequential output numbering.

### `__add__` Merging
The following model classes support `+` for consolidation (merging coplanar surfaces, combining spaces by ERV, etc.):

- `PhxComponentOpaque` — merge surfaces with same assembly
- `PhxComponentAperture` — merge windows with same type
- `PhxComponentThermalBridge` — merge TBs with same psi/type (length-weighted psi recalculation)
- `PhxSpace` — merge spaces by ERV assignment
- `PhxLoadVentilation` — combine airflow values
- `PhxUsageProfile` — combine coverage percentages
- `PhxMechanicalDevice` (and subclasses) — merge device quantities/coverage
- `PhxMechanicalDeviceParams` (and subclasses) — merge device parameters
- Various exhaust ventilator types, `PhxHotWaterTank`, `PhxSupportiveDevice`, `PhxDevicePhotovoltaic`

### Program = Load + Schedule
Ventilation, occupancy, and lighting each follow: `PhxProgram* = PhxLoad* + PhxSchedule*`. The load holds numeric values (airflow, people, watts); the schedule holds operating periods and hours.

### Dict-Keyed vs List Collections
- **Dict-keyed** (by identifier/key): `assembly_types`, `window_types`, `shade_types`, `_devices`, `_thermal_bridges` — O(1) lookup
- **List-ordered**: `variants`, `zones`, `spaces`, `_components` — ordered iteration

### Component Classes Use `__init__` (not dataclass)
`PhxComponentBase` subclasses (`PhxComponentOpaque`, `PhxComponentAperture`, `PhxApertureShadingDimensions`, `PhxComponentThermalBridge`) use plain `__init__` with a shared `_count` on `PhxComponentBase`, unlike most other model classes which use `@dataclass`.

### Library References
Constructions/windows/shades live in project-level dicts; components reference them by identifier, not by embedding.

### Piping Hierarchy
DHW piping uses a three-level hierarchy: `PhxPipeTrunk` → `PhxPipeBranch` → `PhxPipeElement` (fixtures). Each `PhxPipeElement` contains `PhxPipeSegment` objects. Recirculation piping is stored separately as flat `PhxPipeElement` entries.

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
- `create_variant.py` — build PhxVariant from HB model
- `create_building.py`, `create_rooms.py`, `create_geometry.py` — geometry conversion
- `create_assemblies.py` — construction/material conversion
- `create_hvac.py` — HVAC device conversion
- `create_schedules.py` — schedule conversion
- `create_elec_equip.py` — electrical equipment conversion
- `create_shades.py` — shade device conversion
- `create_shw_devices.py` — service hot water device conversion
- `create_foundations.py` — foundation/ground conversion
- `cleanup.py`, `cleanup_merge_faces.py` — post-conversion cleanup (vertex welding, face merging, component grouping)

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
