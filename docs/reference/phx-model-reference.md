---
title: PHX Model Reference
description: "Complete object graph, module map, design patterns, and testing conventions for the PHX in-memory data model."
ref_meta:
  schema_version: "PHX 1.x"
  maintainer: "bldgtyp"
  source: "PHX / docs"
llm_purpose: "Complete object graph, module map, design patterns, and testing conventions for the PHX in-memory data model"
llm_use_when: "Before navigating, modifying, extending, or testing any PHX model class"
llm_related:
  - "reference/wufi-xml-schema.md"
  - "dev/architecture.md"
---

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
| Room ventilation-unit assignment | `PhxSpace.vent_unit_id_num` → matching variant ventilation device, or `None` |
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
| `model/components.py` | `PhxComponentBase`, `PhxComponentOpaque`, `PhxComponentAperture`, `PhxApertureElement`, `PhxApertureElementPsiInstall`, `PhxApertureShadingDimensions`, `PhxComponentThermalBridge` | Surfaces, windows, thermal bridges |
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

### Project-scoped identities

Public Honeybee and WUFI conversions build each `PhxProject` inside a fresh
`IdentityAllocator` scope. Integer IDs are allocated in reference-domain
namespaces (assemblies, windows, components, variant geometry, HVAC, etc.), so
sequential and concurrent conversions of independent projects cannot change one
another's output. Imported WUFI IDs are explicit claims and are reserved for
later allocation.

The completed project retains its allocator. Later model construction that must
join the project graph uses `with phx_project.identity_scope(owner=variant.id_num):`
for variant-owned objects. Concurrent mutation of the same project is not
supported. Legacy `_count` ClassVars remain only as a compatibility fallback for
standalone constructors outside a project identity scope.

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

### Ventilation Assignment Integrity

`PhxSpace.vent_unit_id_num` is `None` when no mechanical ventilation unit is
assigned. Positive identifiers resolve against all ventilation devices in the
Space's `PhxVariant`; the display name is descriptive and never repairs a bad
reference. Duct identifiers are scoped to their owning
`PhxMechanicalSystemCollection`, so separate collections may reuse a numeric
device ID without making their ducts ambiguous.

Call `PhxVariant.ventilation_assignment_issues()` to collect every invalid
Space and duct reference, or `assert_ventilation_assignments_ready()` to raise
one aggregate `VentilationAssignmentError`. Project-level exporters run the
same readiness check before writing. A Space with supply/extract airflow may
remain unassigned when the variant has no mechanical ventilation devices; once
a device is modeled, every mechanically ventilated Space must resolve to one
device.

### Occupancy Channels and Lighting EFLH

HBJSON occupancy reaches WUFI XML and METr JSON through two independent channels:

| Channel | PHX field | WUFI XML | METr JSON |
|---------|-----------|----------|-----------|
| Explicit Passive House occupancy | `PhxZone.res_occupant_quantity` | `OccupantQuantityUserDef` | `loadsZ.nOcc` |
| Derived Honeybee People load | `PhxSpace.occupancy.load.people_per_m2` / `peak_occupancy` | `LoadPerson/NumberOccupants` | `loadsZ.lPersZ[].nOcc` |

The channels are mutually exclusive per dwelling group. If any pre-merge Honeybee Room in a
dwelling group carries explicit PH occupancy, PHX suppresses the derived Space occupancy for
every Room in that group. Otherwise it derives occupants from the Honeybee People load. An
untagged Room is a group of one. The gate is group-level because the upstream *Set Occupancy*
workflow normalizes `people_per_area` across the whole dwelling; a per-Room gate would leak
derived occupants from the other Rooms and double-count the same people. PHX distributes each
Room's derived total among its Spaces by their share of total PH Space floor area, preserving
the Room total even when the Spaces do not tile the Honeybee Room.

