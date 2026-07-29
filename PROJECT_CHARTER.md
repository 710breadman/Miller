# Miller project charter

Charter revision: **2026-07-21-definitive**

## Mission

Miller is a **local-first, traceable, resumable comic-to-video production system**. Its primary workflow turns a finished script and edited narration into a polished, comic-first video by indexing an approved comic library, understanding pages and panels, retrieving the strongest visual matches, building a coherent storyboard, aligning timing, rendering, and allowing focused human correction.

Miller must feel simple to operate while retaining deep provenance, alternatives, revision history, and an optional complex export.

## Intended experience

### Normal input

- finished script;
- edited narration supplied by the owner;
- approved comic folders or CBZ files;
- optional steering keywords;
- optional music.

### Alternate input

- topic, briefing, keywords, and approved research sources;
- Miller may create a script through a separately validated script-factory workflow.

### Normal output

- a polished H.264/AAC video;
- comic artwork is the dominant visual source;
- lettering or other distracting page text is avoided, cropped, masked, or removed when approved;
- no on-screen text by default; subtitles remain an explicit option;
- background music is complementary, quiet, and ducked under narration;
- a simple project and storyboard editor supports corrections;
- a complex timeline export is optional.

### Duration

The owner preference is **13–18 minutes** for normal video essays, with shorter content allowed when the subject does not support that length and a separate deep-dive mode for longer work. `docs/PRODUCT_SPEC.md` is reconciled to this default; historical planning references remain historical.

## Product principles

1. **Local first.** Core operation must not require a cloud account.
2. **Read-only sources.** Never overwrite comics, narration, scripts, music, or other user media.
3. **Miller owns state.** SQLite and immutable artifacts own project, queue, provenance, revision, and render state.
4. **External AI is replaceable.** OCR, alignment, VLM, embedding, inpainting, and LLM environments communicate through versioned typed boundaries.
5. **AI output is untrusted.** Validate schema, provenance, bounds, confidence, hashes, and applicability before accepting it.
6. **Evidence before completion.** A contract test is not a real-corpus pass; a real-corpus pass is not a human quality pass.
7. **Resume safely.** Expensive stages are independently repeatable and invalidate only affected dependents.
8. **Simple surface, strong engine.** Ordinary operation should require little interaction; advanced controls remain available.
9. **Bounded loops.** Repair, retry, research, and agent loops have explicit limits.
10. **Preserve working work.** Improve existing subsystems rather than rebuilding them without evidence.

## Core product requirements

- safe folder and CBZ ingest;
- stable identity and provenance for sources, pages, panels, regions, derived assets, and revisions;
- panel, balloon, text-region, and reading-order analysis;
- OCR and visual semantic analysis;
- searchable dialogue, descriptions, characters, locations, actions, emotions, quality, and source locators;
- lexical, multimodal, metadata, and reranked retrieval;
- page-level and panel-level candidate selection;
- script-to-beat and beat-to-scene planning;
- global continuity, emotional relevance, visual variety, and reuse control;
- narration timing with a measured fallback;
- safe crops, motion, transitions, masks, cleanup, and optional inpainting;
- native FFmpeg rendering;
- focused human review, locks, alternatives, and partial rerender;
- queue, progress, cancellation, restart, and recovery;
- reproducible manifests and optional editorial interchange;
- explicit approved feedback records for later improvement.

## Experimental or optional capabilities

- Revideo renderer;
- SAM/subject masks and depth-assisted parallax;
- automated character re-identification beyond local sequences;
- DaVinci Resolve interchange;
- learned reranking or active learning;
- automatic script research from the web;
- optional automatic narration cleanup;
- advanced inpainting or generative edge extension.

These must not become mandatory for a basic render.

## Milestones

### Minimum usable

A Windows-local installation can ingest a real short comic, build a no-AI/OCR-optional storyboard, render a verified MP4, preserve sources, refuse overwrite, record provenance, and recover cleanly from a stopped run.

### Strong v1

Real comic-aware panel/text analysis, measured OCR, multimodal retrieval, real narration alignment, coherent storyboard selection, visual review, partial correction, and reliable target-hardware performance all pass.

### Polished v1

The local UI supports the full workflow; quality repair is evidence-backed; text-free visual handling is dependable; queues, recovery, packaging, notices, clean-machine install, and release evidence pass.

### Long-term vision

Miller becomes a private, searchable comic-production library and editorial assistant that improves through owner-approved labels and corrections without losing reproducibility or becoming dependent on a single model or cloud service.

## Explicit non-goals

- replacing a professional nonlinear editor;
- generating or redistributing comic libraries;
- silently training on owner media;
- a general-purpose autonomous agent platform;
- mandatory cloud storage, cloud inference, or hosted databases;
- copying GPL or restricted research code into the core without a license decision;
- automatically publishing videos;
- claiming copyright or legal conclusions;
- using model confidence as a substitute for human acceptance.

## Target operating environment

- Windows 11;
- Ryzen 7 3700X;
- RTX 3070 8 GB;
- 32 GB RAM;
- local context budget around 64K tokens for Gemma 4 12B implementation work;
- current owner-reported working path is `V:\AI\Miller`; verify in `ENV-001`;
- CPU fallback must remain functional.

## Implementation team

- **ChatGPT/OpenAI/Codex:** director, research, architecture, sprint planning, review, escalation, and release approval.
- **Gemma 4 12B:** primary local implementation worker for bounded sprints.
- **Specialized external workers:** optional runtime OCR, alignment, embedding, VLM, and inpainting processes.
- **Owner:** approves private test data, subjective quality, distribution/license choices, and high-impact product decisions.
