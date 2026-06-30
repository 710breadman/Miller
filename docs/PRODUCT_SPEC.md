# Comic to Video: Final Product Definition

## One-sentence product statement

**Comic to Video is a local-first automatic YouTube production system that researches and writes human-sounding scripts, searches an indexed comic library for appropriate artwork, synchronizes visuals to recorded narration, creates a polished comic-first video, automatically repairs weak scenes, and optionally exports a professional editable timeline.**

## Primary product

It is primarily an:

> **Automatic YouTube video generator built on top of a searchable and pre-analyzed comic-production library.**

The searchable library, research engine, script factory, storyboard, and renderer support this automatic workflow. They are not separate products the user must operate manually.

## Typical result

* Default length: **8–12 minutes**
* Optional mode: **Deep Dive**
* Visual emphasis: **mostly comic artwork**
* Normal input: **finished script and edited narration**
* Alternate input: briefing, keywords, sources, or a topic
* Default operation: fully automatic
* Cleanup: simple scene-based editor
* Advanced editing: optional complex timeline export
* Default QC: automatic repair loop
* Project handling: one video completed fully before the next begins

---

# 1. Target Workflow

## Primary workflow

```text
Finished script
+ edited narration
+ optional steering keywords
        ↓
Validate script and audio
        ↓
Align narration to script at word level
        ↓
Detect story sections and visual beats
        ↓
Propose comic search scope
        ↓
Search approved characters, series, arcs, and eras
        ↓
Rank and verify pages and panels
        ↓
Remove or avoid comic lettering
        ↓
Create scene plan and motion plan
        ↓
Select adaptive music
        ↓
Render draft
        ↓
Run automatic quality analysis
        ↓
Repair weak scenes
        ↓
Repeat up to configured pass limit
        ↓
Render final YouTube video
        ↓
Optional scene cleanup or complex export
```

## Script-creation workflow

```text
Topic / briefing / keywords / sources
        ↓
Choose research mode
        ↓
Discover possible framing angles
        ↓
Research local and web sources
        ↓
Build compact evidence ledger
        ↓
Propose theses and structures
        ↓
Create outline
        ↓
Draft script
        ↓
Fact and lore verification
        ↓
Theme and structure review
        ↓
Human-tone rewrite
        ↓
Read-aloud and speech-rhythm pass
        ↓
Anti-repetition pass
        ↓
Anti-robotic-language pass
        ↓
Length and pacing pass
        ↓
Final script
```

Research modes:

* Closed-source
* Local-library-first
* Broad research — default
* Custom source set

Script styles:

* Documentary
* Video essay
* Character analysis
* Lore investigation
* Hidden history
* Real-world parallels
* Publication history
* Relationship analysis
* Mystery or secrets
* Dark history
* Entertainment-focused
* Custom blend

---

# 2. Source-Study Strategy

The project must not treat existing tools merely as external programs. Codex should inspect their actual repositories and determine what can be:

* Called directly
* Wrapped
* Ported
* Adapted
* Reimplemented from a proven design
* Used as a fallback
* Used only as reference
* Rejected

MoneyPrinterTurbo already demonstrates API and web interfaces, custom or generated scripts, batch generation, subtitles, music, local media, multiple stock providers, Ollama support, and configurable scene duration. Those are valuable patterns and possible reusable components, but they should not dictate the new application’s limits. ([GitHub][1])

BallonsTranslator is especially relevant because its existing workflow includes comic text detection, recognition, removal, balloon-region handling, masks, inpainting, and interactive image editing. Its internals should be studied before building custom comic-text removal. ([GitHub][2])

StoryToolkitAI should be studied for transcript indexing, semantic footage search, story construction, EDL/XML/Fountain export, project management, and DaVinci Resolve integration. It is GPL-3.0, so direct code reuse requires an explicit licensing decision; initially, study its architecture or integrate externally rather than copying its code into the core. ([GitHub][3])

