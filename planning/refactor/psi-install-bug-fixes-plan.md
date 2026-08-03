# Plan — Psi-Install Bug Fixes

```
DATE:    2026-08-03
STATUS:  In progress — Phases 1–4, 6, and 7 complete; Phase 5 blocked on METr order confirmation; Phase 8 implemented pending Ed's live GH verification
AUTHOR:  Ed + Claude
SCOPE:   Fix the bugs catalogued in psi-install-possible-bugs.md §3.6. Bug fixes only —
         the psi-install *feature* work (program-aware defaults, mulled edges, PHN
         install-types) is a separate effort and is NOT in this plan.
RELATED: psi-install-possible-bugs.md (research), tests/test_xl_replay (golden invariant)
```

---

## Verification summary (2026-08-03)

Every item in the research doc's §3.6 bug list was re-checked against source.

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | WUFI-XML import: bottom frame reads `*_Top` fields | **CONFIRMED — real bug** | `from_WUFI_XML/phx_schemas.py:285-290`. `Frame_Width_Bottom` / `Frame_Psi_Bottom` / `Frame_U_Bottom` / `Glazing_Psi_Bottom` all exist in `wufi_file_schema.py:913-916` and are never read. Every WUFI import silently sets bottom = top. |
| 2 | SI/IP localization psi_i bottom↔top column swap | **CONFIRMED — real inconsistency** | `EN_10_6.json` + `EN_10_4A.json` (SI): Components bottom=KB / top=KA, Windows bottom=AQ / top=AP. `EN_10_6IP.json` + `EN_10_4IP.json`: Components bottom=KA / top=KB, Windows bottom=AP / top=AQ. Same PHPP version cannot have different column layouts per unit system — one side is wrong. `EN_10_3.json` (L,R,B,T = JZ,KA,KB,KC sequential) suggests the **IP variants are correct and the SI variants are swapped**, but this must be confirmed against real workbooks (Phase 2). |
| 3 | Windows sheet psi written with no unit conversion | **CONFIRMED — real bug** | `PHPP/phpp_model/windows_rows.py:90-99` builds `XlItem`s with no input/target units while the shape declares `BTU/HR-FT-F` for IP files → raw SI W/m·K values land in IP PHPP. The in-code TODO at `:89` ("Install condition, not Psi-Install") flags a second, unresolved semantic question: PHPP's Windows-sheet per-edge columns may be install-*situation* selectors (0/1), in which case writing a psi value there (e.g. 0.04 instead of 1) would scale install losses to ~4% of intended. Resolve both in Phase 2/3. |
| 4 | psi-install column averaging always unweighted | **CONFIRMED as code fact — no wrong output today** | `phpp_app.py:333-338` only fills `psi_g_*` weight keys; `component_frame.py:179-182` looks up `psi_i_*` → always default 1.0. Currently harmless: in every 10.x shape only left/right share a column (JZ), and left/right edge lengths are always equal (both = height), so unweighted mean == length-weighted mean. Latent bug + misleading dead machinery; fix cheaply in Phase 4. |
| 5 | METr `lrtb*` arrays filled T,R,B,L | **PLAUSIBLE — cannot confirm from available evidence** | `to_METr_JSON/metr_schemas.py:219-242`. Key name implies left,right,top,bottom; code fills top,right,bottom,left. The WUFI-Passive-generated reference files (`tests/reference_files/from_WUFI/metr_json/`, per its CONTEXT.MD) have all four sides identical (0.1 / 0.123 / 0.04) so the true order cannot be inferred from data, and neither plan doc in `plans/20260314/` documents it. Needs METr dev-team confirmation (Phase 5). Harmless today only because all-equal sides are the norm; becomes a live defect the moment per-side psi values diverge (mulled edges). |
| 6 | PPP frame dedup key omits psi values | **CONFIRMED — real bug** | `to_PPP/ppp_schemas.py:663-671` keys on name + per-side width/u_value only; `user_component_sections` (`:746-750`) is first-wins. Two window types sharing a frame product but differing in psi_install / psi_glazing collapse to one PPP frame row carrying the first type's values. Directly conflicts with the planned mulled-edge design (per-cell constructions differing *only* in psi_install). |
| 7 | honeybee_ph `from_dict` requires `psi_install` key | **CONFIRMED as code fact — effectively theoretical** | `honeybee_energy_ph/construction/window.py:58-62` reads five keys with no fallback. But git history shows `psi_install` serialized since the class's first commit (2022-04-22), so no real-world HBJSON lacks it. Low-priority robustness fix. (Same era applies to the `psi_g` → `psi_glazing` naming.) |
| 8 | GH "Set Aperture Psi-Installs" aliasing hazard | **CONFIRMED — real bug** | `win_set_psi_install_values.py`: `ap.duplicate()` does not duplicate the shared `WindowConstruction` (honeybee constructions pass by reference), and `set_ph_frame` (`:99`) assigns `prop_ph.ph_frame` on the **shared construction's** ph properties. Result: mutates every aperture using that construction — including originals not passed through the component — with last-write-wins across branches. The sibling component `win_set_hb_const_psi_install_values.py` duplicates the construction correctly (the fix pattern), but is itself **not registered** in `honeybee_ph_rhino/_component_info_.py` (verified: only "HBPH - Set Aperture Psi-Installs" appears). |

