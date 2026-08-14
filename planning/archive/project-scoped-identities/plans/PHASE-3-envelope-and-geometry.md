# Phase 3 — Envelope and geometry identities

**Status:** Complete · 2026-08-14

## Goal

Migrate component, polygon, and vertex allocation while preserving every exported
reference and current clean-process gaps.

## Entity families

- `PhxComponentBase` and all subclasses
- `PhxVertix`, `PhxVertix2D`, `PhxPolygon`
- component → construction/window/shade references
- component → polygon, polygon → vertex, and parent → child polygon references
- PHPP aperture polygon → host polygon lookup

## Red tests

- dirty legacy globals do not change a scoped envelope identity projection;
- all component polygon IDs resolve;
- all polygon vertex and child polygon IDs resolve;
- opaque assembly and aperture window/shade refs resolve;
- mixed opaque/aperture construction preserves one component sequence;
- constructing aperture elements, shading dimensions, and thermal bridges preserves
  the clean baseline's later exported component IDs;
- 2D geometry preserves the clean baseline's current 3D-vertex burn;
- PHPP host lookup still finds the correct opaque polygon.

## Green implementation

- Route the shared component sequence through one compatibility namespace.
- Route polygons and vertices through distinct geometry namespaces.
- Represent the `PhxVertix2D` behavior explicitly; do not “fix” it by silently
  closing golden gaps.
- Keep integer refs derived from assigned PHX objects.
- Ensure merge (`__add__`), weld, and transform-created objects remain inside the
  active project scope.
- Do not renumber at export time.

## Guardrails

- no geometry ordering change;
- no set/dict sorting change disguised as identity work;
- no component class hierarchy refactor;
- no deletion of unused component-subclass IDs.

## Verification

- model component/geometry suites
- HBJSON building/geometry/cleanup tests
- WUFI component/geometry exporter tests
- METr schema/reference tests
- PHPP window/area tests and xl-replay

## Definition of done

The complete envelope graph is deterministic in a scoped conversion, every
integer ref resolves, and WUFI/METr/PHPP protected output is unchanged.

## Commit

`feat(identity): scope envelope and geometry identities`
