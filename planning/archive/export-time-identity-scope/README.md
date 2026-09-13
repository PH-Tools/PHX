# WUFI export fails identity validation on any project with ≥200 kW cooling

**Issue:** [#106](https://github.com/PH-Tools/PHX/issues/106)

**Status:** Phases 0-2 **merged to main** (PR #96, 2026-08-25); Phase 3 (zone coverage) **resolved, no change** (2026-09-13: WUFI validates device `CoverageWithinSystem` sums, which PHX's split satisfies; [#126](https://github.com/PH-Tools/PHX/issues/126) closed); Phase 4 **complete** (2026-09-13: production model loads and calculates in WUFI-Passive; docs note added). Archived. See [`PLAN.md`](PLAN.md).
**Opened:** 2026-08-25
**Kind:** Regression (identity allocation), introduced by [PR #86](https://github.com/PH-Tools/PHX/pull/86), released in **v1.56.82**
**Owner files:** `PHX/to_WUFI_XML/_bug_fixes.py`, `PHX/model/project.py`
**Predecessor:** [`archive/project-scoped-identities/`](../../archive/project-scoped-identities/README.md)

---

## TL;DR

`split_cooling_into_multiple_systems()` builds new PHX model objects **after** the
conversion has returned, i.e. outside the project's identity scope. PR #86 made
identity allocation project-scoped, which leaves the legacy class counters sitting
at `0`; the post-conversion objects therefore restart numbering at `1` and collide
with IDs the project already handed out. The export validator (also from #86)
catches it and refuses the export.

The mutation site is the defect. PR #86 even **documented** the required call
(`with phx_project.identity_scope(owner=variant.id_num):`) — it just never applied
it to the one pre-existing caller.

**The fix cannot ship alone.** Removing the hard-fail un-masks two pre-existing
defects in the same function that currently cannot be reached: installed cooling
capacity is inflated 1.5–2× whenever a variant has ≥2 cooling devices (§7), and
every new collection claims 100% of zone 1's cooling (§7). Shipping the ID fix by
itself converts a loud refusal into a silently oversized cooling plant in a Phius
certification model.

---

## 1. Reported symptom

Grasshopper, `HBJSON → WUFI-XML`, model
`2242 Arverne D/13_HBJSON/Arverne_D_260825.hbjson`:

```
PHX.model.identity_validation.IdentityValidationError: wufi identity validation failed with 3 issue(s):
- duplicate: variants[0].mechanical_systems[1].devices[0] -> ('variants[0]', 'variant.mechanical.devices.PhxHeatPumpAnnual') ID 1 (also used by variants[0].mechanical_systems[0].devices[26])
- duplicate: variants[0].mechanical_systems[2].devices[0] -> ('variants[0]', 'variant.mechanical.devices.PhxHeatPumpAnnual') ID 2 (also used by variants[0].mechanical_systems[0].devices[1])
- duplicate: variants[0].mechanical_systems[1] -> ('variants[0]', 'variant.mechanical.systems') ID 1 (also used by variants[0].mechanical_systems[0])
```

The same model converted cleanly before ~2026-07-22.

## 2. Reproduction

Reproduced at repo `HEAD` (v1.56.91) with a **byte-identical** error message —
same three issues, same paths, same IDs. Independently re-reproduced by a second
reviewer running against the committed git blob rather than the working tree.

```python
p = create_project.convert_hb_model_to_PhxProject(
    hb_model, _group_components=True, _merge_faces=True,
    _merge_spaces_by_erv=True, _merge_exhaust_vent_devices=True)

validate_project_export_readiness(p, IdentityValidationTarget.WUFI)   # PASSES
p = _bug_fixes.split_cooling_into_multiple_systems(p)                 # <-- mutation
xml_builder.generate_WUFI_XML_from_object(p)                          # RAISES
```

Key observation: **the conversion output itself is clean.** Validation passes
immediately after `convert_hb_model_to_PhxProject()` and fails only after the
export-time bug-fix transform runs. Nothing in `from_HBJSON/` is at fault.

Model facts:

| | |
|---|---|
| variants | 1 |
| zones | 1 (`id_num` 1) |
| mech collections after conversion | 1 (`id_num` 1, 27 devices) |
| cooling devices | 1 — `WSHP [Heating & Cooling]`, `PhxHeatPumpAnnual` `id_num` 1 |
| total recirc cooling capacity | **1 628.5 kW** |
| `PhxHeatPumpAnnual` IDs in use | {1 (`WSHP`), 2 (`DHW-HP-1-2-3`)} |

### Why exactly three issues, not sixteen

1 628.5 kW / 200 → `number_of_new_cooling_systems = 8`. The transform appends
**eight** new collections, each holding one new `PhxHeatPumpAnnual`. Both the new
collections and the new heat-pumps are numbered `1…8`.

The validator reports only the *overlap* with what already exists:

| namespace | pre-existing IDs | new IDs | duplicates reported |
|---|---|---|---|
| `('variants[0]', 'variant.mechanical.systems')` | {1} | 1…8 | **1** |
| `('variants[0]', 'variant.mechanical.devices.PhxHeatPumpAnnual')` | {1, 2} | 1…8 | **2** |

Three issues. This matters for triage: **the issue count tells you the size of the
collision, not the size of the mutation.**

## 3. Root cause

### 3.1 The mechanism

`PHX/to_WUFI_XML/_bug_fixes.py:81,86` constructs model objects at export time:

```python
new_collection = PhxMechanicalSystemCollection()          # line 81
new_cooling_heat_pump = PhxHeatPumpAnnual()               # line 86
```

Both run `allocate_identity()` in `__post_init__`
(`collection.py:535`, `hvac/_base.py:211`). That helper has two modes
(`PHX/model/identity.py:174`):

```python
allocator = current_identity_allocator()
if allocator is not None:
    return allocator.next_id(_owned_namespace(namespace))   # project-scoped
legacy_counter_owner._count += 1                            # legacy fallback
return legacy_counter_owner._count
```

The allocator lives in a `ContextVar` activated by
`build_project_with_identities()` and released in that function's `finally`.
`split_cooling_into_multiple_systems()` is called from `hbjson_to_wufi_xml.py:265`,
**after** `convert_hb_model_to_PhxProject()` has returned, so the ContextVar is
empty and the legacy branch runs.

### 3.2 Why the legacy branch is now poisoned

The compatibility shim is deliberately non-mutating inside a scope: *"Inside a
project scope it delegates to the allocator and **does not mutate** the legacy
`ClassVar`"* (`archive/project-scoped-identities/PLAN.md`, "Compatibility shim").

So after a full HBJSON conversion, in a fresh process:

```
PhxMechanicalSystemCollection._count == 0
PhxHeatPumpAnnual._count            == 0
```

— verified at runtime. The fallback therefore starts at `1` and walks straight over
the project-scoped IDs.

### 3.3 Why it worked before PR #86

Pre-#86, `__post_init__` did:

```python
self.__class__._count += 1
self.id_num = self.__class__._count
```

One process-global counter. On the shipped CLI path the old code could not
collide, and the reason is **structural, not luck**: `from_HBJSON` never manually
overwrites a collection's or heat-pump's `id_num`, so the global counter is
strictly monotonic and every post-conversion ID strictly exceeded every existing
one. Old-code collision required manually-claimed IDs in the same process — a
prior `from_WUFI_XML` import (old `phx_schemas.py:469` assigned `id_num = IdentNr`
directly) or the test-only counter reset (`tests/conftest.py:74-84`). Neither is
reachable from `hbjson_to_wufi_xml.py`.

So: the transform had a *real* correctness property, but an **unstated and
unenforced** one, inherited from a global counter it is no longer attached to.

### 3.4 One-line statement

> PR #86 replaced a process-global ID counter with a project-scoped allocator and a
> context that ends when the conversion returns. `_bug_fixes.py` mutates the project
> after that point, silently falls back to a counter that is now `0` in a fresh
> process, and re-issues IDs the project has already used.

## 4. Why PR #86 was done, and what it got right

Read [`archive/project-scoped-identities/PRD.md`](../../archive/project-scoped-identities/PRD.md).

**The motivation was concurrency, and it was a real, demonstrated defect** — not
speculative hardening. From the PRD:

- Numeric `id_num` values are WUFI `IdentNr` foreign keys; METr consumes the same
  identities; PHPP uses a subset for in-memory joins.
- Global counters spanned *all* projects in one interpreter. The audit reproduced
  it **without concurrency**: converting the same committed HBJSON fixture twice in
  one process, without the test-only counter reset, produced **324 unified-diff
  lines** of different WUFI XML.
- The driver was the POC web service — several concurrent conversions per process.
  Interleaved (perfectly valid) increments across two projects produce
  nondeterministic output and cross-reference bugs that appear only under load.
  *"Engineering results must not depend on which request constructed a ventilator
  first."*

The design deliberately kept the legacy counters as a **release-1 compatibility
fallback for standalone construction** (PRD §5, PLAN "Compatibility shim"), so
direct `PhxZone()` / `PhxHeatPumpAnnual()` use outside any project keeps working.
That decision is sound and is *not* what broke — the fallback firing on a
*project-owned* object is.

### The gap is a missed application, not a missing design

PR #86 anticipated this situation and built the API for it:

- `PhxProject._attach_identity_allocator()` retains the allocator (`project.py:452`).
- `PhxProject.identity_scope(owner=...)` re-enters it (`project.py:457`).
- `PHASE-4` DoD: *"Attach the completed allocator to `PhxProject` and provide an
  explicit project mutation scope for post-conversion additions."*
- `docs/dev/exporter-patterns.md` (added by #86): *"explicit post-conversion
  mutation enters `phx_project.identity_scope()` (with the variant ID as `owner`
  for variant-local objects)."*
- `docs/reference/phx-model-reference.md:210` (added by #86): *"Later model
  construction that must join the project graph uses
  `with phx_project.identity_scope(owner=variant.id_num):`"*

Grepping the whole `archive/project-scoped-identities/` packet for `bug_fixes` /
`split_cooling` returns **zero hits**. `AUDIT.md` — the inventory of every `_count`
ClassVar and every manual `id_num` overwrite — mentions `to_WUFI_XML` exactly once
(line 179, `_PhxPhBuildingData`). The audit scoped itself to *constructors and
exporter reads* and never enumerated *export-time model mutation*, so
`_bug_fixes.py` fell between PHASE-4 ("no entity built through the public HBJSON
conversion path depends on a global counter" — and this runs outside
`convert_hb_model_to_PhxProject`) and PHASE-6 (which gated the exporter entry
point).

### Where PHASE-6's gate placement is *not* right

The gate caught this bug because the CLI's mutation happens upstream of it. But
**both exporters validate and then mutate**:

| | |
|---|---|
| `xml_builder.py:136` | `validate_project_export_readiness(...)` |
| `xml_builder.py:137` | `synthesize_window_type_psi_variants(...)` ← mutates, ungated |
| `metr_builder.py:29` | `validate_project_export_readiness(...)` |
| `metr_builder.py:30` | `synthesize_window_type_psi_variants(...)` ← mutates, ungated |

So "the gate is correctly placed" holds only for the CLI cooling split. Each
exporter's *own* transform runs outside its own gate, in both targets. See §8.2.

PHASE-6's guardrail — *"validator is read-only and never repairs/renumbers"* —
still rules out any fix that makes the validator paper over a collision.

## 5. Blast radius

**Trigger:** total variant recirculation cooling capacity **≥ 200.0 kW** (the guard
is `if variant_total_cooling_capacity < 200.0: continue`, so exactly 200.0
triggers). Only on the `hbjson_to_wufi_xml.py` path — the sole caller of
`split_cooling_into_multiple_systems()`.

| Path | Affected? |
|---|---|
| Grasshopper `write_wufi_xml` → `PHX/run.py` → `hbjson_to_wufi_xml.py` | **Yes** |
| `hbjson_to_wufi_xml.py` CLI directly | **Yes** |
| `PHX.conversion.from_honeybee()` + `generate_WUFI_XML_from_object()` | No — but see §8.1 |
| `hbjson_to_metr_json.py`, `hbjson_to_phpp.py`, `hbjson_to_ppp.py` | No — none call `_bug_fixes` |
| `from_WUFI_XML` round-trip | No |

Practically: **large multifamily Phius models only.** Single-family and small
projects never reach 200 kW and never enter the transform. That matches the
reporting pattern — it broke on Arverne D and nothing else.

### It is not purely a hard-fail

An earlier draft of this ticket said "hard-fail, not silent-wrong". That is true
only for the **first export in a process**. The legacy counter is process-global
and *does* accumulate across exports, so it walks past the collision:

```
run 1: legacy _count=3   collection IdentNr=[1, 1, 2, 3]  -> EXPORT FAILS
run 2: legacy _count=6   collection IdentNr=[1, 4, 5, 6]  -> EXPORT OK
run 3: legacy _count=9   collection IdentNr=[1, 7, 8, 9]  -> EXPORT OK
```

In any long-lived process — the POC web service PR #86 was built for, a notebook, a
batch loop, a direct library import — a ≥200 kW model today exports a *valid* WUFI
file whose mechanical-system `IdentNr` are a function of how many exports the
process has already performed. That is exactly the nondeterminism #86 existed to
kill, resurfacing through the door it left open.

The one-shot CLI and the `PHX/run.py` subprocess shim are always "run 1", which is
why the user only ever sees the hard failure.

## 6. Why the test suite missed it

`tests/test_to_WUFI_xml/test_bug_fixes/test_cooling_capacity_fix.py` builds its
fixtures with bare constructors:

```python
phx_project = PhxProject()
phx_variant = PhxVariant()
```

No allocator is ever attached, so **every** object in those tests — pre-existing and
new alike — comes from the legacy counters, consistently, and no collision can
occur. The tests assert only device/collection *counts* and capacity values; they
never assert ID uniqueness and never call the validator.

Measured: applying the fix and running the full suite gives **1032 passed, 3
skipped** — byte-identical to baseline. Not one test observes this behaviour in
either direction.

Two structural gaps behind that:

1. **No test exercises the CLI composition.** `convert → _bug_fixes → validate →
   serialize` is only ever assembled in `hbjson_to_wufi_xml.py`, which has no test.
   Every unit test covers one link.
2. **Nothing in this repo pins WUFI XML bytes.**
   `tests/test_to_WUFI_xml/test_reference_cases/test_xml_output.py:25` is literally
   `assert True  # new_xml_txt == ref_xml_text`. Verified: no other test reads
   `tests/reference_files/**/wufi_xml/*.xml` for comparison — `conftest.py:155-163`
   only parametrizes the paths, and `test_project_identity_isolation.py` compares
   run-1 XML to run-2 XML (self-consistency, not a golden). METr's reference test
   (`test_metr_json_output.py:68`) compares **top-level keys only**, not values.
   `tests/test_xl_replay/` is the only true golden and is unaffected — nothing in
   the PHPP path calls `_bug_fixes`.

   PR #86's PRD leans on *"preserve existing clean-process WUFI reference output"*
   as its compatibility gate. **For WUFI XML that gate is inert.**

## 7. Defects the fix un-masks — these must ship with it

Both are pre-existing bugs in `split_cooling_into_multiple_systems()` that are
currently unreachable because the export hard-fails first. Fixing only the IDs
turns a loud refusal into a silently wrong certification model.

### 7.1 Installed cooling capacity is inflated 1.5–2× with ≥2 cooling devices

`_bug_fixes.py:53-54`:

```python
target_cooling_system_size     = variant_total_cooling_capacity / target_number_of_cooling_systems
target_cooling_system_airflow_rate = variant_total_airflow_rate / target_number_of_cooling_systems
```

`target_number_of_cooling_systems = number_of_new_cooling_systems + 1` — the `+ 1`
assumes **exactly one** pre-existing cooling device. But the value is then assigned
to every *device*, existing (`:71-72`) and new (`:92-93`). Measured:

| pre-existing cooling devices | total in | devices out | total out | ratio |
|---|---|---|---|---|
| 1 × 1628.5 kW (Arverne D) | 1628.5 | 9 | 1628.5 | **1.000** |
| 1 × 300 kW | 300.0 | 2 | 300.0 | **1.000** |
| 2 × 150 kW | 300.0 | 3 | 450.0 | **1.500** |
| 3 × 250 kW | 750.0 | 6 | 1125.0 | **1.500** |
| 4 × 100 kW | 400.0 | 6 | 800.0 | **2.000** |

The divisor should be `target_number_of_cooling_devices`
(`= total_number_of_cooling_devices + number_of_new_cooling_systems`), which the
function already computes one line earlier at `:52` and uses correctly for the
coverage percentage at `:55`. Substituting it makes every row above conserve total
capacity, and leaves the Arverne D numbers unchanged.

Arverne D is conservative only because it has exactly one cooling device — which is
why the bug has never been visible.

Device-level `usage_profile.cooling_percent` is **correct**: it sums to exactly
1.0 in every case tested.

⚠️ `test_cooling_capacity_fix.py::test_cooling_capacity_fix_300KW_with_2_mech_systems`
currently **asserts the inflated result as correct**, so it will actively defend
this bug. Fixing the divisor requires fixing that test.

### 7.2 Every new collection claims 100% of zone 1's cooling

`PhxZoneCoverage` defaults to `zone_num=1, cooling=1.0` (`collection.py:74`) and the
transform never sets it. `_PhxZoneCoverage` (`xml_schemas.py:1615-1623`) writes
`IdentNrZone` and `CoverageCooling` per collection. Measured on Arverne D after the
split:

```
zone_nums:        [1, 1, 1, 1, 1, 1, 1, 1, 1]
cooling coverage: [1.0] * 9      sum: 9.0
```

Nine systems each declaring 100% coverage of zone 1 — 900% total. Reachable today
on the `from_HBJSON` path; the dangling-reference variant of this (a WUFI-imported
project whose only zone is `IdentNr 5`) stays latent.

**Checked 2026-08-25 — probably not a defect.** Two real-project files in
`tests/reference_files/from_WUFI/wufi_xml/` disagree with the premise: `_la_mora`
has three systems (`System`, `Cooling overflow`, `Cooling overflow 2`) at
1.0/1.0/1.0 = **3.0**, and `_ridgeway` has two at 1.0/0.5 = **1.5**. Coverage
summing to 1.0 is not a WUFI invariant, and a human splitting cooling into
overflow systems for this same 200 kW reason left each at 1.0 — the names were
typed in the WUFI UI (`git log -S "Cooling overflow"` over `PHX/` is empty). PHX's
output matches that convention. See [`PLAN.md`](PLAN.md) Phase 3 for the residual
question and the provenance caveat.

### 7.3 The trigger is a variant total, not a per-device maximum

The WUFI 3.x limitation is per-Ideal-Air-System. The guard sums the whole variant,
so 4 devices × 100 kW — every one already legal — is split into 6 devices *and*
(via §7.1) doubled. Worth deciding on deliberately rather than inheriting.

## 8. Candidate fixes — after adversarial review

Four reviewers attacked this section. **None of the originally-drafted options is
safe as written.**

### Option A — scope the mutation

```python
with _phx_project.identity_scope(owner=phx_variant.id_num):
    ...create the new collections and heat-pumps...
```

Verified on Arverne D: collections `1,2,…,9`, new devices `3…10`, validation PASS.

`owner=variant.id_num` is the correct key in **both** build paths, verified
empirically on a 2-variant HBJSON and on `_la_mora.xml` (variants `[3, 1]`,
non-sequential):

- `from_HBJSON`: `create_project.py:179` scopes on the 1-based `variant_index` from
  `:168`; `VARIANTS` is project-level and allocated sequentially from 1, so
  `variant.id_num == variant_index`.
- `from_WUFI_XML`: `phx_schemas.py:216` scopes on `variant_dict.IdentNr`;
  `phx_schemas.py:485` claims that same value as `variant.id_num`.

It is the pattern already used in
`tests/test_from_HBJSON/test_project_identity_isolation.py:121` and
`tests/test_from_WUFI/test_project/test_explicit_identity_claims.py:27`.

**Placement is load-bearing:** the `with` must sit *inside* the per-variant loop and
*after* the `< 200.0` `continue`. Around the whole function it would lazily attach
an allocator to every project passed through the CLI.

> #### ⚠️ A1 — unguarded, it breaks hand-assembled projects (CONFIRMED)
>
> `PhxProject.identity_scope()` **lazily creates an empty allocator** when the
> project has none (`project.py:459-460`). For a bare-constructor project the
> existing objects were numbered by the legacy counters and the fresh allocator
> knows nothing about them:
>
> ```
>                   post coll ids   post hp ids   validation
> HEAD (no fix)     [1, 2]          [1, 2]        PASS
> naive Option A    [1, 1]          [1, 1]        FAIL
> ```
>
> Full suite with the naive fix applied: **1032 passed** — nothing catches it.

> #### ⚠️ A2 — the obvious guard is unsound (CONFIRMED, new)
>
> The draft proposed guarding on `_identity_allocator is not None`. **That field is
> set by `identity_scope()` itself.** One prior call — precisely what
> `docs/reference/phx-model-reference.md` tells users to do — flips it permanently,
> and the guard then takes the allocator branch on a legacy-numbered graph:
>
> ```
> no prior identity_scope() call: new coll id=2  new hp id=2   PASS
> one prior no-op call:           new coll id=1  new hp id=1   FAIL
> ```
>
> `_identity_allocator is not None` is not evidence the graph was
> allocator-numbered. **Fix the lazy-create instead of guarding around it** — see
> Option A′.

### Option A′ — make `identity_scope()` honest, then Option A (RECOMMENDED)

Stop `project.py:459-460` from lazily creating an allocator. When
`_identity_allocator is None`, either raise or yield without activating a scope
(legacy path). Then `_identity_allocator is not None` genuinely means "this graph
was allocator-numbered", A2's poisoning vector disappears at the source, and
Option A's guard becomes correct **by construction rather than by luck**.

~3 lines in `project.py` plus the `with` in `_bug_fixes.py`. This is the smallest
change that is actually sound.

### Option B — move the transform into the exporter entry point

**Unsafe as drafted.** `split_cooling_into_multiple_systems` is **not idempotent** —
verified end-to-end through the emitted `MaxRecirculationAirCoolingPower` on a
620 kW model:

```
applied 1x: collections=4   exported total =  630.0 kW
applied 2x: collections=7   exported total = 1378.1 kW
applied 3x: collections=14  exported total = 2756.3 kW
```

Moving the call into `generate_WUFI_XML_from_object()` while
`hbjson_to_wufi_xml.py:265` still calls it ships a WUFI file with **2.2× the
installed cooling capacity**, silently — ID validation passes. Viable only if the
CLI call is deleted in the same commit *and* the transform is made idempotent.
Blast radius is also untested: seven tests call `generate_WUFI_XML_from_object`
with a `PhxProject`, none currently over 200 kW.

Its real merit is §8.1 (the facade never gets the fix) and §8.8 (a shared project
carrying a WUFI-only workaround into PHPP). **Separate ticket.**

### Option C — seed a lazily-created allocator from the graph

**Larger and more dangerous than advertised.** The doc originally claimed the
`_GraphValidator` traversal could be reused. It cannot — the two keying schemes
barely overlap. Measured on `Multi_Room_Complete.hbjson`:

```
validator namespaces : 26
allocator namespaces : 40
INTERSECTION         :  6
```

- The validator keys variant-local namespaces `(f"variants[{i}]", ns)` — a **0-based
  index string** (`identity_validation.py:161`, visible in this ticket's own error
  text).
- The allocator keys them `(owner, ns)` where owner is the **1-based
  `variant_index`** (`create_project.py:179`) or the WUFI `IdentNr`
  (`phx_schemas.py:216`).
- Materials diverge three ways: allocator uses bare `MATERIALS`
  (`constructions.py:84`), validator uses `(MATERIALS, assembly.id_num)`
  (`identity_validation.py:136`), `from_WUFI` uses `(MATERIALS, material IdentNr)`
  (`phx_schemas.py:335`).

A naive shared traversal would seed 26 keys the allocator never reads and leave
**34 of 40 real namespaces unseeded** — doing nothing while appearing to work.

Two further problems, both reproduced:

- Seeding **raises where the code works today**. On a legacy project with a
  deepcopy'd variant (a plausible design-alternative pattern), `claim_id` throws
  `DuplicateIdentityError: (1, 'variant.zones'): 1` at *mutation* time, replacing
  the aggregated, path-annotated `IdentityValidationError` with a single opaque
  error from a helper — a straight diagnostic regression on the contract #86 built.
- `identity_scope()` serves PHPP- and METr-bound projects too. The validator
  deliberately skips namespaces for PHPP (`identity_validation.py:161,187`);
  unconditional seeding would raise on duplicates that are legal for a PHPP export.
- Cost: seeding claims every ID individually, defeating the allocator's high-water
  mark design. At N=100 000: ~28 ms seed, ~12 MB claims dict, per scope entry.

**Rejected for this fix.** Option A′ gets the same safety for three lines.

### Option D — renumber on add (REJECTED)

`add_new_window_type()` bumps `id_num` on collision (`project.py:511`) and one could
do the same for mech collections. Rejected: it does not claim the number in the
allocator, so a later `next_id()` can re-issue it. This is not hypothetical — it is
already shipping in `add_new_window_type` itself (§8.2).

### Option E — don't construct model objects at all (the right long-term shape)

Raised independently by the gpt-5.5 reviewer. The cooling split is a **WUFI 3.x
serialization workaround**, not a fact about the building. The exporter could
project one PHX cooling system into N WUFI `<System>` entries with **export-local**
IDs at the schema layer, and never touch `PhxProject`. That removes this bug class
by construction, removes the idempotency problem, and removes §8.8. It is also a
real piece of work and does not belong in a regression fix. **File as a follow-up.**

## 9. Adjacent findings

Verified during review. Each is independent of this fix; the severe ones need their
own tickets.

**8.1 The WUFI cooling bug-fix is not on the facade path.**
`split_cooling_into_multiple_systems()` lives only in the CLI script. A caller using
`PHX.conversion.from_honeybee()` + `generate_WUFI_XML_from_object()` gets a WUFI file
with a >200 kW ideal-air system and no split — the original WUFI 3.x bug,
unmitigated.

**8.2 `PhxSpace.__add__` mutates the source graph *during serialization*
(SEVERE — filed as [`space-merge-mutates-source-graph`](../../archive/space-merge-mutates-source-graph/README.md)).**
`xml_schemas.py:208` and `metr_schemas.py:970` call `reduce(operator.add, ...)`
while writing the file. `PhxSpace.__add__` (`spaces.py:142`) passes
`ventilation=self.ventilation` — a **shared reference** — then accumulates into it.
Independently reproduced on `Multi_Room_Complete.hbjson` with
`_merge_spaces_by_erv=True` (the setting the Grasshopper component uses):

```
flows before any export:   [53.24, 53.24]
flows after WUFI export 1: [106.48, 53.24]
flows after WUFI export 2: [159.72, 53.24]
two exports byte-identical? False
```

Exporting one `PhxProject` twice — or to WUFI then METr, or WUFI then PHPP
(`phpp_model/vent_space.py:101` reads the same load) — ships a model with
ventilation supply flow inflated by the export count. No validator sees it, and the
byte-comparison that would catch it is the `assert True` from §6.2. Not reachable
from the one-shot CLI; fully reachable from the POC service and from any notebook.

**8.3 `synthesize_window_type_psi_variants` issues an ID it never claims.**
`transforms.py:88` `deepcopy`s a window type (duplicating `id_num`);
`project.py:511-512` renumbers to `max(ids)+1` **without claiming it in the
allocator**:

```
window ids: [1, 2]           allocator WINDOWS: (1, 2)
after synthesize: [1, 2, 3]  allocator WINDOWS: (1, 2)   <- never claimed
next allocator-issued window id: 3   -> collides
```

Benign today only because it runs after the gate and nothing allocates afterwards.
It stops being benign the moment `identity_scope()` becomes the sanctioned mutation
path — which is what this fix makes it. Combined with §4's finding that both
exporters validate-then-mutate, the clean correction is to move
`synthesize_window_type_psi_variants` **above** the validator in both builders and
have `add_new_window_type` claim through the allocator.

**8.4 Five devices share `IdentNr=1` in one WUFI `<System>` today.**
`identity_validation.py:186-190` validates devices per Python class; the WUFI writer
flattens `collection.devices + collection.renewable_devices` into one `<Devices>`
list (`xml_schemas.py:1639-1641`; `metr_schemas.py:1777` likewise). Verified on
stock `main` with a stock fixture:

```
emitted <Devices> IdentNr: ['1', '1', '2', '1', '1', '1']
  = heat-pump / ventilator / 'Test_Unit' / '_unnamed_hw_tank_' / 'my_PV_system'
```

`Room/IdentNrVentilationUnit` (`:936`) and `AssignedVentUnits/IdentNrVentUnit`
(`:1500`) resolve against that list. This is **pre-existing and predates #86** (the
per-class counters behaved identically), and PR #86's PRD explicitly declared reuse
across "typed mechanical-device groups" to be legal (PRD, target-architecture item
7). **So it was a considered decision — but the evidence above suggests the premise
needs checking against a WUFI-authored file.** Separate investigation; do not fold
into this fix. `renewable_devices` are additionally invisible to the validator
entirely (`collection.devices`, `collection.py:541`, returns only `_devices`).

**8.5 `IdentNrPH_Building` is hard-coded.** `xml_schemas.py:367` writes `bd.id_num`
while `xml_schemas.py:256` hard-codes the zone's reference as `1`
(`metr_schemas.py:1369` likewise). Any project where `bd.id_num != 1` writes a
dangling reference, unvalidated.

**8.6 METr's material namespace is project-global; the validator's is per-assembly.**
`identity_validation.py:129` validates materials under `(MATERIALS, assembly.id_num)`
— correct for WUFI (materials nest inside assemblies), wrong for METr, which builds
one global deduplicated `lMaterial` list (`metr_schemas.py:60-67`) that `idMat`
points into (`:173`). Reachable via WUFI round-trip, where `phx_schemas.py:334`
claims exchange materials per-assembly while `:349-350` allocates layer materials
globally.

**8.7 The allocator is not thread-safe, and this fix makes it shareable.**
`next_id` (`identity.py:97-106`) is an unlocked read-modify-write. Measured: 16
threads × 3000 `next_id()` on one allocator → 48 000 calls, **16 637 unique**.
PR #86's PRD explicitly excludes *"concurrent mutation of the same PHX project"*
from the contract, so this is a documented non-goal — but `identity_scope()`
re-entry is what makes a completed allocator re-enterable at all, so the exclusion
should be restated in the docs next to the API, not only in the PRD. Separately:
**ContextVars are not inherited by `threading.Thread`**, so a worker thread spawned
inside a conversion silently falls back to the legacy counter (measured: `allocator
visible in thread: False`).

**8.8 A shared `PhxProject` carries the WUFI workaround into PHPP.**
`phpp_app.py:632-677` iterates **all** `mech_collections`, so a project passed
through the split and then written to PHPP gets 9 cooling systems at 1/9 capacity.
Not reachable via `hbjson_to_phpp.py` (it never calls `_bug_fixes`), but it is the
mirror image of §8.1 and the strongest argument for Option E.

**8.9 `build_project_with_identities` does not enforce an owner scope.** A project
built with the allocator but *without* `identity_owner_scope` puts variant-owned
objects in the unqualified namespace; `owner=variant.id_num` then allocates in a
different, empty one and restarts at 1 (reproduced: 4 duplicates across 2 variants).
No shipped path does this — `create_project.py:179` and `phx_schemas.py:216` both
scope correctly — but it is public API with no guard.

**8.10 `PHX/PHPP/phpp_model/uvalues_constructor.py:18`** has a
`PhxConstructionOpaque()` as a class-body default, allocating an ID at import time.
Never joins a project graph. Noise, not a defect.

## 10. Complete inventory of unscoped construction sites

For the record, so the next person does not have to re-derive it:

| # | Site | Reaches an exported graph? | Covered by this fix? |
|---|---|---|---|
| 1 | `to_WUFI_XML/_bug_fixes.py:81,86` | Yes — `hbjson_to_wufi_xml.py:265` | **Yes** |
| 2 | `model/spaces.py:142` (`PhxSpace.__add__`) via `xml_schemas.py:208`, `metr_schemas.py:970` | Yes — **during serialization**, downstream of the gate | No — [own ticket](../../archive/space-merge-mutates-source-graph/README.md) |
| 3 | `model/transforms.py:88` + `project.py:509` via `xml_builder.py:137`, `metr_builder.py:30` | Yes — **after** validation | No — §8.3 |
| 4 | `PHPP/phpp_model/uvalues_constructor.py:18` | No | n/a — §8.10 |
| 5 | `model/hvac/collection.py:179,318,461` (`copy` + `__add__`) | Only from `create_variant.py` — **inside** the scope | n/a |
| 6 | `from_HBJSON/create_*.py`, all `from_WUFI_XML/phx_schemas.py` builders | Inside `build_project_with_identities` | n/a |

`PHX/from_PHPP/`, `PHX/to_PPP/`, `PHX/xl/` and the `hbjson_to_*.py` scripts construct
**zero** PHX model objects. `to_PPP` has no `id_num` reference at all and correctly
needs no gate.

## 11. Related

- [`archive/project-scoped-identities/`](../../archive/project-scoped-identities/README.md)
  — PRD, AUDIT, and the seven phase briefs for PR #86.
- `docs/dev/exporter-patterns.md` → *Identity lifecycle and export gates* — the
  contract this ticket restores.
- `docs/reference/phx-model-reference.md:210` → *Project-scoped identities*.
- [`PLAN.md`](PLAN.md) — the phased plan of attack.