Corrections to the research doc: item 7 has no real-world exposure (key present since 2022); item 4 produces no wrong output with any current localization; item 5 is unproven either way, not confirmed.

---

## Cross-cutting constraints

- **Golden replay invariant** (repo hard rule 4): Phases 2–4 change *what* is written to PHPP cells. The recorded golden state in `tests/test_xl_replay/` will legitimately change — re-record via `scripts/perf/record_replay_fixture.py` as part of each of those phases, and say so in the commit body.
- **Conventional commits**: each phase merges as its own `fix(scope):` commit — these are release-driving.
- **Cross-repo**: Phases 6 and 7 live in `honeybee_ph` and `honeybee_grasshopper_ph`, not PHX. They are planned here for one-place tracking, but ship as PRs in those repos (GH code is Python 2.7 / IronPython — no f-strings, no walrus).
- **Reference-file regeneration**: Phase 1 changes what a WUFI import produces → any `from_WUFI` reference outputs (METr JSON, PHPP writes) that flow from fixtures with differing top/bottom frames must be regenerated. Current fixtures appear to use identical sides, so expect no diff — verify, don't assume.
- Verify before closeout of every phase: `python -m pytest tests/`.

---

## Phase 1 — WUFI-XML import: bottom frame reads Top fields (bug 1)

**Repo: PHX. No external input needed. Do first — smallest, highest confidence.**

**Status: Complete (2026-08-03).** Bottom-frame fields now read the WUFI bottom values while preserving the top-side fallback cascade. An asymmetric four-side regression test verifies width, U-value, psi-glazing, and psi-install routing. Verification: `.venv/bin/python -m pytest tests/test_from_WUFI/test_envelope_types/test_window_types.py -q` (`5 passed`) and `.venv/bin/python -m pytest tests/` (`777 passed, 3 skipped, 1 deselected`). Existing reference fixtures have identical top/bottom data; the reference-output tests passed without regenerated files.

1. `from_WUFI_XML/phx_schemas.py:285-290`: read `_t.Frame_Width_Bottom`, `_t.Frame_U_Bottom`, `_t.Glazing_Psi_Bottom`, `_t.Frame_Psi_Bottom`, keeping the existing cascade fallback (`or frame_data_top[...]`).
2. Test: add/extend a `from_WUFI` fixture whose window type has four *distinct* per-side values (width, u, psi_g, psi_i); assert the parsed `PhxConstructionWindow` carries all four correctly. (Existing fixtures with identical sides could never catch this.)
3. Check downstream reference files for diffs (should be none with current fixtures).

**Verify:** new test fails before the fix, passes after; full suite green.
**Commit:** `fix(from_wufi): read Frame_*_Bottom fields for bottom frame element (was copying Top)`

## Phase 2 — Establish PHPP ground truth: psi_i columns + Windows-sheet semantics (bugs 2, 3-semantic)

