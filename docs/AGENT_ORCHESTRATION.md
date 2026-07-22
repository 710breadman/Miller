# Miller agent orchestration

## Governing principle

Agents may research, propose, implement bounded code, and review evidence. Only Miller core owns project/media state. No model silently changes architecture, migrations, public interfaces, licenses, or owner-approved data.

## Hierarchy

| Agent | Responsibility | Allowed actions | Required inputs | Output | Context target | Escalate when |
|---|---|---|---|---|---:|---|
| Director — ChatGPT/Codex | scope, architecture, sprint activation, owner decisions | inspect all; approve cards/ADRs; review/publish | charter, state, roadmap, evidence | active sprint and decisions | 20–60K | owner/license/destructive tradeoff |
| Research agent | current primary-source research | browse/read only; no code mutation | research question, catalog | cited research memo | 8–24K | conflicting terms or weak sources |
| Architecture agent | interfaces, data flow, migrations | propose ADR/schema; no silent merge | relevant subsystem and decisions | ADR and impact map | 16–32K | public API/data migration |
| Sprint planner | split bounded work | edit sprint/control docs only | roadmap item, active evidence | one runnable card | 8–16K | result cannot fit one card |
| Gemma 4 12B worker | primary local implementation | only allowed files; tests/docs; one commit | active card + direct files | code, tests, evidence, handoff | target ≤32K, hard ≤64K | card escalation rules |
| Test/verification agent | independently execute gates | tests, probes, report; no acceptance inflation | diff, card, fixture | evidence report | 8–24K | flaky/non-reproducible failure |
| Code-review agent — Codex | correctness/security/scope review | inspect diff/tests; request changes | card, diff, logs | review findings | 16–40K | architecture or hidden coupling |
| Integration reviewer | cross-subsystem contracts | integration tests and compatibility review | accepted sprint outputs | integration report | 16–40K | regression or schema mismatch |
| Editorial reviewer | visual/narrative assessment | rubric and recommendations; no source mutation | preview/storyboard | E5 review record | 8–24K | preference/intent ambiguity |
| Release reviewer | clean-machine, licenses, manifests | package verification only | release candidate | signed-off checklist | 12–32K | missing notice/license/evidence |

## Gemma operating constraints

Gemma receives only:

1. `PROJECT_CHARTER.md`;
2. `CURRENT_STATE.md` summary section;
3. active card from `docs/sprints/<ID>.md`;
4. directly referenced ADR/decision excerpts;
5. allowed source and test files;
6. exact prior handoff and failing logs.

It does not receive the whole roadmap, research catalog, or repository unless the card explicitly requires them.

### Mandatory Gemma response artifacts

- scope confirmation;
- files inspected and changed;
- implementation summary;
- tests/commands and exact results;
- artifacts/evidence produced;
- failures and unresolved uncertainty;
- state/doc updates;
- exact next action;
- proposed commit message.

### Gemma escalation conditions

Stop and write a blocker when:

- requirements conflict;
- stored data or a migration changes;
- a public interface must break;
- a dependency/license is questionable;
- target hardware invalidates the card;
- unrelated refactoring is necessary;
- acceptance cannot be met;
- the same root failure occurs twice;
- source media could be changed;
- context exceeds 80% before a stable checkpoint.

## Independent review flow

```text
Director activates card
  → Gemma implements bounded scope
  → verification agent reruns focused/full gates
  → Codex reviews diff, evidence, and scope
  → human review added when card requires E5
  → director accepts, rejects, or returns card
  → state advances once
```

The implementer may not be the sole accepter of its work.

## Parallel work

Parallel agents require separate branches/worktrees and non-overlapping allowed files. Only the director integrates. GPU-heavy local tasks run sequentially in v1. Shared database schema, lockfiles, public models, and control files are single-writer resources.

## Handoff format

```markdown
# Handoff — <sprint ID>
Status: complete | blocked | partial
Commit/branch: ...
Evidence level reached: E...
Files changed: ...
Commands and results: ...
Artifacts/reports: ...
Unresolved: ...
Do not redo: ...
Next exact action: ...
Next unblocked cards: ...
```
