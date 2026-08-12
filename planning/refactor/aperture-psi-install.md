# Refactor: Aperture-level Psi-Install — PHX conversion + exporters

**Status:** Planned — design agreed 2026-08-12; not implemented. Blocked on `honeybee_ph`
shipping the data model + resolver (the primary).
**Date:** 2026-08-12
**Author:** Ed May + Claude
**Kind:** Cross-repo refactor, downstream consumer + the export-side heavy lifting.

**Companion docs (same slug in each repo):**
- `honeybee_ph/planning/refactor/aperture-psi-install.md` — **primary**: `PhApertureInstallType`,
  per-edge aperture slots, the resolver, issue #51 mapping
- `honeybee_grasshopper_ph/planning/refactor/aperture-psi-install.md` — components, bug #59
- `ph-navigator-v2/planning/features_v1.1/aperture-psi-install/upstream-alignment.md`

Related prior work: `planning/archive/psi-install-bug-fixes/` (complete — the 2026-08-03
per-edge correctness fixes this design builds on).

---

## 1. Role of this repo

honeybee-ph gains per-aperture, per-edge Ψ-install overrides (named Install Types) so that
window constructions stay minimal in the HBJSON. PHX's job:

1. Carry the **resolved** per-edge values on the aperture element.
2. **PHPP**: write them per Windows-worksheet row — PHPP supports per-instance Ψ-install
   natively; the plumbing already exists.
3. **WUFI/METr**: neither format supports per-instance Ψ-install (`Frame_Psi_*` live only on
   `<WindowType>`; the aperture `<Component>` has no psi field — verified against
   `wufi_file_schema.py`, three reference XMLs, and `docs/reference/wufi-xml-schema.md:639-653`).
   So the exporter synthesizes the **minimal, deterministic** set of window-type variants at
   export time. This is where the unavoidable duplication lives — bounded and invisible upstream.

## 2. Model changes

### 2.1 `PhxApertureElement` — resolved per-edge install psi

`PHX/model/components.py` (`PhxApertureElement`, `:370`): add a small per-edge structure
(working name `PhxPsiInstall`): `top/right/bottom/left` floats (W/mK) plus an optional per-edge
label (the install-type display name, for provenance and variant naming).

- **Always populated** at `from_HBJSON` with the resolver's output — even when no override
  exists (values then equal the window type's). Uniform representation; "overridden?" is
  answered by comparing against `window_type.frame_*.psi_install`.
- One HB aperture → one element (`create_building.py:200-217`), so the element is the natural
  carrier. `PhxConstructionWindow.frame_*.psi_install` keeps its meaning as the type default —
  WUFI needs it there regardless.

### 2.2 `PhxComponentAperture.unique_key` — keep merged components homogeneous

`merge_aperture_components_by_assembly()` (`building.py:258-278`) concatenates elements from
components sharing `unique_key` (`components.py:615-629`). Two apertures with different resolved
psi tuples must **not** merge (a WUFI Component references exactly one `IdentNrWindowType`).
Add a stable digest of the element's resolved psi tuple to `unique_key`. Models without
overrides produce identical digests → merging behavior unchanged.

### 2.3 `from_HBJSON` — use the upstream resolver, don't re-derive

`create_building.py` `create_component_from_hb_aperture()` (`:164-220`): populate §2.1 via
`honeybee_ph_utils.aperture_psi_install.resolve_psi_install_values()`. Resolution logic lives
in exactly one place, upstream.

`create_assemblies.py` is untouched: window types are still built once per HB construction
identifier (`:511-519`) with the construction's own frame data.

## 3. Exporter changes

### 3.1 PHPP — per-row resolved values (small change)

`PHPP/phpp_model/windows_rows.py:93-116` currently writes `psi_i_left/right/bottom/top` from
`phx_construction.frame_*.psi_install`. Change the source to the aperture **element's** resolved
values (thread the element, not just its polygon, through `phpp_app.write_project_window_surfaces()`
`:489-542`). Unit conversion, shape-file columns (AN/AO/AP/AQ in 10.x), and existing tests all
stand. Components-worksheet frame rows (`component_frame.py`) keep writing the **type default**
— unchanged, including the shared-column length-weighted averaging.

Result: per-instance Ψ-install in PHPP with **zero** additional Components entries.

### 3.2 WUFI + METr — window-type variant synthesis (the core new piece)

New shared transform (suggested home: `PHX/model/transforms.py` or similar neutral module),
invoked by both `to_WUFI_XML` and `to_METr_JSON` before serialization:

```
for each aperture component (elements are psi-homogeneous per §2.2):
    tuple = element resolved psi (t, r, b, l)
    if tuple == component.window_type per-edge psi_install:  keep — no variant
    else:  get-or-create variant keyed (window_type.id_num, tuple); repoint component.window_type
```

Variant construction rules:
- Clone of the base `PhxConstructionWindow` with `frame_*.psi_install` replaced by the tuple.
- **Content-keyed, deterministic identifier**: `{base.identifier}__psi-{sha256(tuple)[:8]}`
  with the tuple formatted to fixed precision (the bug-#59 fix pattern, applied at the right
  layer). Two exports of the same model ⇒ byte-identical identifiers.
- Human-readable `display_name`: `{base.display_name} [Ψi 0.10/0.10/0.00/0.10]` (t/r/b/l) —
  QA-legible in the WUFI/METr UI; use the element's install-type labels when present.
- Registered in `project.window_types`; `id_num` assigned by the existing
  `add_new_window_type()` collision handling.
- Cache by key for the run: apertures sharing a tuple share one variant. Minimality:
  M base types + K distinct non-default tuples ⇒ exactly M + K types.

**Variant `u_value_window` — decided 2026-08-12 (Ed): recompute.** The stored U_w includes
install psi (computed at `create_assemblies.py:418` on the ISO standard window), so each
variant recomputes its own standard-window U_w via a small PHX-native helper operating on the
variant's `PhxWindowFrameElement` data (mirroring `honeybee_ph_utils.iso_10077_1`'s
standard-window method). Stored values stay honest regardless of `use_detailed_uw`.

