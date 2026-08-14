# STATUS — honeybee-conversion-facade

**Status:** Requested · 2026-08-14

- Existing implementation:
  `PHX.from_HBJSON.create_project.convert_hb_model_to_PhxProject()`.
- The implementation already accepts a live Honeybee `Model`; the gap is
  public discoverability, naming, documentation, and a stable compatibility
  surface.
- **Next step:** choose the canonical public import, write legacy-equivalence
  tests, then add an additive facade and update docs/examples.
- Blockers: none.
- Coordinate the downstream handoff with OpenPH's
  `planning/features/phx-conversion-facade/` packet.