**Repo: PHX. Blocked on: real PHPP 10.6 SI, 10.6 IP (and ideally 10.4A/IP) workbooks — Ed to supply/open.**

**Status: Complete (2026-08-03) from the available licensed PHPP 10.6 SI workbook.** `plans/20260714/excel-interop-refactor/test_files/PHPP_EN_V10.6_Empty.xlsx` provides the decisive physical-column ground truth. No IP or 10.4 workbook was found locally, but a unit-system variant cannot reorder the same worksheet; therefore the IP localization files, not SI, are the swapped variants.

| Version / units | Components psi-install columns | Windows edge columns | Windows cell semantics | Evidence |
|---|---|---|---|---|
| PHPP 10.6 SI | sides `JZ`; top `KA`; bottom `KB` | left `AN`; right `AO`; top `AP`; bottom `AQ` | Explicit `W/(mK)` value **or** selector `1/0`; `1` uses Components value, `0` means adjacent window | Direct workbook labels at Components rows 8–13 and Windows rows 20–23 |
| PHPP 10.6 IP | Must use the same physical order: top `KA` / bottom `KB`; top `AP` / bottom `AQ` | Current JSON reverses both top/bottom pairs | Explicit psi values remain valid but require W/mK → Btu/h-ft-F conversion | Inference from the verified unit-invariant 10.6 sheet layout; no local IP workbook found |
| PHPP 10.4A / IP | SI JSON follows the verified 10.6 layout; IP JSON repeats the same reversal | Same | Same code path | Localization comparison; no local 10.4 workbook found |
| PHPP 9.x | Four distinct sequential columns; no mapping change planned | Four distinct columns | Not re-verified from a workbook | No local 9.x workbook found; outside the defective 10.x pair |

This is an evidence-gathering phase; fixes land in Phase 3. For each workbook, record:

