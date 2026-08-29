# PLAN — export-time identity scope

Read [`README.md`](README.md) first. This is the sequencing. Red-green-refactor,
one phase at a time. Phases 1–3 ship **together** as one PR; shipping Phase 1 alone
converts a loud failure into a silently wrong certification model (README §7).

**Verification gate for every phase:** `python -m pytest tests/` (baseline: 1032
passed, 3 skipped) and `black --check` (CI enforces it since `a28f9f3` — the pinned
version; do not let a `uv.lock` bump ride along).

---

## Decision — SETTLED 2026-08-25 (Ed): option (i), no-op

`PhxProject.identity_scope()` (`project.py:457-466`) lazily creates an empty
allocator when the project has none. That lazy-create is the root of hazards A1 and
A2 (README §8). It must stop. Two shapes:

| | Behaviour when `_identity_allocator is None` | Caller impact |
|---|---|---|
| **(i) no-op** ✅ **CHOSEN** | yield without activating a scope; construction falls through to the legacy counters | `_bug_fixes.py` calls `identity_scope()` unconditionally; both project kinds correct; no guard anywhere |
| (ii) raise | `IdentityAllocationError` | every caller needs a guard, and the guard needs a public "was this allocator-built?" predicate |

**(i) is recommended.** It makes the API mean *"join this project's identity
regime, whatever that regime is"* — which for a hand-assembled project genuinely is
the legacy counters, and is correct and unique there (README §3.3). It removes the
guard from every call site rather than making every call site remember one.

Both public conversion paths attach an allocator
(`from_HBJSON/create_project.py:112`, `from_WUFI_XML/phx_converter.py:20`), so
"no allocator" reliably means "hand-assembled", never "built by PHX".

Signature becomes `Iterator[IdentityAllocator | None]`. Both existing callers
(`test_project_identity_isolation.py:121`,
`test_explicit_identity_claims.py:27`) use it as a bare statement and never bind
the yielded value, so nothing breaks.

---

## Phase 0 — red tests ✅ DONE

No production code. Every test below must **fail** for the stated reason before
proceeding.

1. **Allocator-built project, ≥200 kW, validates after the split.**
   Convert a fixture through `convert_hb_model_to_PhxProject`, force a cooling
   device over 200 kW, run `split_cooling_into_multiple_systems`, then
   `validate_project_export_readiness(..., WUFI)`.
   *Red:* `IdentityValidationError`, duplicates in `variant.mechanical.systems` and
   `variant.mechanical.devices.PhxHeatPumpAnnual`.

2. **Hand-assembled project, ≥200 kW, validates after the split.**
   Bare `PhxProject()` / `PhxVariant()`, as `test_cooling_capacity_fix.py` builds
   them. *Red only against the naive fix* — green on today's `HEAD`. This is the
   regression guard for hazard A1 and it is the test the suite has never had.

3. **`identity_scope()` does not attach an allocator to a hand-assembled project.**
   `with p.identity_scope(owner=1): pass` then assert
   `p._identity_allocator is None`. *Red:* it is not None. Guards hazard A2.

4. **Capacity conservation.** Parametrised over 1/2/3/4 pre-existing cooling
   devices: total installed recirculation capacity and total airflow are unchanged
   by the split; every resulting device is ≤200 kW; `cooling_percent` sums to 1.0.
   *Red* for ≥2 devices (1.5×, 2.0× — README §7.1).

5. **Zone coverage.** After a split, the per-collection `zone_coverage.cooling`
   values sum to 1.0 and every `zone_num` resolves to a real zone.
   *Red:* sums to 9.0 (README §7.2). **Blocked** — see Phase 3.

Also update the existing `test_cooling_capacity_fix.py` tests to call the validator,
so this class of defect can never again pass silently.

## Phase 1 — restore the identity contract ✅ DONE

**Files:** `PHX/model/project.py`, `PHX/to_WUFI_XML/_bug_fixes.py`

1. `project.py:459-460` — remove the lazy-create per the decision above.
2. `_bug_fixes.py` — wrap the new-collection loop:

   ```python
   with _phx_project.identity_scope(owner=phx_variant.id_num):
       for i in range(number_of_new_cooling_systems):
           ...
   ```

   **Placement is load-bearing:** inside the per-variant loop, after the
   `< 200.0` `continue`. Around the whole function it would attach an allocator to
   every project the CLI touches.

Greens Phase 0 tests 1–3. Verified outcome on Arverne D: collections `1…9`, new
devices `3…10`, validation PASS.