Revideo is an MIT-licensed TypeScript framework designed for programmatic video editing, dynamic templates, browser previews, audio synchronization, and headless rendering. It is a strong renderer candidate, but it should first be tested against a native FFmpeg renderer using real comic scenes. ([GitHub][4])

---

# 3. Tool Classification

## Core dependencies

### FFmpeg and FFprobe

Responsibilities:

* Media inspection
* Audio conversion
* Loudness analysis
* Image sequence rendering
* Pans, zooms, crops, overlays, fades, and transitions
* Subtitle composition
* Music mixing and ducking
* Proxy and final rendering

FFmpeg remains the lowest-level media engine even if Revideo provides scene composition. Its filter system is designed for structured audio and video processing. ([FFmpeg][5])

### WhisperX

Responsibilities:

* Transcription verification
* Word-level timestamps
* Forced alignment
* Voice-activity detection
* Mapping the supplied script to the actual narration

WhisperX provides word-level alignment and supports local GPU execution; its repository is BSD-2-Clause licensed. ([GitHub][6])

### Ollama model gateway

Responsibilities:

* Local script analysis
* Framing generation
* Beat segmentation
* Query generation
* Theme and emotion analysis
* Script rewrites
* Candidate verification where suitable

Ollama exposes local chat, generation, embedding, model-inspection, and running-model APIs. The project should access it through its API rather than shell-scraping terminal output. ([Ollama Documentation][7])

### SQLite

Responsibilities:

* Projects
* Jobs
* Queue state
* Pipeline stages
* Assets
* User overrides
* Render history
* Failures
* Tool versions

### Qdrant

Responsibilities:

* Comic panel embeddings
* Semantic text-to-image search
* Metadata filtering
* Character, series, issue, era, and continuity restrictions

Qdrant supports local execution, vector similarity search, stored payloads, and structured filtering. That makes it more appropriate than raw FAISS for the main application, where visual similarity and comic metadata must be queried together. ([Qdrant][8])

FAISS remains useful as a benchmark or lightweight fallback, but it is primarily a similarity-search library rather than a complete metadata-aware database. ([GitHub][9])

## Candidate core components requiring evaluation

### OpenCLIP versus SigLIP

Use for semantic text-to-panel retrieval.

Do not choose permanently before benchmarking them on actual comic panels. OpenCLIP supplies many pretrained image-text models, while SigLIP supplies separate image and text encoders suitable for cross-modal retrieval. ([GitHub][10])

The project must create a small labeled evaluation set:

* 100–300 narration queries
* Known relevant panels
* Hard negatives
* Different art styles
* Different costumes and eras
* Abstract emotional queries
* Concrete action queries

Select the model based on comic-specific retrieval quality, VRAM use, indexing speed, and query speed.

### Revideo

Use when it demonstrably improves:

* Scene templates
* Camera paths
* Animated overlays
* Previewing
* Deterministic rerendering
* Reusable effect components

Keep a native FFmpeg rendering path so Revideo never becomes a single point of failure.

### BallonsTranslator components

Study and potentially integrate:

* Text detector
* OCR regions
* Removal masks
* Inpainting modules
* Balloon boundaries
* Manual mask correction

Prefer a headless module adapter. Do not launch and automate its full GUI unless no stable internal interface is available.

## Optional advanced tools

### SAM 2

Use for occasional subject masks and object-aware effects. SAM 2 supports promptable segmentation in images and video, but it should not be required for every ordinary scene. ([GitHub][11])

### Depth Anything V2

Use for optional depth-assisted parallax. It provides models at different scales, making a smaller model practical for selective use on current hardware. ([GitHub][12])

### ComfyUI

Optional only:

* Inpainting difficult text
* Extending panel edges
* Special energy effects
* Controlled cleanup
* Highlight-scene animation

It must never be required for a basic render.

## Study or optional adapters

* MoneyPrinterTurbo
* StoryToolkitAI
* NarratoAI
* Pixelle-Video
* Immich
* PhotoPrism
* yt-dlp
* Manga OCR
* PaddleOCR

