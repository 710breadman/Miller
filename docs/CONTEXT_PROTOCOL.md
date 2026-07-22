# Miller context and continuity protocol

## Progressive disclosure

### Startup packet — always small

1. `PROJECT_CHARTER.md`
2. first sections of `CURRENT_STATE.md`
3. `SPRINT_STATE.json`
4. active card only
5. `HANDOFF.md`
6. `git status --short --branch`

### Add only when needed

- relevant architecture section/ADR;
- allowed production files and focused tests;
- exact error logs;
- fixture manifest;
- one research catalog entry.

The full roadmap, board report, and research catalog are planning/review context, not ordinary implementation context.

## Context-start procedure

1. Read charter and evidence definitions.
2. Read current state and active sprint ID.
3. Extract the active card; confirm allowed/forbidden files.
4. Read relevant decisions only.
5. Inspect Git branch/status/diff and latest commit.
6. Verify the previous handoff’s exact test or next command.
7. Confirm prerequisites and blockers.
8. Continue from the recorded next action; do not repeat completed work.

## Context-close procedure

Before session end or at 80% context:

1. Stop starting new work.
2. Reach a safe file/state boundary.
3. Run focused tests; run full gate when appropriate.
4. Inspect generated artifacts and source hashes.
5. Record completed and incomplete changes precisely.
6. Record failures with commands and log locations.
7. Update `SPRINT_STATE.json` only if evidence warrants it.
8. Update decisions, blockers, risks, and current state when changed.
9. Write `HANDOFF.md` with the exact next command/action.
10. Commit a safe checkpoint if the diff is coherent; otherwise preserve a named patch/branch and do not claim completion.

## Context budget

- target startup: ≤6K tokens;
- normal Gemma card: ≤32K total;
- high card: ≤48K, with Codex review;
- hard ceiling: 64K;
- reserve at least 20% for tests, failures, and handoff.

If a card cannot fit, split it into investigation/design/implementation/test cards while preserving its permanent parent ID in history.

## Persistent state rules

- Markdown explains; JSON controls.
- `SPRINT_STATE.json` is machine-readable active state.
- `CURRENT_STATE.md` describes accepted evidence, not aspirations.
- `DECISIONS.md`/ADRs record why.
- `BLOCKERS.md` records owner/external constraints and fallback cards.
- `HANDOFF.md` is replaced each session but history is preserved in commits.
- Logs/artifacts remain in managed workspace and are referenced by hash/path.

## Failure continuation

When blocked:

1. classify local fix, architecture escalation, owner input, hardware, data, license, or external dependency;
2. preserve evidence and partial work;
3. update blocker and handoff;
4. choose the first dependency-valid card in `next_unblocked` with non-overlapping files;
5. never mark the blocked card complete.
