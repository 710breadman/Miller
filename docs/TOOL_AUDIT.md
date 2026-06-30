# Tool audit

Audit date: 2026-06-29. Revisions are immutable in
[`upstream-lock.json`](upstream-lock.json). Repositories were inspected
read-only. No downloaded source was executed.

## Executive decision

Miller should own project state, stage transitions, provenance, comic metadata,
storyboards, repair history, and render manifests. Use narrow adapters around
libraries/tools. Do not fork an upstream application.

## MoneyPrinterTurbo

Decision: study and recreate selected patterns; do not use as foundation.

Observed:

- FastAPI endpoints enqueue tasks through in-memory or Redis managers.
- `app/services/task.py` directly sequences script, terms, audio, subtitles,
  materials, and final rendering.
- FFmpeg/MoviePy-oriented services already cover local media, stock providers,
  subtitles, music, transitions, and task APIs.
- Tests cover services, schemas, state, CLI, uploads, and video behavior.

Useful:

- Request/config vocabulary, local-media validation, task endpoint shape,
  subtitle fallback, media normalization, and practical FFmpeg composition
  cases.

Reject:

- Its task/state model as Miller's source of truth. It lacks Miller's
  content-hash DAG invalidation, scene provenance, partial repair, and strict
  project resume semantics.

