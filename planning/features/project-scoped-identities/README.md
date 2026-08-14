# project-scoped-identities — router

**Scope:** Make PHX conversion identities deterministic and isolated per project
so independent conversions can run concurrently without class-global counters
changing one another's IDs or exported cross-references.

**Read order:**
1. `PRD.md` — what / why (identity and concurrency contract)
2. `STATUS.md` — current state, next step, blockers

**Origin:** production-readiness gap identified by the ph-modeler POC review
(2026-08-14). This is not a currently reproduced wrong-energy defect.

