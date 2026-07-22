# Implementation report

## Usable today without local AI

Miller can ingest a comic folder or CBZ, create safe derived page assets, build
page analysis records, inspect narration, create deterministic fallback timing,
retrieve candidate pages lexically, build a traceable storyboard, and render a
verified MP4. The baseline command persists its inventory, analyses, alignment,
beats, storyboard, and final render manifest as revisioned project documents.

## Core architecture

SQLite is authoritative. Every expensive stage has typed records, content-based
fingerprints, immutable attempts, restart recovery, and append-only events.
Derived bytes use content-addressed paths and integrity checks. User source files
are never cache directories and are never overwritten.

Heavy or conflicting tools are isolated behind contracts:

- Tesseract OCR subprocess
- WhisperX JSON worker
- OpenCLIP/SigLIP JSON embedding worker
- Ollama structured-output HTTP adapter
- External inpainting worker
- Native FFmpeg renderer
- Optional Qdrant and OpenTimelineIO adapters

## Implemented ahead of the canonical roadmap

- Durable script/video/library queues and bounded workers
- Automatic storyboard generation
- Derived text-cleaning asset chain
- Full FFmpeg audio/video composition and scene cache
- Quality findings and repair proposals
- Revisioned browser editor and optimistic locking
- Evidence-led script stages
- Project portability and OTIO export
- Runtime profiles and Windows packaging

These modules are tested as software contracts. They are not substitutes for
real-corpus, real-model, or subjective visual acceptance tests.

## Deliberately not claimed complete

- Real OpenCLIP/SigLIP winner selection
- Real WhisperX alignment quality on the user's narration
- BallonsTranslator headless integration proof
- Revideo comparison and Windows packaging proof
- Broad web-research provider
- Resolve interchange validation
- Subjective pacing/music/art-quality acceptance
- Final public distribution/license review