## Do not adopt initially

* Temporal
* Prefect
* LangGraph
* CrewAI
* AutoGen
* n8n
* Node-RED
* LlamaIndex
* Haystack

They may be reconsidered later, but the first pipeline needs a small deterministic stage runner, not another orchestration platform.

---

# 4. Recommended Architecture

```text
React local UI
        ↓
FastAPI application service
        ↓
Project and queue manager
        ↓
Deterministic pipeline engine
        ↓
Capability and tool registry
        ↓
┌───────────────────────────────────────────────┐
│ Research       Comic indexing   Audio         │
│ Script factory Retrieval        Rendering     │
│ Quality loop   Music            Export        │
└───────────────────────────────────────────────┘
        ↓
SQLite + Qdrant + content-addressed file cache
        ↓
FFmpeg / WhisperX / Ollama / optional workers
```

## UI

Version 1 should run as a local web application:

* React frontend
* FastAPI backend
* Automatic browser launch

Later, it may be packaged with Tauri. Do not add desktop-shell complexity before the complete pipeline works.

## Pipeline engine

Use a custom deterministic state machine backed by SQLite.

Each stage must support:

* Pending
* Running
* Completed
* Failed
* Skipped
* Invalidated
* Cancelled

Each stage records:

* Input hashes
* Configuration
* Tool version
* Model
* Prompt version
* Start and completion time
* Output artifacts
* Logs
* Error
* Retry count

If an upstream artifact changes, only dependent stages are invalidated.

## Queues

### Script queue

May prepare several scripts sequentially:

```text
Research → framing → evidence → outline → draft → checks → final
```

### Video queue

Strict project-level sequencing:

```text
Complete Video A fully
→ archive stable state
→ begin Video B
```

Library indexing and cache maintenance may run independently, but two video projects should not compete for the GPU in Version 1.

---

# 5. Unified Project Format

Suggested project layout:

```text
projects/<project-id>/
├── project.json
├── input/
│   ├── brief.md
│   ├── keywords.json
│   ├── script.txt
│   └── narration.wav
├── research/
│   ├── sources.jsonl
│   ├── claims.jsonl
│   ├── framing_candidates.json
│   └── context.caveman.txt
├── script/
│   ├── outline.json
│   ├── draft-01.txt
│   ├── verified.txt
│   ├── humanized.txt
│   └── final.txt
├── audio/
│   ├── alignment.json
│   ├── waveform.json
│   └── cleaned-preview.wav
├── storyboard/
│   ├── beats.json
│   ├── scenes.json
│   └── alternatives.json
├── assets/
│   ├── original-references/
│   ├── derived-panels/
│   ├── masks/
│   ├── music/
│   └── effects/
├── renders/
│   ├── draft/
│   ├── repair-pass-01/
│   ├── repair-pass-02/
│   └── final/
├── export/
└── logs/
```

## Compact research storage

Do not save entire websites unless specifically required.

Store:

```json
{
  "claim_id": "claim_0042",
  "claim": "Compact normalized factual claim",
  "source_id": "source_0017",
  "locator": "issue 50, pages 17-19",
  "evidence_excerpt": "Short supporting excerpt or paraphrase",
  "support": "strong",
  "confidence": 0.92,
  "used_in_sections": ["section_06"]
}
```

The “Caveman” version should be generated from this structured evidence:

```text
PETER QUIT.
CITY WORSE.
DUTY PULL PETER BACK.
SOURCE: ASM50 P17-19.
SUPPORT STRONG.
```

The Caveman file saves model context. It is **not** the authoritative source record.

---

# 6. Storyboard and Scene Model

Each scene should contain:

