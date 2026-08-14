# AUDIT — `_count`, `id_num`, references, tests, and fixtures

**Audit date:** 2026-08-14

**Scope:** `PHX/`, `tests/`, committed reference fixtures, and relevant Git history

**Result:** `_count` is not one contract. It currently implements target IDs,
foreign-key-style references, internal joins, unused legacy sequence numbers,
and compatibility-sensitive allocation side effects.

## Executive finding

`_count` was introduced in the 2022 initial commit together with the WUFI writer.
The reason was concrete: WUFI objects carry integer `IdentNr` values, and other
WUFI fields refer to those values (`IdentNrAssembly`, `IdentNrWindowType`,
`IdentNrPoints`, `IdentNrPolygons`, `IdentNrUtilizationPatternVent`,
`IdentNrVentilationUnit`, and others). The counters supplied those integers while
the Honeybee/PHX string or UUID `identifier` supplied library lookup identity.

METr later reused the same object IDs and references. PHPP uses only two identity
joins: aperture polygon → host polygon and Space/duct → ventilator. PPP has no
`id_num` consumer.

The design stopped being safe when PHX began serving more than one conversion per
interpreter. The counter belongs to a Python class for the life of the process,
not to a PHX project. A second conversion therefore starts after the first one's
last number. Threads can interleave valid increments. The GIL does not provide
project isolation.

## Reproduced behavior

The audit loaded the committed
`tests/reference_files/from_grasshopper_tests/hbjson/Default_Model_Single_Zone.hbjson`
twice, creating a new Honeybee model each time, then ran the public HBJSON → PHX
→ WUFI path twice in one process without `tests/conftest.py` resets.

- `equal_without_reset = False`
- 324 unified-diff lines
- examples: ventilation schedule `1 → 2`, occupancy pattern `1 → 2`, variant
  `1 → 2`, and first exported vertex `27 → 63`

This is a deterministic sequential reproduction of process-global leakage. It
does not claim an energy-calculation defect: the exported IDs and references can
remain internally aligned while the bytes are nondeterministic. Concurrency makes
the allocation order depend on request scheduling and increases the risk around
the second reads and class-state exporter noted below.

## Why PHX has two identities

| identity | purpose | examples |
|---|---|---|
| `identifier` (string/UUID) | stable lookup/deduplication in Python collections and correspondence with Honeybee objects | project construction/window/schedule dictionaries, mechanical-device keys |
| `id_num` (integer) | target-format record number or compact internal reference | WUFI `IdentNr`, METr `id`, assembly/window/material refs, vertex/polygon refs, ventilator refs |

They are not interchangeable. Replacing every numeric ID with a UUID would break
the WUFI/METr schema. Replacing every dictionary key with the integer would lose
stable source identity and deduplication behavior.

## Counter inventory

There are 27 explicit `_count: ClassVar[int]` declarations. Inherited
`self.__class__._count += 1` creates additional effective leaf-class counters for
electrical and mechanical subclasses.

### Project-owned and exported/reference-bearing

| counter family | allocation behavior | consumers / references | required namespace |
|---|---|---|---|
| `PhxVariant` | per concrete class | WUFI/METr variant `IdentNr`/`id` | project variants |
| `PhxZone` | per concrete class | WUFI/METr zone ID; foundation and HVAC zone coverage refs | variant zones |
| `PhxComponentBase` | one shared sequence for opaque components, apertures, aperture elements, shading dimensions, and thermal bridges | only opaque/aperture IDs are exported; component → polygon; component → assembly/window/shade | variant/building components, preserving legacy burns initially |
| `PhxVertix` | fixed base class | WUFI/METr vertex record; polygon vertex refs | variant geometry vertices |
| `PhxPolygon` | fixed base class | WUFI/METr polygon record; component polygon refs; parent-child aperture refs; PHPP host lookup | variant geometry polygons |
| `PhxMaterial` | concrete class | WUFI/METr material record; assembly layer/grid material refs | project materials |
| `PhxConstructionOpaque` | concrete class | WUFI/METr assembly record; opaque component ref | project assembly types |
| `PhxConstructionWindow` | concrete class | WUFI/METr window type; aperture ref | project window types |
| `PhxWindowShade` | concrete class | WUFI/METr shade type; window/aperture ref | project shade types |
| `PhxScheduleVentilation` | concrete class | WUFI/METr pattern record; Space ref; PHPP pattern lookup | project ventilation patterns |
| `PhxScheduleOccupancy` | concrete class | WUFI/METr pattern record; person and lighting load refs | project occupancy patterns |
| `PhxPhBuildingData` | concrete class | WUFI/METr PH-building case ID | variant PH-building data |
| `PhxMechanicalSystemCollection` | concrete class | WUFI/METr HVAC system ID | variant HVAC systems |
| mechanical-device leaf classes | `PhxMechanicalDevice.__post_init__` increments `self.__class__`; most leaf types therefore start at 1 independently | WUFI/METr device IDs; ventilator IDs are referenced by Spaces/ducts and PHPP | preserve typed device families; ventilator reference namespace must be unambiguous in its owning variant/collection |
| `PhxDuctElement` | concrete class | WUFI/METr duct ID; assigned ventilator IDs are separate refs | mechanical distribution ducts |
| `PhxPipeElement`, `PhxPipeBranch`, `PhxPipeTrunk` | three independent sequences | WUFI/METr nested DHW row IDs | twig/branch/trunk lists respectively |

