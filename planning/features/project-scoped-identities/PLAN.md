# PLAN — Project-scoped identities

Read `AUDIT.md` and `PRD.md` first. This file is the sequencing overview. The
self-contained handoff briefs are in `plans/`; implement exactly one phase at a
time using red-green-refactor.

## Recommended architecture

Add a small `IdentityAllocator` with explicit namespaces and three operations:

```python
next_id(namespace) -> int
claim_id(namespace, explicit_id) -> int
is_claimed(namespace, value) -> bool
```

Allocation occurs through a conversion-local context whose token is reset in a
`finally` block. The core HB conversion function owns the scope so both the new
`PHX.conversion.from_honeybee()` facade and legacy direct callers are covered;
the WUFI conversion entry point does the same. Each independent conversion gets
a fresh allocator. Nested builders and model `__add__` operations inherit it
without adding allocator parameters to every public model constructor.

The completed `PhxProject` retains the allocator and exposes an explicit context
manager for post-conversion mutations. Concurrent mutation of that same project
is not supported. An allocator is intentionally not made internally thread-safe;
ownership isolation is the contract.

Direct standalone model construction outside a project scope continues to use
the existing class-counter fallback in release 1. This limits API breakage and
keeps focused model tests meaningful while public conversion paths stop using
global state.

### Namespace rules

- Namespace keys represent the consuming list/reference domain, not Python MRO.
- Component subclasses that historically share `PhxComponentBase` keep one
  compatibility namespace during release 1.
- Mechanical leaf classes retain typed namespaces where current target output
  legally reuses IDs; ventilator references receive explicit validation.
- Variant-local objects include the variant ownership in their namespace.
- Project libraries/patterns use project ownership.
- Imported explicit IDs are claims, not post-hoc unchecked assignments.

### Compatibility shim

Use one allocation helper from every migrated constructor:

```python
allocate_identity(namespace, legacy_counter_owner) -> int
```

Inside a project scope it delegates to the allocator and does not mutate the
legacy `ClassVar`. Outside a scope it performs the current class increment. This
is temporary but testable and avoids a flag or allocator argument on dozens of
constructors.

## Phase sequence

| phase | outcome | blocked on |
|---|---|---|
| 0 — baselines and red tests | protected bytes, identity projection, deterministic reproductions | nothing |
| 1 — allocator and scope primitive | isolated allocation/claim API; no entity migration | 0 |
| 2 — project libraries, patterns, variants, certification | first project-owned namespaces; fixes `bd._count` export | 1 |
| 3 — envelope and geometry | components, polygons, vertices, materials, constructions, shades | 2 |
| 4 — zones, Spaces, HVAC, and distribution | all reference-bearing runtime identities migrated | 3 |
| 5 — WUFI explicit identity claims | source IDs preserved/reserved; conflicts rejected | 4 |
| 6 — project validator and exporter gates | duplicate/dangling refs fail before affected export | 5 |
| 7 — transition cleanup, docs, and closeout | public conversion resets retired; complete regression evidence | 6 |

No phase re-records golden fixtures. If a clean-process golden changes, stop and
classify the change before proceeding.

## Red-green-refactor protocol for every phase

1. Add the smallest test that states the phase contract.
2. Run it and record the expected failure message/diff.
3. Implement only enough production code to make it green.
4. Run the phase's focused suite.
5. Run WUFI + METr reference cases and xl-replay where IDs can reach those paths.
6. Refactor only while all phase tests stay green.
7. Update `STATUS.md` with exact command/result before starting the next phase.

Tests must assert both sides of each reference. For example, do not only assert
that an assembly ID is deterministic; assert every component's assembly reference
resolves to the exported assembly record.

## Test ladder

### Layer 1 — allocator unit tests

- namespaces start independently at 1
- explicit claims are preserved
- automatic allocation skips claimed IDs
- duplicate claims in one namespace raise a typed error
- same numeric claim in different namespaces is allowed
- context token resets after success and exception
- nested scope behavior is explicit and tested

### Layer 2 — entity-family tests

For each migrated family:

- direct standalone construction retains current numbering
- scoped construction is deterministic with dirty legacy globals
- all stored integer references resolve in the owning graph
- historical compatibility burns reproduce clean-process IDs

### Layer 3 — public conversion isolation

- same fixture converted twice sequentially with no reset → identical identity
  projection, WUFI XML, and METr JSON
- two distinct fixtures converted in a `ThreadPoolExecutor` → each matches its
  isolated baseline
- multiple concurrent copies of one independently loaded source → all outputs
  match (the mutable Honeybee object itself is not shared)
- a deliberately failing conversion followed by a valid conversion → valid output
  still matches baseline

### Layer 4 — WUFI explicit-ID tests

- high/sparse source IDs survive WUFI → PHX → WUFI
- a new auto object after import skips reserved IDs
- duplicate explicit ID in one namespace fails with namespace/value/source path
- same number in different namespaces remains legal
- references resolve after import and after adding a new object

### Layer 5 — exporter validation

- duplicate component/material/pattern/ventilator IDs in the relevant namespace
  fail before serialization/write
- dangling assembly/window/material/polygon/schedule/ventilator references fail
- WUFI, METr, and PHPP validate only contracts they consume
- PPP remains unchanged and does not acquire an irrelevant validator dependency

### Layer 6 — protected regressions

- WUFI reference cases byte-identical
- METr JSON reference cases structurally/byte identical under current test rules
- WUFI importer suite green
- PHPP focused ventilator/duct tests green
- `tests/test_xl_replay/` final cell state identical
- `tests/test_to_PPP/` green
- full `python -m pytest tests/` green

## Stop conditions

Stop the current phase rather than broadening it if:

- clean-process golden IDs move;
- a namespace rule is unclear from target references;
- an imported explicit ID cannot be preserved without changing a referenced ID;
- direct-constructor behavior changes outside the named family;
- validation rejects an existing committed fixture;
- a proposed cleanup removes a compatibility burn.

Record the evidence in `STATUS.md`, revise `AUDIT.md`/`PRD.md`, then continue only
after the contract is clear.
