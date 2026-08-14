# STATUS — honeybee-conversion-facade

**Status:** Requested · 2026-08-14

- The conversion capability already exists in
  `PHX.from_HBJSON.create_project.convert_hb_model_to_PhxProject()` and already
  accepts a live Honeybee `Model`.
- Remaining scope: add the thin `PHX.conversion.from_honeybee()` public facade,
  give the four existing options public names, improve boundary errors, add
  legacy-equivalence tests, and correct the public docs/examples.
- Explicitly out of scope: converter changes, model changes, implementation-
  module moves, and a PHX-level single-variant convenience function.
- OpenPH remains responsible for validating and selecting one `PhxVariant`
  from the returned `PhxProject`.
- **Next step:** add facade/equivalence tests, implement the delegating facade,
  then update PHX and OpenPH documentation.
- Blockers: none.
