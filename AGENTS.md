# Project instructions

## Goal

Build a local-first automatic YouTube production system that creates comic-first
videos from scripts, narration, research, and an indexed comic library.

## Source study

Before implementing any significant capability:

1. Search this repository for existing work.
2. Inspect approved upstream projects implementing similar behavior.
3. Record architecture, interfaces, limits, license, tests, dependencies, and
   reusable concepts.
4. Prefer proven code or patterns when they preserve project capability.
5. Never adopt an upstream limit merely to reduce implementation work.
6. Integrate through typed, replaceable adapters.
7. Copy or port code only after explicit license review.
8. Record exact upstream repository and revision.
9. Add contract tests for every external integration.

MoneyPrinterTurbo is a major study source, not this application's foundation.

## Ownership

This repository owns project state, job state, source provenance, script stages,
comic index, storyboard, scene definitions, repair history, user overrides, and
render history. External applications never become source of truth.

## Safety

- Treat comic libraries as read-only.
- Never overwrite narration, scripts, comics, or user media.
- Store derived assets only in managed project/cache directories.
- Never delete user files during cleanup.
- Never run downloaded code without explicit provenance.
- Never silently ignore failed stages.
- Never claim success without tests or artifact verification.

## Pipeline

- Every stage has typed input and output.
- Cache every expensive result by content hash.
- Make every stage independently rerunnable.
- Invalidate only dependent stages after input changes.
- Resume failed projects after restart.
- Run video projects sequentially in Version 1.
- Bound all quality and agent loops. Default repair limit: two passes.

## AI

- AI output remains a proposal until validated and parsed.
- Require structured output.
- Preserve prompts and model identifiers.
- Separate evidence from interpretation.
- Never invent source provenance.
- Give alternatives for low-confidence visual matches.
- Do not use autonomous agents for file mutation or render-state control.

## Codex procedure

1. Read `AGENTS.md`, `STATUS.md`, and `SPRINT_STATE.json`.
2. Read only active sprint in `SPRINTS.md`.
3. Inspect existing implementation.
4. Select next incomplete task.
5. Implement only that task.
6. Run relevant tests and verify artifacts.
7. Update status and sprint state.
8. Record decisions/failures.
9. Stop at a stable checkpoint.
