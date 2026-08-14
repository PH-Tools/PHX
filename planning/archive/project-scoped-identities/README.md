# project-scoped-identities — router

**Scope:** Make PHX conversion identities deterministic and isolated per project
so independent conversions can run concurrently without class-global counters
changing one another's IDs or exported cross-references.

**Read order:**
1. `AUDIT.md` — why `_count` exists, every counter family, consumers,
   test/fixture behavior, and compatibility hazards
2. `PRD.md` — required identity and concurrency contract
3. `PLAN.md` — implementation sequence and verification ladder
4. `plans/` — self-contained red-green TDD briefs, one phase at a time
5. `STATUS.md` — current state, decisions, next step, blockers

**Origin:** production-readiness gap identified by the ph-modeler POC review
(2026-08-14). This is not a currently reproduced wrong-energy defect.

**Implementation state:** complete on `codex/project-scoped-identities` as of
2026-08-14. Public HB and WUFI conversions own isolated allocators, all runtime
identity families are scoped, imported WUFI IDs are preserved and reserved, and
affected exporters validate the graph before consuming numeric references. The
full suite passes without reference-fixture changes.