### Present but not currently exported as identity

| counter family | actual use | disposition |
|---|---|---|
| `PhxVertix2D` | equality/internal geometry only; its own `_count` is never incremented because `__post_init__` increments `PhxVertix._count` | compatibility hazard: currently burns 3D vertex IDs; preserve the burn in release 1, normalize only with approved golden movement |
| `PhxSpace` | unit tests, `__str__`, merge-created instance sequencing; WUFI/METr Rooms have no Space ID field | legacy/display sequence; no exporter reference |
| `PhxScheduleLighting` | collection lookup and WUFI-import bookkeeping; export uses the occupancy pattern ID as `RoomCategory` and has no lighting-pattern record | internal/legacy; do not confuse it with the exported occupancy pattern |
| `PhxElectricalDevice` and leaf subclasses | unit tests/equality-facing model state; WUFI HomeDevice and METr home-device records do not emit the ID | legacy; per-leaf counters arise through inheritance |
| `PhxSupportiveDevice` | model lookup; neither WUFI nor METr supportive-device schema emits its ID | legacy; currently double-increments its own counter |
| renewable/supportive/exhaust collection counters | model lookup/display only; collection IDs are not exported | legacy |
| `PhxExhaustVentilatorBase` | model lookup only; WUFI/METr exhaust records do not emit an ID | legacy; subclass and base counters both increment before the base ID wins |
| `PhxComponentThermalBridge`, `PhxApertureElement`, `PhxApertureShadingDimensions` | inherit the shared component ID but their target schemas do not emit it | compatibility burns in the component namespace |

These are candidates for later cleanup, not for silent deletion in the first
project-scoping release. Some unused objects consume a sequence shared with an
exported class; deleting the increment renumbers clean-process goldens.

## Stored integer references that must remain aligned

### Envelope and geometry

- `PhxComponentOpaque.assembly_type_id_num` → `PhxConstructionOpaque.id_num`
- `PhxComponentAperture.window_type_id_num` → assigned window type
- `PhxComponentAperture.shade_type_id_num` → assigned shade type
- component `polygon_ids` → `PhxPolygon.id_num`
- polygon `vertices_id_numbers` → `PhxVertix.id_num`
- polygon `child_polygon_ids` → aperture polygons
- `interior_attachment_id` / `exposure_interior` → zone/variant-side attachment IDs
- mixed-layer `division_material_id_numbers` → `PhxMaterial.id_num`

### Programs, zones, and systems

- Space ventilation schedule → project ventilation pattern ID
- Space occupancy schedule → project occupancy pattern ID
- `PhxSpace.vent_unit_id_num` → assigned ventilator ID
- `PhxDuctElement.assigned_vent_unit_ids` → ventilator IDs
- `PhxZoneCoverage.zone_num` → zone ID
- foundations emitted under a zone carry that zone's ID in METr

### PHPP-only joins

- aperture polygon ID → host polygon child-ID lookup
- Space ventilator ID → mechanical-device lookup → PHPP ventilator row
- duct ventilator ID → exporter-local ventilator ordinal

PHPP row ordinals are target-local and must stay in `PHPP/phpp_app.py`; they are
not project model identities.

## HBJSON conversion: why comments say “keep IDs aligned”

The HBJSON builder currently writes allocated PHX IDs back into mutable Honeybee
PH properties before later builders read them:

- opaque/window/shade construction `properties.ph.id_num`
- ventilation/occupancy/lighting schedule PH properties
- merged Room PH properties for variant/interior attachment identity
- ventilation, heating, and heat-pump system objects

Later code reads those values for component library references, Space ventilator
references, and interior attachments. This explains why `_count` is not merely
an exporter detail.

The first project-scoping release preserves this observable writeback behavior,
but the assigned value must come from the new PHX object/allocator, never from a
second read of a mutable class `_count`. Removing source mutation is a separate
compatibility decision because downstream callers may inspect those PH properties
after conversion.

## Manual overwrites and explicit imported IDs

The WUFI importer constructs objects (thereby consuming a global count) and then
overwrites 16 instance IDs from source `IdentNr` values. This includes variants,
zones, geometry, components, libraries, schedules, PH-building data, one HVAC
collection path, and the ventilator path.

Problems:

1. The constructor's provisional number remains consumed.
2. The explicit number is not reserved from later automatic allocation.
3. Duplicate explicit IDs are not uniformly rejected.
4. Several non-ventilator mechanical import builders do not restore the source
   device ID, so WUFI device round-trip behavior is inconsistent by type.
