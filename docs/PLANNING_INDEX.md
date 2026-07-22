# Miller planning index

Planning revision: **2026-07-21-definitive**

## Startup set

Read only:

1. `PROJECT_CHARTER.md`
2. executive section of `CURRENT_STATE.md`
3. `SPRINT_STATE.json`
4. active card in `docs/sprints/<ID>.md`
5. `HANDOFF.md`
6. Git status

## Authority map

| Need | File |
|---|---|
| mission/safety/evidence | `PROJECT_CHARTER.md` |
| proven/current/gaps | `CURRENT_STATE.md` |
| boundaries/data flow | `ARCHITECTURE.md` |
| accepted decisions | `DECISIONS.md` and existing `docs/adr/` |
| milestones/critical path | `ROADMAP.md` |
| sprint navigation | `SPRINT_INDEX.md` |
| active machine state | `SPRINT_STATE.json` |
| exact sprint instructions | `docs/sprints/<ID>.md`; index in `docs/SPRINT_CARDS.md` |
| blockers/fallbacks | `BLOCKERS.md` |
| research sources | `RESEARCH_CATALOG.md` |
| external adopt/adapt/reject | `EXTERNAL_PROJECTS.md` |
| evaluation and metrics | `EVALUATION_PLAN.md` |
| test coverage | `TEST_MATRIX.md` |
| risks | `RISKS.md` |
| agent roles | `docs/AGENT_ORCHESTRATION.md` |
| context reset | `docs/CONTEXT_PROTOCOL.md` |
| specialist reviews | `docs/BOARD_REVIEWS.md` |
| repeated plan reviews | `docs/REVIEW_PASSES.md` |
| first local proof | `docs/LOCAL_ACCEPTANCE_TEST.md` |
| owner decisions | `docs/OWNER_DECISIONS.md` |
| latest exact continuation | `HANDOFF.md` |
| planning history | `CHANGELOG_PLANNING.md` |

## Legacy documents

Existing product specs, implementation reports, tool audits, capability matrices, and ADRs remain evidence and source material. They are not deleted. Where they conflict with the definitive files, record and resolve the conflict in `DECISIONS.md`; do not silently rewrite history.

## Validation

```powershell
uv run python scripts/validate_planning.py
```
