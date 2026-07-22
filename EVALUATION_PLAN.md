# Miller evaluation plan

## Evidence states

| State | Meaning | Required record |
|---|---|---|
| Automated pass | deterministic tests on synthetic/controlled fixtures | command, environment, logs, artifacts |
| Local hardware pass | run on target Windows/RTX hardware | capability manifest, timing, RAM/VRAM, failures |
| Quantitative corpus pass | measured against approved labels | dataset manifest, metrics, confidence intervals where useful |
| Human review pass | visual/audio/narrative review | rubric, reviewer, scores, comments, approved examples |
| Provisional | useful but missing one or more required evidence classes | exact missing gate |
| Fully accepted | all gates required by the roadmap item pass | immutable acceptance record and ADR |

## Evaluation assets

### Synthetic contract fixtures

Small generated images/audio/archives used for deterministic edge cases. They may prove software behavior but never comic understanding.

### Private local corpus

Owner-approved comics and narration stored outside Git. Git stores only schema, anonymized IDs when needed, hashes, coverage statistics, and reports without copyrighted images/dialogue.

### Golden projects

At least two:

1. **Acceptance short** — 30–90 seconds, varied layouts, fast iteration.
2. **Production representative** — 8–18 minutes according to owner decision, real narration, multiple issues/styles, music optional.

A third “hard cases” project should contain borderless panels, spreads, dense lettering, stylized fonts, low-quality scans, and continuity shifts.

## Major stage gates

### Ingestion and archive safety

- path traversal, Windows absolute path, backslash, duplicate normalized name;
- encrypted entries, compression bomb, excessive entry/total size;
- corrupt/truncated images and archives;
- source-before/source-after SHA-256 equality;
- changed issue reprocesses only affected pages;
- interruption and restart leave no authoritative partial record.

### Panel, text, balloon, and reading order

Metrics by page type:

- panel detection precision/recall/F1 and IoU thresholds;
- full-page/spread classification;
- text/balloon region precision/recall and mask IoU;
- reading-order exact match and Kendall/Spearman-style order error;
- failure buckets: borderless, nested, diagonal, splash, manga RTL, captions, sound effects.

Do not hide full-page fallback as a successful panel detection.

### OCR

- character error rate and word error rate where transcription is allowed;
- searchable-name/action retrieval impact;
- text-region coverage and hallucination rate;
- preprocessing variants: baseline, grayscale/contrast, upscale/sharpen, adaptive threshold, combinations only when separately tested;
- runtime, memory, language and typography breakdown.

### VLM observations

Use a structured rubric:

- object/character grounding;
- action, location, mood/emotion, costume/era, and composition accuracy;
- unsupported assertion rate;
- consistency across repeated runs/configurations;
- JSON validity and recovery;
- latency/VRAM and process unload;
- value added to retrieval versus OCR/metadata alone.

### Retrieval

Minimum 100–300 queries across:

- named character;
- visual action;
- location;
- costume/era;
- mood/emotional abstraction;
- composition/art style;
- dialogue/OCR;
- panel versus page;
- hard negatives and continuity restrictions.

Report Recall@1/5/10/20, MRR, nDCG@K, latency p50/p95, indexing time, index size, RAM/VRAM, and failure classes. Use the exact same labels and candidate corpus for all systems.

### Alignment

- word timestamp spot checks at beginning/middle/end;
- script-versus-spoken mismatch precision;
- drift, long pause, retake, clipped word, punctuation, and silence cases;
- fallback tier and uncertainty visibly recorded;
- GPU load/unload and CPU fallback.

### Storyboard and narrative

Human rubric per scene and whole sequence, 1–5:

- narration relevance;
- emotional/thematic support;
- character/continuity correctness;
- composition and crop safety;
- visual variety without distracting reuse;
- pacing and scene duration;
- motion/transition appropriateness;
- cleanup burden;
- strength of alternatives.

Compare baseline greedy selection against global optimizer using blind A/B when practical.

### Rendering

- expected stream types, codec, resolution, fps, duration, sample rate;
- A/V sync and no missing/black/frozen scenes;
- atomic output promotion and refusal to overwrite;
- cancellation cleanup and restart;
- repeated-run frame/audio tolerance;
- partial rerender changes only intended scenes;
- CPU versus NVENC speed/quality/size on same fixture;
- peak RAM/VRAM/disk and low-disk behavior.

### UI and recovery

- complete project without terminal use;
- clear current step/progress/error and exact recovery action;
- stale edit conflict does not lose work;
- lock/alternative/crop/motion/preview/undo/partial rerender tasks;
- keyboard/basic accessibility and narrow-window usability;
- crash browser/service/worker separately and recover.

### Release

- clean Windows user account/machine or VM;
- install, launch, repair, update, project create, baseline render, archive/export;
- no user media overwritten or removed;
- dependency/model/FFmpeg notices and SBOM;
- wheel and packaged artifact hashes;
- rollback/uninstall boundaries documented.

## Statistical and reporting rules

- Never tune on the hidden acceptance subset and report it as generalization.
- Preserve per-query/per-page results, not only averages.
- Report regressions and failed cases.
- Compare against the current fallback.
- A new model is adopted only when benefit is material enough to justify operational cost.
- Human acceptance includes reviewer and date; AI self-review is advisory only.
