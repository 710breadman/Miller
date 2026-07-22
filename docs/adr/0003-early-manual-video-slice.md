# ADR 0003: Prove a manual video slice before AI automation

Status: accepted

## Decision

Before OCR, embeddings, storyboard AI, and repair models are complete, Miller
supports a narrow path from manually selected comic images and optional narration
to a typed scene specification and native FFmpeg render.

This proof does not replace the later renderer sprint. It validates scene timing,
source integrity, command construction, manifests, media probing, and visual motion
with minimal dependencies.

## Consequences

- End-to-end architecture problems are discovered early.
- Users can produce a basic result before automatic retrieval exists.
- Rich transitions, music policy, subtitles, partial render segments, and Revideo
  remain later work.