**Commit:** `fix(identity): allocate export-time cooling systems in the project scope`

## Phase 2 — capacity conservation ✅ DONE

**File:** `PHX/to_WUFI_XML/_bug_fixes.py:53-54`

Divide by `target_number_of_cooling_devices` (already computed at `:52`, already
used correctly for the coverage percentage at `:55`) instead of
`target_number_of_cooling_systems`. Apply to both capacity and airflow.

`target_number_of_cooling_systems` then has no remaining reader — delete it rather
than leaving a misleading name.

⚠️ `test_cooling_capacity_fix_300KW_with_2_mech_systems` currently **asserts the
inflated value as correct** and will defend the bug. It must be corrected in this
phase, with a comment recording that the old expectation was wrong and why.

Arverne D's numbers are unchanged by this phase (one cooling device → both divisors
agree). Greens Phase 0 test 4.

**Commit:** `fix(wufi): conserve total cooling capacity when splitting systems`

## Verification evidence (Phases 0-2, 2026-08-25)

Branch `bug-fix/export-time-identity-scope`.

```
python -m pytest tests/    ->  1052 passed, 3 skipped, 1 deselected
python -m black  --check . ->  clean (434 files)
python -m isort  --check . ->  clean
```

End-to-end on the reported model
(`2242 Arverne D/13_HBJSON/Arverne_D_260825.hbjson`), which previously raised
`IdentityValidationError`:

```
cooling capacity  before = 1628.5 kW   after = 1628.5 kW
mech collection ids       = 1 ... 9        (were 1,1,2,3,4,5,6,7,8)
new heat-pump ids         = 3 ... 10       (were 1 ... 8)
max device capacity       = 180.94 kW      (under the WUFI 200 kW limit)
XML written OK            = 3,223,082 chars
sum(MaxRecirculationAirCoolingPower) = 1628.5 kW
```

Residual risk carried forward: `zone_coverage.cooling` is still `1.0` on all nine
collections (Phase 3). The export succeeds and the identity graph is valid; whether
that 900% figure is a modelling error depends on the open WUFI question below.

## Phase 3 — zone coverage *(BLOCKED — needs a WUFI-semantics answer)*

**Open question:** does WUFI-Passive honour system-level `ZoneCoverage`
(`xml_schemas.py:1615-1623`), device-level `usage_profile.cooling_percent`, or
both? If `ZoneCoverage` is load-bearing, nine systems each at `CoverageCooling=1.0`
is a modelling error. If the device percent dominates, it is cosmetic.

### Evidence gathered 2026-08-25 — the premise is wrong, the question is narrower

Read the two real-project files in `tests/reference_files/from_WUFI/wufi_xml/`
(the index calls this folder "real WUFI XML parsed back in"):

| file | systems | `CoverageCooling` per system (zone 1) | sum |
|---|---|---|---|
| `_la_mora.xml` | 3 — `System`, **`Cooling overflow`**, **`Cooling overflow 2`** | 1.0, 1.0, 1.0 | **3.0** |
| `_ridgeway.xml` | 2 — `Ideal Air System`, `Extra Cooling System` | 1.0, 0.5 | **1.5** |

Two things follow:

1. **"Coverage must sum to 1.0" is not a WUFI invariant.** Neither real file
   obeys it. Phase 0 test 5 was written against a premise the data contradicts;
   do not implement it as drafted.
2. **A human split cooling into overflow systems for exactly this reason and left
   `CoverageCooling` at 1.0 on each.** `git log -S "Cooling overflow"` over `PHX/`
   returns nothing, so those names were never generated by PHX — they were typed
   into the WUFI-Passive UI. PHX's current output (all `1.0`) matches the
   convention the modeller used for the same 200 kW overflow pattern.

Caveat on provenance: the devices inside those two overflow systems are named
`unnamed_annual_heat_pump`, which is PHX's *importer* fallback for an empty
`Name` (`from_WUFI_XML/phx_schemas.py:1771`) and appears nowhere in the exporter.
So the file has been through PHX at least once after the human named the systems.
That weakens the evidence from "authored by WUFI" to "written by a human in the
WUFI UI, and round-tripped without WUFI normalising the three 1.0 values away".