Scope note: the transform mutates `project.window_types` / component references. Each export
pipeline (`hbjson_to_phpp`, WUFI, METr) runs on its own project instance today, so this is
safe — but assert/document it, or operate on a copy, so a future shared-project pipeline can't
silently ship variant types to PHPP.

### 3.3 PPP

`to_PPP/ppp_schemas.py` writes per-window install-situation toggles hardcoded to 1 (`:477-481`)
and a psi average (`:703-707`). Out of scope here; note the per-row columns exist (idx 12-35,
currently empty, `:702`) as a follow-up.

## 4. Bug fixes folded in

- **`from_WUFI_XML` psi fallback**: `phx_schemas.py:262-291` uses `or`-chains, so an explicit
  `Frame_Psi_Right = 0.0` in the XML is treated as missing and inherits the previous edge —
  wrong for exactly the zero-psi edges this feature produces. Replace with `is not None` checks.
- On import, synthesized variants read back as ordinary distinct window types (no un-splitting).
  Lossy but correct; note in docs.

## 5. Implementation phases (this repo)

Branch: `refactor/aperture-psi-install`. One phase at a time; each ends green with a
simplify pass. Dev loop runs against the local `honeybee_ph` checkout (editable install).

| Phase | Scope | Verification | State |
|---|---|---|---|
| 1 | `from_WUFI_XML` psi fallback fix (§4): `is not None` instead of `or`-chains | Explicit-0.0 edge round-trips; existing WUFI import tests green | ☐ |
| 2 | Model: per-edge resolved-psi block on `PhxApertureElement` + tuple digest in `PhxComponentAperture.unique_key` (§2.1-2.2) | Merge-homogeneity tests; unchanged `unique_key` for no-override models | ☐ |
| 3 | `from_HBJSON`: populate resolved values via the upstream resolver (§2.3) | Conversion tests: overrides land on the element; no-override values equal type values | ☐ |
| 4 | PHPP: `WindowRow` reads the element's resolved values (§3.1) | Per-row psi tests updated; Components sheet unchanged | ☐ |
| 5 | WUFI/METr: window-type variant synthesis transform (§3.2), recomputed `u_value_window` | Count invariant (M+K), determinism, no-op invariant vs reference XMLs | ☐ |
| 6 | Closeout: xl-replay aperture-fixture gap (assess feasibility — golden fixture may need a licensed PHPP workbook to record; if so, document and cover with unit tests instead), full suite, docs | Full suite green; status sync | ☐ |

## 6. Tests (the "never again" invariants)

The bug-#59 class of failure: instance data faked with per-instance types, uuid identifiers,
counts growing with instance count. Encode the inverse at this layer:

- [ ] **Count invariant (PHPP)**: N apertures, M base types, any mix of overrides ⇒ exactly M
      Components frame/glazing entries; N Windows rows with per-row resolved psi.
- [ ] **Count invariant (WUFI/METr)**: M base types + K distinct non-default tuples ⇒ exactly
      M + K `<WindowType>` entries; every `IdentNrWindowType` resolves.
- [ ] **No-op invariant**: a model with zero overrides exports **byte-identical** WUFI XML /
      METr JSON / PHPP writes vs. pre-refactor. (Regression gate for every existing project.)
- [ ] **Determinism**: converting the same HBJSON twice yields identical variant identifiers,
      id_nums, and ordering.
- [ ] **Merge homogeneity**: two apertures, same window type, different tuples ⇒ separate
      aperture components; same tuple ⇒ merged as today.
- [ ] Zero-psi edge round-trips WUFI XML (the §4 fallback fix, asserted with explicit 0.0).
- [ ] End-to-end fixture modeled on project 2310: 939 apertures / 79 types / uniform psi ⇒
      79 types in every target.
- [ ] Known gap to close while here: the xl-replay golden fixture (`tests/test_xl_replay/`)
      contains **zero apertures**, so Components/Windows writes are outside the replay gate.
      Add an aperture-bearing fixture with mixed install conditions.
