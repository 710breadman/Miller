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

## Human quality rubric, reviewer roles, and acceptance records (`QAE-001`)

This section finalizes the human-review side of the evaluation plan: who reviews, how a 1-5 score becomes an
accept/repair/reject decision, what happens when reviewers disagree, and how an E5 human-acceptance record is
stored so it cannot be silently edited later.

### Visual, audio, and narrative rubric

Score each dimension 1-5 (1 = fails the goal; 3 = acceptable with caveats; 5 = strong). The narrative/storyboard
dimensions were already defined above ("Storyboard and narrative"); the same 1-5 scale extends to visual and audio
review at the rendered-scene and whole-video level:

**Visual** (per scene, then whole video):
- crop/composition safety (no important subject cut off, no distracting frame);
- text-free cleanliness (no readable leftover lettering unless intentionally kept);
- motion/transition appropriateness for the beat's pacing and emotional weight;
- visual variety without distracting repetition (see reuse policy in `docs/PRODUCT_SPEC.md`);
- overall polish versus a professional video essay baseline.

**Audio** (whole video):
- narration clarity and levels (no clipping, no unintended silence);
- music-under-narration balance (present but never competing with speech);
- music transition smoothness at structural points;
- A/V sync throughout;
- absence of jarring or repeated audio artifacts.

**Narrative** (whole video): use the existing "Storyboard and narrative" criteria above, evaluated against the
*final rendered video*, not just the storyboard plan — a scene can score well on paper and still fail in the
render (bad crop, mistimed transition, audio clash).

### Reviewer roles

- **Primary reviewer**: the project owner, or an explicitly delegated reviewer the owner names. Has final authority
  to accept, request repair, or reject. Every E5 record requires exactly one primary reviewer.
- **Secondary reviewer** (optional, recommended for `REL-002`/release-gating acceptance and for any golden project
  used to tune defaults): an independent second person or an explicitly time-boxed second pass by the same person
  after a break, scoring blind to the primary reviewer's scores. Not required for routine per-project acceptance.
- **AI self-review** (advisory only, per the existing statistical rule below): automated `quality/` findings
  (`editorial.py`, `media.py`) may flag candidates for human attention and appear in the record's `automated_flags`
  field, but never substitute for a human score and never set `threshold_result` on their own.

No role may accept a risk involving public licensing, private corpus handling, destructive data migration, or a
permanent quality/capability tradeoff (see `RISKS.md` "Risk acceptance") — that remains the owner's alone even if a
delegated reviewer scored the video.

### Scoring thresholds

Compute `overall_score` as the unweighted mean of all scored dimensions for the relevant scope (scene-level scores
average into a video-level score; visual/audio/narrative each report their own sub-mean plus the combined mean).
Thresholds:

| `overall_score` | `threshold_result` | Meaning |
|---:|---|---|
| ≥ 4.0 | `accepted` | Ships as-is; no repair pass required. |
| ≥ 3.0 and < 4.0 | `needs_repair` | At least one dimension scored ≤ 2; route to the bounded repair loop (`quality/repair.py`, capped at the configured `repair_passes`) and re-review after. |
| < 3.0 | `rejected` | Fundamental problem (wrong footage, broken audio, factual/narrative error); do not repair-loop indefinitely — return to an earlier stage (storyboard/render) instead of iterating on quality passes. |

A single dimension scoring 1 ("fails the goal") forces at most `needs_repair` even if the mean would otherwise
round up to `accepted` — a strong overall average must never mask one broken dimension.

### Disagreement handling

When a secondary reviewer's scores differ from the primary reviewer's by more than 1 point on any dimension, or the
two reviewers land in different `threshold_result` bands:

1. Do not silently average and move on. Record both score sets in full.
2. The primary reviewer and secondary reviewer discuss the specific disagreeing dimension(s) against the rubric
   text above, not general impressions.
3. If they reach consensus, record the agreed score with both reviewers' names/roles and a one-line note on what
   changed their view.
4. If they do not reach consensus, the primary reviewer's score is authoritative for `threshold_result`, but the
   disagreement and the secondary reviewer's dissenting score are both preserved permanently in the record's
   `disagreement` field — never overwritten or deleted.
5. Recurring disagreement on the same dimension across multiple projects is a signal the rubric text itself is
   ambiguous and should be revised (open a `DOC` correction, do not keep re-litigating case by case).

### Immutable E5 acceptance records

An E5 record is content-addressed and write-once, matching the project's existing immutability conventions
(artifact IDs, document revision history): once written, a record is never edited or deleted, only superseded by a
new record referencing it (e.g. after a repair pass and re-review).

- Schema: `docs/schemas/e5-acceptance-record.schema.json`.
- Example (synthetic, illustrative only — not a real acceptance claim):
  `docs/schemas/e5-acceptance-record.example.json`.
- Verification: `docs/schemas/verify_e5_example.py` recomputes `content_hash` and `record_id` from the example
  record's own content and confirms they match the stored values byte-for-byte — concrete, runnable proof that the
  format is genuinely content-addressed, not just described as such. Run with
  `python docs/schemas/verify_e5_example.py`.
- Storage convention: one JSON file per record, named `e5_<sha256 of the record's canonical content>.json`, under
  the project's managed workspace (e.g. `<workspace>/projects/<project_id>/acceptance/`) — never under Git for
  records that reference private media; a redacted/hash-only copy may be committed for a golden project used as a
  release gate.
- `content_hash` is the SHA-256 of the record's canonical JSON (sorted keys, compact separators) with the two
  derived identity fields, `content_hash` and `record_id`, excluded. `record_id` is then `e5_<content_hash>` — the
  same tamper-evidence pattern Miller already uses for artifacts and documents (`artifacts.py`, `db.py`).
- A record that supersedes an earlier one sets `supersedes` to the earlier record's ID; the earlier record is never
  mutated in place.

## Statistical and reporting rules

- Never tune on the hidden acceptance subset and report it as generalization.
- Preserve per-query/per-page results, not only averages.
- Report regressions and failed cases.
- Compare against the current fallback.
- A new model is adopted only when benefit is material enough to justify operational cost.
- Human acceptance includes reviewer and date; AI self-review is advisory only.
