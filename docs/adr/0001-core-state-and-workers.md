# ADR 0001: Core owns state; tools run behind workers

Status: accepted

## Decision

Miller core owns project state, stage transitions, provenance, and artifact
acceptance in SQLite. FFmpeg and future OCR, WhisperX, retrieval, inpainting, and
LLM components run through typed adapters, preferably separate processes when
they have heavy or conflicting dependencies.

Workers may emit progress, warnings, and proposed outputs. Only core may commit a
stage result after validating the current attempt ID, lease token, output schema,
file existence, and hashes.

## Consequences

- A failed model or tool cannot corrupt authoritative state.
- GPU models can be loaded and unloaded independently on an RTX 3070.
- Core remains installable and testable without CUDA or local-AI dependencies.
- Adapter contracts and process lifecycle code require additional implementation.