5. Library `add_*` methods repair some duplicates by renumbering, but do so after
   references may already have been derived and cover only three libraries.

The allocator must support an explicit claim/reserve operation. Import builders
may retain compatibility burns, but later automatic allocation must skip claimed
values and duplicate claims in the same namespace must fail deterministically.

## High-risk implementation details

### Exporter reads class state

`PHX/to_WUFI_XML/xml_schemas.py::_PhxPhBuildingData` writes
`XML_Node("IdentNr", bd._count)` instead of `bd.id_num`. Constructing an unrelated
PH-building object after `bd` can therefore change `bd`'s later export. This must
be corrected early and pinned with a red test. The audit reproduced this directly:
the same `PhxPhiusCertification` instance exported `<IdentNr>1</IdentNr>` before
constructing another certification object and `<IdentNr>2</IdentNr>` afterward.

### Second reads of `_count`

HB builders sometimes construct an object, then overwrite its `id_num` from the
class counter again. Another conversion can increment the counter between those
operations. The write must use the identity already allocated to the instance.

### Inherited counters are not one namespace

`self.__class__._count += 1` creates/shadows a counter on each leaf class. Current
fixtures consequently contain several mechanical device types with ID `1` in the
same project. A blanket “all IDs unique in the project” validator would reject
existing fixtures and is wrong. Validation must follow the target/reference
namespace, with special attention to the untyped Python lookup used by PHPP.

### Incidental allocation is visible

- `PhxLayer` creates a default `PhxMaterial` before the HB builder replaces it,
  producing the even-number material pattern visible in METr fixtures.
- `PhxComponentOpaque` creates a default assembly before assignment.
- `PhxComponentAperture` creates a default window type before assignment.
- each `PhxSpace` creates three schedule objects before assigned schedules replace
  them.
- aperture elements, shading dimensions, and thermal bridges consume the shared
  component counter without exporting their own IDs.
- WUFI polygon import creates temporary plane vertices before restoring source
  geometry IDs.

Release 1 must reproduce clean-process output. It may model these as explicit
compatibility allocations rather than preserve every awkward class implementation,
but it may not silently close the gaps.

## Tests and fixtures

Static audit counts on 2026-08-14:

- 27 explicit production `_count` declarations
- 23 production Python files mentioning `_count`
- 113 test files using `reset_class_counters`
- 16 WUFI importer instance-ID overwrites from `IdentNr`
- 12 committed XML files, 8 JSON files, and 10 HBJSON/JSON source fixtures in
  `tests/reference_files/`

`tests/conftest.py` resets many base and leaf counters before/after WUFI and METr
reference cases. It does **not** currently reload model modules, despite the public
model-reference document still describing `_reload_phx_classes()`.

The reset list is incomplete and contains duplication:

- omitted: `PhxVertix2D`, `PhxPipeElement`, lighting schedule, supportive device,
  and several collection counters
- duplicated: ventilation base/ventilator resets
- anomalous: assigns `PhxScheduleVentilation.id_num = 0` on the class

This is evidence that a manual global-reset registry is not a sustainable runtime
or test contract. Direct standalone constructor unit tests may keep a narrowly
documented legacy reset during transition. Public conversion tests must stop
depending on it once migrated.

## Compatibility requirements derived from the audit

1. Preserve clean-process WUFI and METr bytes; compare before approving any golden
   change.
2. Preserve all integer reference pairs, not merely record IDs.
3. Preserve legal reuse across independent/typed namespaces.
4. Preserve WUFI explicit IDs and reserve them against later allocation.
5. Keep direct constructors usable without requiring callers to create a project.
6. Do not reset globals inside a public conversion.
7. Ensure scope cleanup after exceptions and task/thread isolation.
8. Keep PHPP exporter-local row numbers local.
9. Keep the xl-replay final cell state identical.
10. Do not claim PPP needs identity migration; verify it as a negative regression.
11. Update the stale public testing/new-class guidance only after implementation.
12. Treat deletion of compatibility burns or unused counters as a separately
    approved output-normalization change.

## Files that define the implementation surface

- allocator/context: new `PHX/model/identity.py`
- public scopes: core `PHX/from_HBJSON/create_project.py` (so every caller is
  covered), the live-object facade `PHX/conversion.py`, and
  `PHX/from_WUFI_XML/phx_converter.py`
- counter-bearing model files listed in the inventory above
- HB writebacks: `create_assemblies.py`, `create_schedules.py`,
  `create_variant.py`, `create_building.py`, `create_rooms.py`, `create_hvac.py`
- WUFI explicit claims: `PHX/from_WUFI_XML/phx_schemas.py`
- validation/export: WUFI, METr, and PHPP entry points
- transition fixture: `tests/conftest.py`
- public canon after green implementation: `docs/reference/phx-model-reference.md`,
  `docs/dev/architecture.md`, `docs/dev/exporter-patterns.md`
