# Phase 7 — Transition cleanup, docs, and closeout

## Goal

Remove conversion-path dependence on the manual reset harness, reconcile public
documentation, and close the feature with full evidence.

## Red/documentation checks

- Temporarily remove the reset fixture from public HBJSON/WUFI reference cases;
  those cases must remain deterministic.
- Run reference cases in varied order and repeated in one process.
- Search production public conversion paths for direct `_count` reads/writes.
- Search docs for stale “every model class” and module-reload guidance.

## Cleanup

- Keep `reset_class_counters` only for direct standalone legacy-constructor tests
  that explicitly test fallback numbering.
- Delete duplicate/anomalous reset lines and document the remaining scope.
- Do not delete compatibility counters/burns that preserve output.
- Add deprecation comments only where they identify a concrete follow-up.
- Update:
  - `docs/reference/phx-model-reference.md`
  - `docs/dev/architecture.md`
  - `docs/dev/exporter-patterns.md`
  - `context/CODING_STANDARDS.md`
  - docstrings/nav if the allocator or project mutation scope is public
- State the independent-project concurrency guarantee and same-project exclusion.

## Full verification

Run and record:

1. allocator/entity/validation focused suites;
2. repeated sequential and parallel isolation tests;
3. `tests/test_from_HBJSON/`;
4. `tests/test_from_WUFI/`;
5. `tests/test_to_WUFI_xml/`;
6. `tests/test_to_METr_JSON/`;
7. `tests/test_PHPP/` and `tests/test_xl_replay/`;
8. `tests/test_to_PPP/`;
9. `python -m pytest tests/`.

Review `git diff -- tests/reference_files` separately. Expected result: empty.

## Closeout

- Update `../STATUS.md` phase table with exact counts/results.
- Fold final architecture into canonical docs.
- Mark the packet `Complete`, move it unchanged to `planning/archive/`, and add
  the archive index row only after all acceptance criteria pass.
- Use a `feat(identity): ...` conventional commit for release semantics.

## Definition of done

Public conversions require no counter reset, all protected outputs and xl-replay
are unchanged, documentation matches runtime behavior, and no unclassified direct
`_count` dependency remains on a public conversion/export path.

## Final commit

`docs(identity): document project-scoped conversion identities`
