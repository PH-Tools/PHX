# STATUS — honeybee-conversion-facade

**Status:** In progress · 2026-08-14

- The conversion capability already exists in
  `PHX.from_HBJSON.create_project.convert_hb_model_to_PhxProject()` and already
  accepts a live Honeybee `Model`.
- Implemented: thin `PHX.conversion.from_honeybee()` public facade, four public
  option names, model/room boundary diagnostics, legacy-equivalence tests, PHX
  public documentation, and the coordinated OpenPH examples.
- Explicitly out of scope: converter changes, model changes, implementation-
  module moves, and a PHX-level single-variant convenience function.
- OpenPH remains responsible for validating and selecting one `PhxVariant`
  from the returned `PhxProject`.
- **Next step:** run the full formatting, lint, and `python -m pytest tests/`
  verification gate; then mark complete and archive the packet.
- Blockers: none.
