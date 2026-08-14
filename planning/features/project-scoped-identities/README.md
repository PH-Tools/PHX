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

**Planning boundary:** this packet is docs-only as of 2026-08-14. No runtime
identity behavior or tests have been changed yet.