**Still blocked, but on a smaller question:** is `CoverageCooling` a per-system
share of the zone load (in which case 9 × 1.0 over-serves) or a per-system
enable/limit that WUFI reconciles against device capacity and
`cooling_percent`? The reference files show the field is meaningful and adjustable
(ridgeway's 0.5) but not normalised, which is consistent with either reading.

**How to unblock — needs Ed, not another file read.** Build a two-system cooling
model in WUFI-Passive, set the coverages, and compare the reported cooling demand
against the single-system equivalent. That requires the Windows application, so it
is not something this branch can settle. If it turns out to matter: set each new
collection's `zone_coverage.cooling = 1 / target_number_of_cooling_devices` and
copy `zone_num` from the collection whose device was split rather than inheriting
the default `1` — which also closes the latent dangling-reference case (README
§7.2) for WUFI-imported projects with sparse zone `IdentNr`.

If it turns out to be cosmetic, record the finding in the ticket and drop the phase.

**Commit:** `fix(wufi): split zone cooling coverage across the new systems`

## Phase 4 — close out ◻ PENDING (blocked behind Phase 3)

1. Re-run the Arverne D model end to end through
   `hbjson_to_wufi_xml.py` and confirm a WUFI file is produced. Open it in
   WUFI-Passive and confirm the nine cooling systems load and the total installed
   cooling capacity reads 1 628.5 kW.
2. `docs/dev/exporter-patterns.md` → *Identity lifecycle and export gates*: state
   that `identity_scope()` is a no-op on projects that were not allocator-built,
   and restate the PRD's "concurrent mutation of one project is not supported"
   next to the API rather than only in the archived PRD (README §8.7).
3. Fold the outcome into `context/` per `planning/.instructions.md`, move this
   folder to `archive/`, add the row to `archive/README.md`.

---

## Explicitly NOT in this PR

Each is real and evidenced in README §9; each needs its own ticket. Bundling any of
them makes the regression fix unshippable.

| # | Item | Severity | Why separate |
|---|---|---|---|
| 1 | **[`space-merge-mutates-source-graph`](../space-merge-mutates-source-graph/README.md)** — `PhxSpace.__add__` mutates the graph during serialization — two exports of one project inflate ventilation flow 53.24 → 106.48 → 159.72 | **Severe, shipping now** | Independent defect, different subsystem, different fix. Reachable from the POC service and any notebook; not from the one-shot CLI. **Filed 2026-08-25.** |
| 2 | Both exporters validate-then-mutate; `synthesize_window_type_psi_variants` runs outside its own gate and issues an unclaimed window ID (README §4, §8.3) | High | Touches both `xml_builder` and `metr_builder` ordering plus `add_new_window_type`. Becomes urgent *because* this fix makes `identity_scope()` the sanctioned mutation path. |
| 3 | Five devices share `IdentNr=1` in one WUFI `<System>` (README §8.4) | Unknown — needs WUFI verification | PR #86 declared this legal on purpose (PRD item 7). Re-opening that premise is an investigation, not a fix. |
| 4 | Option B / Option E — the transform is missing on the facade path and present where PHPP can see it (README §8.1, §8.8, Option E) | Medium | Requires making the transform idempotent (it is not: 1× → 630 kW, 2× → 1378 kW, 3× → 2756 kW) and deleting the CLI call in the same commit. |
| 5 | Re-arm the WUFI reference-bytes comparison — `test_xml_output.py:25` is `assert True` (README §6) | Medium | Its own golden-file churn. It is the only net that would have caught items 1 and 2, so it should follow closely. |
| 6 | `IdentNrPH_Building` hard-coded to `1` (§8.5); METr global material namespace vs per-assembly validation (§8.6); `build_project_with_identities` does not enforce an owner scope (§8.9) | Low–medium | Latent; no current path reaches them. |

## Risk register for what *is* shipping

| Risk | Assessment |
|---|---|
| Changes exported `IdentNr` for models that export successfully today | **Real but intended.** Only ≥200 kW models in a long-lived process, whose IDs are currently a function of export count (README §5). Post-fix they are deterministic. If any such XML is already with a certifier, the diff is explainable and toward correctness. |
| Changes protected golden output | **No.** Verified: for a <200 kW project the transform `continue`s before the new `with`, and the emitted XML is byte-identical (md5) with and without the fix. METr/PPP/PHPP never call `_bug_fixes`; `tests/test_xl_replay/` is untouched. |
| Breaks hand-assembled projects | **Guarded by Phase 0 test 2 and Phase 1's no-op decision.** This is the failure mode of the naive fix and is the reason the lazy-create must go. |
| Phase 2 changes numbers in a shipped model | Only for variants with ≥2 cooling devices — which cannot export today at all (they hard-fail at the gate). No existing successful export changes. |
| CI formatting | The earlier scratch implementation used a 2-space indent that `black --check` rejects. Run `black` before pushing. |
