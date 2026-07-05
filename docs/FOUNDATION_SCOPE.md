# Foundation branch scope

This branch completes the executable package skeleton and adds initial typed
records for the next checkpoint.

Included:

- Python package and build configuration
- Lightweight core dependencies
- Immutable project, stage, attempt, artifact, and event records
- Import and schema smoke tests
- Updated branch README and status

Excluded:

- SQLite persistence
- Pipeline execution
- CLI behavior
- Comic ingestion
- Rendering and AI workers

Those capabilities remain separate checkpoints so Codex can continue from a
small, reviewable state.
