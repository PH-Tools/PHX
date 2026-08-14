# PRD — Project-scoped deterministic identities

**Status:** Requested · 2026-08-14
**Author:** Ed May + Codex
**Kind:** Architecture/correctness feature (PHX model + converters + exporters)

---

## WHAT

Define and implement a project-scoped identity allocation contract so two
independent Honeybee → PHX conversions in the same process produce the same IDs
they would produce sequentially, even when executed concurrently.

### Current design

Many PHX model classes use mutable class-global `_count` values and assign
`id_num` in `__post_init__()`/`__init__()`. Tests reset or reload classes to
obtain deterministic reference output. That is workable for sequential tests,
but global counters span all projects and all conversions in one interpreter.

Numeric IDs are not cosmetic. They are used for device/space/duct references and
target-format row identities. Interleaved construction can therefore make a
project's exported numbers depend on unrelated concurrent work.

### Required guarantee

> Independent PHX projects may be built and exported concurrently in one Python
> process. Each project's identifiers and cross-references are deterministic for
> its own source model and options. Concurrent mutation of the same project is
> not required to be supported.

### Target architecture

Introduce an explicit per-conversion/per-project identity context or allocator
used by importers/builders. The exact type is an implementation decision, but it
must satisfy:

1. Counters are scoped by model class and project/conversion context.
2. Constructors/builders obtain IDs without resetting shared module state.
3. Every reference (Space → ventilator, duct → ventilator, component/library
   links, target rows) uses IDs from the same owning context.
4. Ordering is based on deterministic source traversal, not thread scheduling.
5. Direct standalone construction remains usable. If legacy global counters
   remain as a compatibility fallback, the public conversion path must not rely
   on them.
6. Existing explicit IDs imported from WUFI/PHPP are preserved according to the
   source contract and reserve/conflict-check allocator ranges as needed.
7. Duplicate IDs inside one project fail validation before export.

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
Target-local row numbering may be better allocated inside the exporter.

### Compatibility and rollout

- Preserve existing reference output for existing fixtures.
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

- Repeated sequential conversion of one source produces identical IDs and
  exported references without test-only resets.
- Parallel conversion of distinct sources produces the same per-project output
  as sequential baselines.
- One invalid conversion does not alter identities in a concurrent valid one.
- Duplicate/conflicting imported IDs are reported before export.
- Existing WUFI, METr, PPP, and PHPP/xl-replay fixtures remain stable.
- Test fixtures no longer need global reset/reload for code paths migrated to
  the project allocator; any remaining use is documented.
- Public docs state the independent-project concurrency guarantee.
- Full `python -m pytest tests/` passes, including a bounded parallel regression
  repeated several times.

