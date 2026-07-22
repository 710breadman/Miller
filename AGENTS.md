# Miller project instructions

## Mission

Build a local-first automatic comic-to-video production system that preserves user media, produces traceable/reproducible decisions, survives interruption, and exposes a simple review workflow.

## Startup

1. Read `PROJECT_CHARTER.md`.
2. Read the executive section of `CURRENT_STATE.md`.
3. Read `SPRINT_STATE.json`, only `docs/sprints/<active_sprint>.md`, and `HANDOFF.md`.
4. Inspect Git status and verify the previous next action.
5. Load only directly relevant files/ADRs.

## Hard safety

- User comics, scripts, narration, music, and source media are read-only.
- Never overwrite an existing output or delete user files.
- SQLite is authoritative; vector indexes/caches are rebuildable.
- External workers return proposals; core validates schema, attempt guard, provenance, files, and hashes.
- Use argument arrays, pinned dependencies/models, bounded retries, and localhost-only services.
- Keep GPL/research-restricted tools external unless an explicit license decision changes this.

## Sprint discipline

- One active card, one bounded outcome, one coherent commit.
- Obey allowed/forbidden file scope; no adjacent refactors.
- Search for existing behavior before adding it.
- Do not make architecture, migration, public interface, license, or owner-quality decisions silently.
- Normal Gemma context target is ≤32K; close context at 80% and write a handoff.
- When blocked, log it and move to a dependency-valid fallback card.

## Evidence

E0 intent; E1 contract; E2 synthetic automation; E3 target hardware; E4 real-corpus quantitative; E5 human acceptance; E6 clean-machine release. Never call work complete without naming and proving the required level.

## Required code gate

```text
uv sync --frozen --extra dev --extra web --extra export --extra retrieval
uv run ruff check .
uv run mypy src
uv run pytest
uv build
uv run python scripts/validate_planning.py
```

Inspect generated artifacts and source hashes. Record exact commands/results; “appears to work” is not evidence.

## Close context

Stop new work, run gates, record complete/incomplete state and failures, update decisions/blockers/state once, write the exact next action in `HANDOFF.md`, and create a safe checkpoint when coherent. See `docs/CONTEXT_PROTOCOL.md`.