1. **Components sheet, frame section**: which physical columns hold psi-install for left/right (shared?), bottom, top. Settles the SI-vs-IP swap direction (working hypothesis from EN_10_3's sequential layout: SI files are the swapped ones).
2. **Windows sheet, per-edge columns** (AN–AQ in 10.x, AA–AD in 9.x): are these install-*situation* selectors (0/1) or psi-value inputs? Resolves the `windows_rows.py:89` TODO. If they are 0/1 selectors, PHX has been writing 0.04-style values into toggle cells — quantify what PHPP does with a non-0/1 value there before deciding the fix.
3. Spot-check one 9.x workbook against `EN_9_6A.json` for the same questions (9.x maps all four psi_i to distinct columns — likely fine, cheap to confirm).

**Deliverable:** a short findings table appended to this file (columns per version/unit-system + Windows-sheet cell semantics). No code changes.

## Phase 3 — PHPP write fixes from Phase 2 findings (bugs 2, 3)

**Repo: PHX. Depends on Phase 2.**

**Status: Complete (2026-08-03).** The PHPP 10.4/10.6 IP localizations now use the workbook-confirmed physical order: Components bottom `KB` / top `KA`, Windows bottom `AQ` / top `AP`. `WindowRow` writes explicit psi-install values with `W/MK` input units and each localization's target units, so IP exports convert to `BTU/HR-FT-F`. Parameterized tests cover all four 10.4/10.6 SI/IP files and verify columns, unit metadata, and converted values. Verification: focused localization/writer/replay suite (`15 passed`), Black/isort/Ruff on changed Python files, and `.venv/bin/python -m pytest tests/` (`788 passed, 3 skipped, 1 deselected`). The recorded replay workbook is PHPP 10.6 SI; its columns and numeric cell values are unchanged, so the replay fixture passed without re-recording. Re-recording an unchanged golden state would violate the golden-fixture invariant.

1. Correct the wrong localization variant(s): align psi_i bottom/top columns (Components + Windows sections) so SI and IP agree with the actual workbooks.
2. `windows_rows.py:90-99`:
   - If the columns are psi inputs: add `"W/MK"` input unit + `self._get_target_unit(...)` target, mirroring the Components-sheet pattern (fixes the IP no-conversion bug).
   - If the columns are 0/1 install-situation selectors: write the selector instead (`0` when that edge's psi_install == 0, else `1`), remove the TODO, and document the semantics in the docstring.
3. Re-record the golden replay fixture only if its intended cell state changes; the current fixture is SI and required no re-record.
4. Tests: unit test on `WindowRow.create_xl_items` asserting column letters and units per localization (parametrize over EN_10_6 / EN_10_6IP at minimum).

**Commit:** `fix(phpp): correct psi-install columns in SI/IP localizations and Windows-sheet write`

## Phase 4 — psi-install averaging weights (bug 4)

**Repo: PHX. Independent; fold into Phase 3's replay re-record if convenient.**

**Status: Complete (2026-08-03), option (a).** `_collect_window_psi_lengths` now supplies both clear-glazing-edge weights for psi-glazing and full opening-edge weights for psi-install. `FrameRow` coverage verifies an unequal weighted left/right collapse while bottom/top pass through unchanged. Focused verification, including `tests/test_xl_replay/test_replay_invariant.py`, passed (`9 passed`); the full suite passed (`780 passed, 3 skipped, 1 deselected`). The golden fixture did not change because current PHPP shapes merge only equal-length left/right install edges, so re-recording would violate the no-output-change invariant.

Pick one (recommend a): 

a. **Wire it properly**: extend `_collect_window_psi_g_lengths` → `_collect_window_psi_lengths` to also accumulate `psi_i_*` keys weighted by full side lengths (left/right = element height, bottom/top = element width, per ISO 10077-1 install perimeter). Numerically a no-op for today's shapes; makes the machinery honest and future-proofs any shape that merges more psi_i columns.
b. **Delete the pretense**: stop passing weights for psi_i and add a comment stating why unweighted is exact for L/R-sharing shapes.

Test: `FrameRow._build_averaged_psi_items` with unequal psi_i L/R and a shared-column shape — assert the averaged value; assert bottom/top pass through unaveraged.

**Commit:** `fix(phpp): weight psi-install column averaging by install edge length` (or `refactor(phpp): ...` for option b — note the release implication).

## Phase 5 — METr lrtb array order (bug 5)

**Repo: PHX. Blocked on: METr dev-team confirmation (piggyback on the existing sel=2 foundation thread).**

1. Ask the METr/WUFI dev team: what is the element order of `lrtbFrW` / `lrtbFrU` / `lrtbGlPsi` / `lrtbFrPsi`? (Or obtain any METr export with asymmetric frames — one such file settles it.)
2. If L,R,T,B (key-name order): reorder the four arrays in `metr_schemas.py:219-242` and regenerate the three `to_METr` reference JSONs (values identical today, so expect no diff — the fix is protective).
3. Add a comment on the block citing the confirmed order + source, so the next reader doesn't have to re-litigate.
4. Add a test fixture with asymmetric frame sides asserting array position ↔ side mapping.

**Commit:** `fix(metr): write lrtb frame arrays in confirmed left,right,top,bottom order`

## Phase 6 — PPP frame dedup key (bug 6)

**Repo: PHX. Independent — can run any time.**

**Status: Complete (2026-08-03).** The frame dedup key now includes per-side psi-install and psi-glazing. Parametrized regression coverage proves that constructions differing only in either psi field produce distinct PPP frame rows and distinct `Fenster_Rahmen` references. Verification: `.venv/bin/python -m pytest tests/test_to_PPP/test_ppp_schemas.py -q` (`6 passed`) and `.venv/bin/python -m pytest tests/` (`779 passed, 3 skipped, 1 deselected`). Black, isort, diff-check, and changed-code Ruff checks passed; full-file Ruff retains five unrelated warnings already present on `HEAD` (`F841` at line 505 and `B007` at lines 732, 755, and 768).

1. `to_PPP/ppp_schemas.py:663-671`: extend `_frame_dedup_key` with per-side `psi_install` and `psi_glazing`.
2. Review `_glazing_dedup_key` while there — it already covers name/g/u; fine as-is.
3. Test: two `PhxConstructionWindow`s, same frame name/widths/u-values, different `psi_install` on one edge → two PPP frame rows, and each window row references its own frame.

**Commit:** `fix(ppp): include psi-install and psi-glazing in frame dedup key`

## Phase 7 — honeybee_ph from_dict robustness (bug 7)

**Repo: honeybee_ph (cross-repo, low priority — batch with the next honeybee_ph release).**

**Status: Complete (2026-08-03).** `PhWindowFrameElement.from_dict()` now falls back to the initialized class defaults for all five legacy frame fields, and `AperturePhProperties.from_dict()` now uses the canonical 4-inch (`0.1016 m`) install-depth default. Verification: focused tests (`10 passed`), full suite (`763 passed`), and Black passed. Repository-wide coverage remains at the pre-existing 76% against a configured 100% target; Ed accepted that baseline for this phase. Commit: `honeybee_ph` `62d72fb`.

1. `honeybee_energy_ph/construction/window.py:58-62`: switch `width` / `u_factor` / `psi_glazing` / `psi_install` / `chi_value` to `.get(key, <class default>)`, matching the `solar_absorptance` / `thermal_emissivity` pattern. Defaults: 0.1 / 1.0 / 0.04 / 0.04 / 0.0.
2. While there: fix the `install_depth` from_dict fallback inconsistency (0.1 vs 0.1016 at `honeybee_ph/properties/aperture.py:141`) noted in the research doc §2.
3. Test: `from_dict` on a dict missing `psi_install` → object with default, no raise.

**Commit (honeybee_ph):** `fix(construction): tolerate missing frame-element keys in from_dict`

## Phase 8 — GH aliasing fix + component registration (bug 8)

**Repo: honeybee_grasshopper_ph (cross-repo). Python 2.7 / IronPython constraints apply.**

**Status: Implemented (2026-08-03), live GH verification assigned to Ed.** The aperture worker now duplicates and uniquely identifies regular constructions; shaded constructions also receive an independent nested `WindowConstruction` because Honeybee's wrapper duplicate retains the original inner construction. The existing HB-construction component is registered. Black, Ruff, syntax/registry smoke, and CPython object-ownership smokes passed for regular and shaded constructions, including two outputs with distinct psi values and an unchanged original. Ed will run the plan's live two-aperture Grasshopper check. No component I/O changed; `.ghuser` regeneration is not required. Commit: `honeybee_grasshopper_ph` `b2c322b`.

1. `win_set_psi_install_values.py`: before `set_ph_frame`, duplicate the construction and assign the duplicate onto `dup_ap` — copy the working pattern from `win_set_hb_const_psi_install_values.py`. Handle both `WindowConstruction` and `WindowConstructionShade` branches (the shade case must duplicate the shade wrapper *and* its inner `window_construction`). Give the duplicated construction a distinct identifier (e.g. suffix from the aperture id) so two apertures with different psi sets no longer share one construction downstream.
2. Register `HBPH - Set HB-Construction Psi-Installs` in `honeybee_ph_rhino/_component_info_.py` (verified missing).
3. Manual GH verification (no CI for IronPython): two apertures sharing one construction, different psi branches → confirm the un-passed original and each output aperture carry independent values; note results in the PR.

**Commit (honeybee_grasshopper_ph):** `fix(gh): stop mutating shared window construction in Set Aperture Psi-Installs`

---

## Sequencing

```
Phase 1 (WUFI bottom-frame)        → immediate, no dependencies
Phase 6 (PPP dedup)                → immediate, no dependencies
Phase 4 (psi_i weights)            → immediate; replay re-record shared with Phase 3
Phase 2 (PHPP ground truth)        → needs Ed + workbooks
Phase 3 (PHPP fixes)               → after Phase 2
Phase 5 (METr order)               → needs dev-team reply; code change is 5 min after
Phase 7 (honeybee_ph from_dict)    → any time, batch with next hb-ph release
Phase 8 (GH aliasing)              → any time; manual Rhino verification session
```

Phases 1, 4, and 6 are pure-PHX, test-verifiable, and can ship as three small PRs this week. Phases 2/3 and 5 are gated on external evidence (workbooks, dev team). Phases 7/8 ride the other repos' release cadence.
