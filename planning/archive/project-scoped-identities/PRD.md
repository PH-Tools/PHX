# PRD — Project-scoped deterministic identities

**Status:** Complete · 2026-08-14
**Author:** Ed May + Codex
**Kind:** Architecture/correctness feature (PHX model + converters + exporters)

---

## WHAT

Define and implement a project-scoped identity allocation contract so two
independent Honeybee → PHX conversions in the same process produce the same IDs
they would produce sequentially, even when executed concurrently.

### Current design

Many PHX model classes use mutable class-global `_count` values and assign
`id_num` in `__post_init__()`/`__init__()`. The current reference fixtures reset
selected counters before and after conversion. The public conversion functions
do not. Global counters therefore span all projects and all conversions in one
interpreter.

Numeric IDs originated as WUFI `IdentNr` values and foreign-key-style references.
METr now consumes many of the same identities. PHPP uses a smaller subset for
in-memory joins (ventilator assignments and host polygons); PPP does not consume
`id_num`. See `AUDIT.md` for the complete classification.

The defect is currently reproduced without concurrency: converting the same
committed HBJSON fixture twice in one process without the test reset yields
different WUFI XML (324 unified-diff lines in the 2026-08-14 audit). Concurrency
adds interleaving, but is not required to demonstrate process-global leakage.

### Required guarantee

> Independent PHX projects may be built and exported concurrently in one Python
> process. Each project's identifiers and cross-references are deterministic for
> its own source model and options. Concurrent conversion of the same mutable
> Honeybee object, and concurrent mutation of the same PHX project, are not
> required to be supported.

### Target architecture

Introduce an explicit per-conversion/per-project identity context or allocator
used by importers/builders. The exact type is an implementation decision, but it
must satisfy:

1. Allocation namespaces follow the target/reference contract, not merely the
   Python class hierarchy. IDs may repeat across independent namespaces.
2. Constructors/builders on public conversion paths obtain IDs from one fresh
   project/conversion allocator without resetting shared module state.
3. Every reference (Space → ventilator, duct → ventilator, component/library
   links, target rows) uses IDs from the same owning context.
4. Ordering is based on deterministic source traversal, not thread scheduling.
5. Direct standalone construction remains usable. If legacy global counters
   remain as a compatibility fallback, the public conversion path must not rely
   on them.
6. Existing explicit IDs imported from WUFI are claimed in the correct namespace,
   preserved on export, and cause later automatic allocation to skip them.
7. Duplicate IDs fail validation only where they are duplicates in the same
   reference namespace. The current format legitimately reuses values such as
   `1` across variants, materials, schedules, and typed mechanical-device groups.
8. Dangling integer references fail validation before an affected export.
9. The first release preserves the clean-process WUFI and METr golden bytes,
   including current gaps caused by temporary/default object construction.
10. An allocator scope is always released in `finally`; a failed conversion
    cannot leak claims into the next conversion.

Do not solve this by calling the existing test counter-reset functions at the
start of conversion; concurrent resets are themselves unsafe.

### Audit scope

Inventory every `_count: ClassVar`, every manual `id_num` overwrite, every
exporter lookup by numeric ID, and every test module reload/reset. Classify each
as:

- project-owned identity;
- target-local row numbering;
- harmless diagnostic/display sequence;
- removable legacy state.

Only project-owned/reference-bearing identities must share the project context.
Target-local row numbering stays inside the exporter. Unused legacy counters are
documented and deprecated separately; they are not deleted if doing so would
renumber protected golden output.

### Compatibility and rollout

- Preserve existing clean-process reference output for existing fixtures. Do not
  re-record goldens merely to accommodate a new numbering scheme.
- Add the allocator behind conversion builders before deprecating direct global
  counter dependence.
- Keep the PHPP xl-replay final written cell-state identical.
- Update the model reference, testing guidance, and new-class checklist so new
  classes do not automatically repeat the global-counter pattern.
- Conventional commit/release semantics apply; this is likely a feature-level
  change even if output remains stable.

## WHY

The POC's calculations are fast enough that a web service can handle several
requests concurrently. PHX's current test guidance explicitly relies on global
counter resets and module reloads for deterministic IDs, which is a warning that
the runtime identity mechanism is process-global.

Even if CPython's GIL prevents a torn integer increment, it does not prevent
valid increments from interleaving between projects. The result can be
nondeterministic output and cross-reference bugs that appear only under load.
Engineering results must not depend on which request constructed a ventilator
first.

## Acceptance criteria

- Repeated sequential conversion of independently loaded copies of one source
  produces identical IDs and exported references without test-only resets.
- Parallel conversion of distinct sources produces the same per-project output
  as sequential baselines.
- One invalid conversion does not alter identities in a concurrent valid one.
- Duplicate/conflicting imported IDs in one reference namespace are reported
  before export; legal reuse across namespaces remains accepted.
- Existing WUFI, METr, PPP, and PHPP/xl-replay fixtures remain stable.
- Test fixtures no longer need global reset/reload for code paths migrated to
  the project allocator; any remaining use is documented.
- WUFI-imported explicit IDs round-trip and reserve later automatic allocations.
- `PhxPhBuildingData` export reads its instance identity, never class state.
- HBJSON source-property ID writebacks remain compatible in the first release
  and always equal the allocated PHX object they mirror.
- Public docs state the independent-project concurrency guarantee.
- Full `python -m pytest tests/` passes, including a bounded parallel regression
  repeated several times.