`PhxScheduleLighting.full_load_lighting_hours` is an equivalent-full-load-hours (EFLH) value:
the schedule's annual operating-window hours multiplied by its relative utilization factor,
clamped to 0-8760. It is not merely the operating window. This follows the Phius non-residential
loads protocol: the shared occupancy utilization pattern describes when the space is in use,
while lighting EFLH carries the load-weighted annual lighting operation and overrides the
lighting pattern in WUFI.

### Dict-Keyed vs List Collections
- **Dict-keyed** (by identifier/key): `assembly_types`, `window_types`, `shade_types`, `_devices`, `_thermal_bridges` — O(1) lookup
- **List-ordered**: `variants`, `zones`, `spaces`, `_components` — ordered iteration

### Component Classes Use `__init__` (not dataclass)
`PhxComponentBase` subclasses (`PhxComponentOpaque`, `PhxComponentAperture`, `PhxApertureShadingDimensions`, `PhxComponentThermalBridge`) use plain `__init__` with a shared `_count` on `PhxComponentBase`, unlike most other model classes which use `@dataclass`.

### Library References
Constructions/windows/shades live in project-level dicts; components reference them by identifier, not by embedding.

### Piping Hierarchy
DHW piping uses a three-level hierarchy: `PhxPipeTrunk` → `PhxPipeBranch` → `PhxPipeElement` (fixtures). Each `PhxPipeElement` contains `PhxPipeSegment` objects. Recirculation piping is stored separately as flat `PhxPipeElement` entries.

### `unique_key` Property
Classes that may be grouped by construction or type expose a `unique_key` property. Components with the same `unique_key` can be merged via `__add__`. For example, `PhxComponentOpaque` instances sharing the same assembly identifier have the same `unique_key` and can be combined into a single component.

### Enum Runtime Extension
Some enums use `_missing_()` to handle unknown values at runtime rather than raising. For example, `ComponentExposureExterior` returns a fallback member for unrecognized integer values from WUFI XML imports. This prevents deserialization failures on non-standard model files.

---

## Honeybee to PHX Concept Mapping

| Honeybee | PHX | Notes |
|----------|-----|-------|
| `Model` | `PhxProject` | Top-level container. One HB Model → one PhxProject. |
| `Room` | `PhxZone` (via `PhxBuilding`) | HB Rooms grouped by `ph_bldg_segment` into zones. |
| `Room` (sub-space) | `PhxSpace` | Each HB Room → one or more PhxSpaces within a zone. |
| `Face` (Wall/Floor/Roof) | `PhxComponentOpaque` | Each HB Face → component with geometry + assembly ref. |
| `Aperture` | `PhxComponentAperture` / `PhxApertureElement` | Windows within opaque components. Each element carries resolved per-edge psi-install values (aperture-level Install Types over window-type defaults); WUFI/METr exports synthesize content-keyed window-type variants from them (`model/transforms.py`), PHPP writes them per-row. |
| `OpaqueConstruction` | `PhxConstructionOpaque` | Reusable assembly in `PhxProject.assembly_types`. |
| `WindowConstruction` | `PhxConstructionWindow` | Reusable window type in `PhxProject.window_types`. |
| `EnergyMaterial` | `PhxMaterial` | Part of construction layers. |
| `IdealAirSystem` / HVAC | `PhxMechanicalSystemCollection` | HB HVAC → PHX device collections. |
| `Schedule` | `PhxSchedule*` | Operating patterns with utilization periods. |
| `ph_bldg_segment` | `PhxVariant` | Rooms sharing a segment become one variant. |

### Key Structural Differences

**Libraries vs inline:** Honeybee stores constructions/schedules inline on rooms and faces. PHX extracts them into project-level libraries and components reference by identifier.

**Room → Zone + Space split:** A single HB Room may become one PhxZone with one PhxSpace, or multiple rooms may be grouped into a single zone with multiple spaces (grouped by `ph_bldg_segment`).