```json
{
  "scene_id": "scene_0042",
  "start": 128.42,
  "end": 134.80,
  "narration": "Spoken text",
  "intent": "Hero accepts an unwanted responsibility",
  "mood": "reflective",
  "primary_asset": "panel_9812",
  "alternatives": ["panel_1182", "page_0911"],
  "source": {
    "series": "Example Series",
    "issue": "50",
    "page": 18,
    "continuity": "main"
  },
  "selection_scores": {
    "semantic": 0.88,
    "character": 0.97,
    "theme": 0.84,
    "continuity": 0.72,
    "reuse_penalty": 0.0
  },
  "text_treatment": "inpaint",
  "camera": {
    "preset": "slow_push",
    "focus": [0.42, 0.37],
    "intensity": 0.31
  },
  "transition": "cut",
  "music_state": "low_tension",
  "effect": null,
  "review_status": "automatic"
}
```

## Reuse policy

A panel should normally appear once.

Reuse is permitted when marked as:

* Callback
* Symbolic repetition
* Before-and-after comparison
* Central recurring image
* Deliberate thematic motif

The search ranker must apply a strong reuse penalty across the current project.

## Continuity policy

* Prefer visual consistency within a section.
* Allow different eras when useful.
* Warn only when a shift could mislead the viewer.
* Multiverse and retcon material may be used intentionally.
* Search steering keywords can include eras, continuity, costumes, exclusions, and mood.

---

# 7. Visual and Motion Policy

## Normal scene treatment

* Crop
* Reframe
* Slow pan
* Slow push or pull
* Page-to-panel movement
* Cut
* Crossfade
* Dip to black
* Lightweight captions
* Subtle texture or background treatment

## Selective impact effects

Use sparingly for:

* Energy beams
* Rings
* Lightning
* Batarangs
* Projectiles
* Smoke
* Sparks
* Magic
* Impact flashes
* Brief camera shake
* Foreground separation
* Short parallax

Effects should be reusable templates with explicit parameters. Avoid unconstrained AI video generation in the normal pipeline.

## Anti-boredom system

The visual planner should measure:

* Time since visual change
* Consecutive static scenes
* Repeated motion preset
* Similarity between adjacent images
* Scene duration
* Narration intensity
* Section type
* Music energy
* Presence of a meaningful reveal

The system should vary movement and shot length, but important emotional moments may intentionally hold longer.

---

# 8. Music and Audio

## Narration

The uploaded, already-edited voice recording is authoritative.

Optional automatic editing should be:

* Non-destructive
* Disabled by default until validated
* Previewable through A/B comparison

Possible operations:

* Loudness normalization
* Light noise reduction
* Silence review
* Repeated-line detection
* Clipping detection
* Script mismatch detection
* Pickup markers

## Music

Use adaptive instrumental music that:

* Matches each major section’s mood
* Changes only at useful structural points
* Ducks beneath narration
* Avoids unnecessary intensity
* Does not compete with spoken words
* Can be replaced per section

Sound effects should be restrained and primarily connected to highlighted visual effects.

---

# 9. Automatic Quality and Repair Loop

User setting:

```text
Repair passes:
0 / 1 / 2 / 3 / 5
Default: 2
```

Each pass should test:

* Duplicate visual use
* Weak semantic match
* Wrong character
* Continuity confusion
* Unreadable or poorly removed text
* Bad crop
* Important subject cut off
* Static sequence
* Excessively repeated motion
* Abrupt music changes
* Music too loud
* Subtitle timing
* Black frames
* Missing media
* Audio clipping
* Render corruption

Repair rules:

1. Repair only affected scenes.
2. Preserve locked scenes.
3. Compare new and previous scene scores.
4. Keep the previous result if the repair is worse.
5. Stop early if improvement is negligible.
6. Never exceed the selected loop limit.
7. Save every pass for rollback.

---

# 10. Version 1 Scope

## Required

* Import script and narration
* Optional script factory
* Broad research mode
* Compact evidence ledger
* Comic library indexing
* Script-led search scope
* Steering keywords
* Panel and page retrieval
* Text-region avoidance or removal
* Automatic storyboard
* Comic-first render
* Adaptive pacing
* Adaptive music
* Configurable repair loops
* Simple scene cleanup
* Sequential video queue
* Separate script queue
* Final MP4, SRT, project manifest
* Resume after failure
* RTX 3070-compatible execution