Evidence:
[task pipeline](https://github.com/harry0703/MoneyPrinterTurbo/blob/48b08719c9690739a79dc70665db8dbd109c2afc/app/services/task.py),
[video API](https://github.com/harry0703/MoneyPrinterTurbo/blob/48b08719c9690739a79dc70665db8dbd109c2afc/app/controllers/v1/video.py).

## BallonsTranslator

Decision: adapt interface concepts; prototype external/headless adapter. Do not
copy GPL code into core.

Observed:

- Registry-backed `TextDetectorBase`, `OCRBase`, and `InpainterBase` modules.
- Text detection returns both mask and `TextBlock` list.
- Inpainting supports block-limited masks, alpha preservation, low-memory
  retries, balloon-mask checks, and several backends.
- Main orchestration uses Qt threads, UI config, signals, and project objects.

Useful:

- Detector → OCR → mask refinement → inpaint contract.
- Clean separation among model registries and common base interfaces.
- Mask restriction to detected blocks and per-region fallback.

Risk:

- Headless extraction is not a stable public service API and is coupled to app
  config/Qt orchestration. GPL-3.0 blocks casual source copying into an
  unlicensed/public core.

Next proof:

- Feed one fixture page through a separately installed pinned checkout via a
  process boundary. Capture image, mask, regions, model IDs, and errors.

Evidence:
[detector base](https://github.com/dmMaze/BallonsTranslator/blob/27c26554fc2ee753fa42d7521441e93098c3e830/ballontranslator/modules/textdetector/base.py),
[inpaint base](https://github.com/dmMaze/BallonsTranslator/blob/27c26554fc2ee753fa42d7521441e93098c3e830/ballontranslator/modules/inpaint/base.py).

## StoryToolkitAI

Decision: study concepts only; no code reuse.

Observed:

- JSON-backed processing queue with task dependencies, status history,
  cancellation, and device-specific worker tracking.
- Project objects own linked transcriptions/stories and timeline metadata.
- Search supports semantic clip indexes.
- Direct DaVinci Resolve scripting integration reads projects, timelines,
  markers, bins, and media.

Useful:

- Search-corpus lifecycle, story-as-edit structure, timeline marker workflows,
  and Resolve failure handling.

Reject:

- Queue persistence design and project model for core. Miller needs atomic
  SQLite transitions, hash invalidation, immutable attempts, and media-specific
  provenance. GPL-3.0 source remains study-only.

Evidence:
[processing queue](https://github.com/octimot/StoryToolkitAI/blob/541b4128d763adab4608fbfa6b888b1ae092a253/storytoolkitai/core/toolkit_ops/processing_queue.py),
[Resolve integration](https://github.com/octimot/StoryToolkitAI/blob/541b4128d763adab4608fbfa6b888b1ae092a253/storytoolkitai/integrations/mots_resolve.py).

## Revideo

Decision: retain as optional renderer candidate; benchmark against native
FFmpeg.

Observed:

- TypeScript monorepo separates core, 2D components, player, renderer, FFmpeg,
  UI, and Vite integration.
- Headless rendering starts Vite plus Puppeteer workers, renders browser-side
  frames, then uses FFmpeg helpers for audio/video output.
- Render settings expose FFmpeg, Puppeteer, worker, project, variable, and
  progress controls.
- E2E render tests exist.

Strength:

- Declarative scenes, reusable animated components, browser preview, and a
  clean path to richer motion templates.

Cost:

- Node + Chromium + Vite add startup, memory, packaging, port, and
  determinism surfaces. Native FFmpeg still remains underneath.

Gate:

- Render identical two-minute comic fixture through both backends. Compare
  frame hashes/tolerances, wall time, peak RAM/VRAM, output size, cancellation,
  subtitles, audio sync, and Windows packaging.

Evidence:
[renderer](https://github.com/midrender/revideo/blob/eef799d3999b1ec441a778e7f573f288a719c647/packages/renderer/server/render-video.ts),
[E2E tests](https://github.com/midrender/revideo/blob/eef799d3999b1ec441a778e7f573f288a719c647/packages/e2e/src/rendering.test.ts).

## WhisperX

Decision: call through a typed adapter, preferably an isolated worker process.

Observed:

- Public lazy API exposes `load_model`, `load_audio`, `load_align_model`,
  `align`, and speaker assignment.
- Pipeline separates VAD/ASR, alignment, and optional diarization.
- Alignment accepts transcript segments plus audio and returns word timing.
- Models can be unloaded between phases; this suits constrained VRAM.

Adapter rules:

- Pin package/model revisions and compute type.
- Normalize output into Miller-owned schema.
- Record language, model, device, warnings, and unaligned words.
- Treat edited narration as authoritative. Compare supplied script separately.
- Keep diarization disabled by default.

Evidence:
[public API](https://github.com/m-bain/whisperX/blob/8dcdec18039f6f6b10b967c45273f54dd2a1f699/whisperx/__init__.py),
[alignment](https://github.com/m-bain/whisperX/blob/8dcdec18039f6f6b10b967c45273f54dd2a1f699/whisperx/alignment.py).

## OpenTimelineIO

Decision: call official Python package for optional export only.

Observed:

- Mature editorial data model for cut order, duration, and external media refs.
- Media itself is deliberately outside OTIO.
- Python bindings build `Timeline`, `Track`, `Clip`, `ExternalReference`, and
  `TimeRange`.
- Non-native adapters moved to separately versioned plugin packages after
  0.16.

Rules:

- Miller manifest stays authoritative.
- Export rational frame times; validate round-trip.
- Pin matching core/plugin versions.
- Treat Resolve interchange as a separate compatibility proof.

Evidence:
[overview](https://github.com/AcademySoftwareFoundation/OpenTimelineIO/blob/73803eff1dbf86b82bcf97179567a243f4036b90/README.md),
[timeline example](https://github.com/AcademySoftwareFoundation/OpenTimelineIO/blob/73803eff1dbf86b82bcf97179567a243f4036b90/examples/build_simple_timeline.py).

## OpenCLIP and SigLIP 2

Decision: benchmark; do not select from generic benchmark scores.

OpenCLIP exposes straightforward image/text encoders and many checkpoints.
Current `main` requires modern PyTorch and warns that training APIs changed;
Miller needs inference only and should pin a released 3.x-compatible API or
tested commit.

SigLIP 2 provides multilingual retrieval models from 86M to 1B parameters,
including variable-aspect NaFlex variants. Start with B-class models suitable
for RTX 3070, using a maintained inference wrapper rather than adopting
Big Vision's training stack.

Benchmark must cover 100–300 labeled comic queries, hard negatives, art styles,
costumes/eras, emotional abstractions, actions, pages vs panels, VRAM, indexing
speed, and query latency.

Evidence:
[OpenCLIP usage](https://github.com/mlfoundations/open_clip/blob/89fb801f1e6087880e951fc8354b8a2077b79c6d/README.md),
[SigLIP 2 reference](https://github.com/google-research/big_vision/blob/0127fb6b337ee2a27bf4e54dea79cff176527356/big_vision/configs/proj/image_text/README_siglip2.md).

## Qdrant

Decision: call official Python client behind Miller's vector-store protocol.

Observed:

- Server and local persisted/in-memory modes share client shape.
- Payload filtering, batch upload, sync/async APIs, and gRPC are available.
- Local mode is useful for tests; Version 1 production should use a pinned local
  Qdrant service for operational parity and metadata filtering.

Rules:

- Miller SQLite owns asset identity/provenance.
- Qdrant contains rebuildable vectors plus filter payloads.
- Never store irreplaceable project state only in Qdrant.

Evidence:
[Python client](https://github.com/qdrant/qdrant-client/blob/326adefcc2158121dd0d04877e1a483b5aa2627b/README.md).

## SAM 2

Decision: optional call for selected subject masks; reject as required stage.

Image API supports prompted masks. Tiny/small checkpoints are plausible
starting points, but published speeds use A100 hardware and do not establish
RTX 3070 fit. Installation may compile CUDA extensions. Benchmark on a small
comic fixture and unload before other GPU stages.

Evidence:
[SAM 2 README](https://github.com/facebookresearch/sam2/blob/2b90b9f5ceec907a1c18123530e92e794ad901a4/README.md).

## Depth Anything V2

Decision: optional selective parallax using Small only at first.

The repository exposes direct and Transformers inference. Code and Small
weights are Apache-2.0; Base/Large/Giant weights are CC-BY-NC-4.0. Reject
non-commercial weights for default/distributable workflows.

Evidence:
[Depth Anything V2 README](https://github.com/DepthAnything/Depth-Anything-V2/blob/a561b849ebae10a6f5ef49e26c83cbbcd36c71bf/README.md).

## Native platform components

- FFmpeg/FFprobe: call executables with argument arrays; parse machine-readable
  FFprobe JSON; keep commands/manifests. Mandatory renderer and media probe.
- Ollama: call HTTP API, never scrape CLI output. Validate every structured
  response before state mutation.
- SQLite: own transactional stage state and queue serialization.