**WUFI load-only Spaces:** A WUFI zone may contain person/lighting utilization-zone records that
have no matching `RoomsVentilation` record. The WUFI importer still creates a `PhxSpace` for each
person-load record so those loads survive a round-trip. Such a Space has zero ventilation airflow;
the WUFI exporter includes it in `LoadsPersonsPH` / `LoadsLightingsPH` but correctly omits it from
`RoomsVentilation`.

**Program composition:** HB stores loads and schedules separately. PHX pairs them: `PhxProgramVentilation` = `PhxLoadVentilation` + `PhxScheduleVentilation`.

**HVAC disaggregation:** HB uses high-level `IdealAirSystem`. PHX disaggregates into specific device types (ventilators, heaters, heat pumps, hot water tanks, piping) with usage profiles specifying coverage percentages.

**Ventilation absence:** A Honeybee Room with no PH ventilation system becomes
an unassigned `PhxSpace` and creates no PHX ventilator. A source mechanical
system must contain a real `Ventilator`; incomplete systems fail before any
PHX device, duct, or source-ID mutation occurs. Empty exterior-duct collections
remain empty.

### Conversion Entry Points

The public live-object entry point is:

- `PHX.conversion.from_honeybee()` — convert a live Honeybee + honeybee-ph `Model` to a transient
  `PhxProject` without file I/O or serialization

The established implementation remains under `from_HBJSON/` for backwards compatibility and
for the file-oriented CLI workflows:

- `create_project.convert_hb_model_to_PhxProject()` — legacy-compatible conversion implementation
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

### Legacy class-counter reset

Use `reset_class_counters` only for tests that directly construct standalone
model objects and explicitly assert compatibility numbering:

```python
@pytest.fixture
def reset_class_counters():
    _reset_phx_class_counters()
    try:
        yield
    finally:
        _reset_phx_class_counters()
```

Public conversion and reference-case tests must not reset counters or reload
modules. Their determinism is part of the conversion-boundary contract.

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
2. Use `reset_class_counters` only when asserting standalone fallback numbering
3. Test `__str__`/`__repr__` to catch serialization issues early
4. Test `__add__` if the class supports merging
5. Test `unique_key` if the class supports grouping
6. For new HVAC device types, test both standalone creation and addition to `PhxMechanicalSystemCollection`

### Common Test Patterns

**Unit test (model class):**
```python
def test_blank_project(reset_class_counters):
    proj = project.PhxProject()
    assert str(proj)
    assert not proj.assembly_types
    assert not proj.variants
```

**Property / behavior test:**
```python
def test_component_face_type(reset_class_counters):
    comp = PhxComponentOpaque()
    comp.face_type = ComponentFaceType.WALL
    comp.exposure_exterior = ComponentExposureExterior.EXTERIOR
    assert comp.is_above_grade_wall is True
```

**Merge / addition test:**
```python
def test_space_addition(reset_class_counters):
    space_a = PhxSpace()
    space_a.floor_area = 100.0
    space_b = PhxSpace()
    space_b.floor_area = 50.0
    merged = space_a + space_b
    assert merged.floor_area == 150.0
```

**End-to-end reference case:**
```python
def test_xml_output(to_xml_reference_cases):
    hbjson_file, xml_file = to_xml_reference_cases
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(hbjson_file)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)
    phx_project = create_project.convert_hb_model_to_PhxProject(hb_model)
    xml_txt = xml_builder.generate_WUFI_XML_from_object(phx_project)
    expected = read_WUFI_XML_file.get_WUFI_xml_file_as_str(xml_file)
    assert xml_txt == expected
```

**Geometry fixture:**
```python
@pytest.fixture
def polygon_1x1x0():  # 1m x 1m square at z=0
    p = PhxPolygon("no_name", 100.0, PhxVertix(1,1,0), PhxVector(0,0,1), plane)
    p.add_vertix(PhxVertix(0,0,0))
    p.add_vertix(PhxVertix(0,1,0))
    p.add_vertix(PhxVertix(1,1,0))
    p.add_vertix(PhxVertix(1,0,0))
    return p
```