## Explicit exclusions

* Full non-linear editor
* Full character animation
* Automatic lip sync
* Large generative video models
* Simultaneous multi-project GPU execution
* Public cloud service
* Mobile application
* Automatic upload to YouTube
* Mandatory ComfyUI
* Perfect universal comic panel detection
* Mandatory complex timeline export

## Optional complex export

The normal user never needs to use it.

When requested, export:

* OpenTimelineIO
* Referenced media
* Narration
* Music stems
* Captions
* Scene timing
* Separate layers when available
* Camera and effect metadata
* Resolve-compatible interchange where practical

OpenTimelineIO is designed to store editorial order, timing, and external media references rather than media itself, making it appropriate for this optional export layer. ([GitHub][13])

---

# 11. Development Roadmap

## Sprint 0 — Source Audit

**Goal:** Learn before building.

Inspect:

* MoneyPrinterTurbo
* BallonsTranslator
* StoryToolkitAI
* Revideo
* WhisperX
* OpenTimelineIO
* OpenCLIP
* SigLIP
* Qdrant
* SAM 2
* Depth Anything V2

Deliver:

* `TOOL_AUDIT.md`
* `REUSE_MATRIX.md`
* `LICENSE_MATRIX.md`
* `CAPABILITY_MATRIX.md`
* `ARCHITECTURE_CANDIDATES.md`
* Minimal proof scripts

Stop when every relevant capability is classified as reuse, adapter, study, replace, or reject.

## Sprint 1 — Project Foundation

Build:

* Pydantic schemas
* SQLite database
* Artifact hashing
* Project directories
* Stage state machine
* Logs
* Cancellation and resume
* CLI

Stop when a fake project can fail, resume, and complete deterministically.

## Sprint 2 — Comic Ingestion

Build:

* CBZ and image-folder support
* Read-only source policy
* Page extraction cache
* Stable IDs
* Thumbnails
* File-change detection
* Incremental updates

Stop when a changed issue reprocesses only changed material.

## Sprint 3 — Comic Understanding

Build:

* Panel candidates
* OCR and text masks
* Balloon/text regions
* Image descriptions
* Metadata
* Quality scores
* Full-page preservation

Stop when a test comic is searchable by OCR and metadata.

## Sprint 4 — Retrieval Benchmark

Compare:

* OpenCLIP models
* SigLIP models
* Full pages versus panels
* OCR versus embeddings
* Hybrid ranking

Stop when one reproducible retrieval configuration wins the labeled benchmark.

## Sprint 5 — Narration Alignment

Build:

* WhisperX adapter
* Script/audio comparison
* Word timing
* Section and beat segmentation
* Mismatch warnings

Stop when narration beats reliably map to timestamps.

## Sprint 6 — Automatic Storyboard

Build:

* Scope proposal
* Keyword steering
* Candidate retrieval
* Continuity scoring
* Reuse penalties
* Alternatives
* Scene JSON

Stop when a two-minute script produces a complete storyboard automatically.

## Sprint 7 — Text Removal and Derived Assets

Build:

* Clean-crop preference
* Text-mask generation
* Inpainting adapter
* Derived asset cache
* Failure fallback

Stop when source pages remain untouched and derived panels are reproducible.

## Sprint 8 — Renderer

Build:

* Native FFmpeg renderer
* Revideo proof-of-concept comparison
* Camera presets
* Transitions
* Subtitles
* Narration
* Music
* Draft and final profiles

Stop when the same project renders deterministically twice.

## Sprint 9 — Quality Repair Loop

Build:

* Preview analysis
* Scene scoring
* Repair planning
* Partial rerendering
* Pass comparison
* User-configurable maximum loops

Stop when an intentionally flawed test project is improved without rerendering unaffected scenes.

## Sprint 10 — Simple Editor

Build:

* Scene cards
* Panel replacement
* Alternative browser
* Crop and focus adjustment
* Motion preset selection
* Music replacement
* Scene lock
* Partial rerender

