# STATUS — honeybee-conversion-facade

**Status:** Complete · 2026-08-14

## Outcome

- Added the thin `PHX.conversion.from_honeybee()` public facade with four public
  option names and no duplicated conversion logic.
- Added wrong-type and model/room honeybee-ph extension diagnostics.
- Preserved the legacy converter and all file-oriented CLIs unchanged.
- Updated PHX architecture, importer/exporter, package, API-navigation, and
  model-reference documentation.
- Updated OpenPH examples while keeping single-variant selection downstream.

## Verification

- PHX implementation commit: `0705767`
- OpenPH documentation commit: `99b675d`
- Black, isort, and Ruff: pass
- `python -m pytest tests/`: `887 passed, 3 skipped, 1 deselected`
- OpenPH `src/openph/conversion.py` Ruff format/lint: pass

## Residual risk / rollout

- No deferred implementation work or known behavioral risk within scope.
- Merge and release PHX before merging the OpenPH documentation branch so its
  published example never precedes availability of `PHX.conversion`.
