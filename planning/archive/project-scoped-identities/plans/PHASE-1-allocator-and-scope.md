# Phase 1 — Allocator and conversion-scope primitive

**Status:** Complete · 2026-08-14

## Goal

Introduce an isolated, exception-safe identity mechanism without migrating model
entities yet.

## Production touch points

- new `PHX/model/identity.py`
- `PHX/model/__init__.py` only if the API is intentionally public
- no counter-bearing entity changes in this phase

## Red tests

Add `tests/test_model/test_identity_allocator.py` covering:

- independent namespaces;
- claim/reserve and skip behavior;
- duplicate claim error with namespace and value;
- legal same-number claims across namespaces;
- context enter/exit and token restoration;
- exception cleanup;
- nested scopes (fresh child vs explicit reuse);
- dirty legacy globals do not affect allocator values.

## Green implementation

Implement a fully typed `IdentityAllocator`, namespace key type, and typed errors.
Use `contextvars.ContextVar`, not a module-global current allocator. Provide:

- a context manager that always resets its token in `finally`;
- `allocate_identity(namespace, legacy_counter_owner)` compatibility helper;
- explicit claim API for Phase 5;
- deterministic diagnostic snapshots for tests, not model serialization.

Do not add locks. Each allocator is owned by one conversion/project; concurrent
mutation of one project is outside the contract.

## Guardrails

- no global counter resets;
- no dependency on `tests/conftest.py`;
- no UUID-to-integer hashing;
- no implicit process singleton allocator;
- no change to direct constructor numbering yet.

## Verification

Run allocator unit tests, existing model ID unit tests, WUFI/METr reference tests,
and xl-replay. All existing outputs must remain unchanged.

## Definition of done

The primitive is isolated and exception-safe; no production entity uses it yet;
all pre-existing tests remain green.

## Commit

`feat(identity): add project identity allocator and scoped context`