Stop when a user can fix a weak scene without using a professional editor.

## Sprint 11 — Script Factory

Build:

* Research modes
* Source ledger
* Framing discovery
* Outline
* Draft
* Verification
* Humanization
* Read-aloud checks
* Script queue

Stop when one topic produces a sourced, human-sounding script through stored repeatable stages.

## Sprint 12 — Optional Export

Build:

* OTIO
* Media package
* Captions
* Metadata
* Resolve interchange experiment

Stop when a test project opens externally with correct basic timing and media references.

## Sprint 13 — Packaging

Build:

* Tool detection
* Configuration UI
* Hardware profile
* Cache management
* Portable project support
* Personal Windows launcher
* Documentation

Public-release polish remains deferred.

---

# 12. Repository Structure

```text
comic-to-video/
├── AGENTS.md
├── README.md
├── SPRINTS.md
├── STATUS.md
├── SPRINT_STATE.json
├── pyproject.toml
├── package.json
│
├── apps/
│   ├── api/
│   ├── web/
│   └── cli/
│
├── core/
│   ├── projects/
│   ├── jobs/
│   ├── pipeline/
│   ├── artifacts/
│   ├── schemas/
│   ├── capabilities/
│   └── tool_registry/
│
├── research/
│   ├── providers/
│   ├── evidence/
│   ├── framing/
│   └── verification/
│
├── script_factory/
│   ├── briefing/
│   ├── outlining/
│   ├── drafting/
│   ├── fact_check/
│   ├── humanize/
│   └── read_aloud/
│
├── comic/
│   ├── ingest/
│   ├── extraction/
│   ├── panels/
│   ├── ocr/
│   ├── text_removal/
│   ├── embeddings/
│   ├── indexing/
│   └── retrieval/
│
├── video/
│   ├── alignment/
│   ├── beats/
│   ├── storyboard/
│   ├── motion/
│   ├── music/
│   ├── render/
│   ├── quality/
│   └── export/
│
├── adapters/
│   ├── ffmpeg/
│   ├── whisperx/
│   ├── ollama/
│   ├── qdrant/
│   ├── moneyprinterturbo/
│   ├── ballonstranslator/
│   ├── storytoolkitai/
│   ├── revideo/
│   ├── sam2/
│   ├── depth_anything/
│   └── opentimelineio/
│
├── vendor_studies/
├── experiments/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── adapter_contracts/
│   ├── retrieval_benchmark/
│   ├── golden_projects/
│   └── fixtures/
└── docs/
    ├── PRODUCT_SPEC.md
    ├── ARCHITECTURE.md
    ├── TOOL_AUDIT.md
    ├── REUSE_MATRIX.md
    ├── LICENSE_MATRIX.md
    ├── PROJECT_FORMAT.md
    ├── DATA_SCHEMAS.md
    ├── TEST_PLAN.md
    ├── THREAT_MODEL.md
    └── MODEL_COMPATIBILITY.md
```

---

# 13. Core `AGENTS.md` Rules

```text
PROJECT GOAL

Build a local-first automatic YouTube production system that creates
comic-first videos from scripts, narration, research, and an indexed comic
library.

SOURCE-STUDY RULE

Before implementing any significant capability:

1. Search the repository for existing work.
2. Inspect approved upstream projects that implement similar behavior.
3. Document their architecture, interfaces, limitations, license, tests,
   dependencies, and reusable concepts.
4. Prefer proven code or patterns when they preserve project capability.
5. Never adopt an upstream limitation merely to reduce implementation work.
6. Integrate through typed adapters where practical.
7. Copy or port code only after explicit license review.
8. Record the exact upstream repository and revision studied.
9. Add contract tests around every external integration.
10. Keep all external components replaceable.

MoneyPrinterTurbo is a major study source, not the application foundation.

PROJECT OWNERSHIP

This repository owns:

- Project state
- Job state
- Source provenance
- Script stages
- Comic index
- Storyboard
- Scene definitions
- Repair history
- User overrides
- Render history

No external application may become the source of truth.

SAFETY

- Comic libraries are read-only.
- Never overwrite narration, scripts, comics, or user media.
- Derived assets go into managed project or cache directories.
- Never delete user files during cleanup.
- Never run downloaded code without explicit provenance.
- Never silently ignore a failed stage.
- Never claim success without tests or artifact verification.

PIPELINE

- Every stage has typed input and output.
- Every expensive result is cached by content hash.
- Every stage is independently rerunnable.
- Changed inputs invalidate only dependent stages.
- A failed project must resume after restart.
- Video projects run sequentially in Version 1.
- No unbounded quality or agent loops.
- Default repair limit is two passes.

AI RULES

- AI output is a proposal, not project state, until validated and parsed.
- Use structured outputs.
- Preserve prompts and model identifiers.
- Separate evidence from interpretation.
- Never invent source provenance.
- Low-confidence visual matches receive alternatives.
- Do not use autonomous agents for file mutation or render-state control.

CODEX RUN PROCEDURE

1. Read AGENTS.md.
2. Read STATUS.md.
3. Read SPRINT_STATE.json.
4. Read the active sprint.
5. Inspect existing implementation.
6. Select the next incomplete task.
7. Implement only that task.
8. Run relevant tests.
9. Verify generated artifacts.
10. Update status and sprint state.
11. Record decisions and failures.
12. Stop at a stable checkpoint.
```

# First Codex Sprint

The first Codex run should perform **source study only**.

It should not begin building the full application.

Its deliverable is a defensible answer to:

> Which parts of MoneyPrinterTurbo, BallonsTranslator, StoryToolkitAI, Revideo, WhisperX, OpenTimelineIO, and related projects should be called, adapted, ported, recreated, or rejected—and why?

That approach preserves the power you want: the project benefits from years of existing work without becoming a patched-together fork or inheriting another application’s ceiling.

[1]: https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README-en.md "MoneyPrinterTurbo/README-en.md at main · harry0703/MoneyPrinterTurbo · GitHub"
[2]: https://github.com/dmMaze/BallonsTranslator/blob/dev/README_EN.md "BallonsTranslator/README_EN.md at dev · dmMaze/BallonsTranslator · GitHub"
[3]: https://github.com/octimot/StoryToolkitAI "GitHub - octimot/StoryToolkitAI: An editing tool that uses AI to transcribe, understand content and search for anything in your footage,  integrated with ChatGPT and other AI models · GitHub"
[4]: https://github.com/midrender/revideo "GitHub - midrender/revideo: Create Videos with Code · GitHub"
[5]: https://ffmpeg.org/ffmpeg-filters.html?utm_source=chatgpt.com "FFmpeg Filters Documentation"
[6]: https://github.com/m-bain/whisperX "GitHub - m-bain/whisperX: WhisperX:  Automatic Speech Recognition with Word-level Timestamps (& Diarization) · GitHub"
[7]: https://docs.ollama.com/api/introduction?utm_source=chatgpt.com "Introduction"
[8]: https://qdrant.tech/documentation/?utm_source=chatgpt.com "Qdrant Documentation"
[9]: https://github.com/facebookresearch/faiss?utm_source=chatgpt.com "facebookresearch/faiss: A library for efficient similarity ..."
[10]: https://github.com/mlfoundations/open_clip?utm_source=chatgpt.com "mlfoundations/open_clip: An open source implementation ..."
[11]: https://github.com/facebookresearch/sam2?utm_source=chatgpt.com "facebookresearch/sam2: The repository provides code for ..."
[12]: https://github.com/DepthAnything/Depth-Anything-V2?utm_source=chatgpt.com "DepthAnything/Depth-Anything-V2: [NeurIPS 2024 ..."
[13]: https://github.com/AcademySoftwareFoundation/OpenTimelineIO?utm_source=chatgpt.com "AcademySoftwareFoundation/OpenTimelineIO"
