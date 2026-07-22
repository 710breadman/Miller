# Remaining implementation and validation plan

Most software framework work is complete. Remaining work depends on real local
assets, models, applications, or owner decisions.

## 1. Local acceptance

- Apply the release to `D:\_Codex\Miller`.
- Save the capability report and verify the RTX 3070 profile.
- Produce one 30–90 second no-AI baseline project.
- Repeat with OCR enabled and preserve the project as a golden local fixture.

## 2. Retrieval evidence

- Select a private, approved comic subset spanning styles, eras, actions, and mood.
- Label 100–300 narration queries with relevant pages/panels and hard negatives.
- Run the existing BM25 benchmark.
- Run pinned OpenCLIP and SigLIP 2 workers on the same exact corpus/config.
- Select the measured hybrid winner and record rollback/failure behavior.

## 3. Real model/tool proofs

- WhisperX: word alignment, mismatches, VRAM, model unload, representative narration.
- BallonsTranslator: external detector/inpaint process, masks, failures, license boundary.
- Revideo: same two-minute fixture as FFmpeg, startup, RAM/VRAM, sync, cancellation.
- Resolve: open exported timing/media using an installed supported version.

## 4. Subjective product acceptance

- Review pacing, image relevance, continuity shifts, crop safety, text cleanup,
  music changes, and repair quality.
- Tune defaults from measured projects rather than generic assumptions.

## 5. Distribution decision

- Select Miller's license.
- Generate final SBOM/notices and record model/weight terms.
- Decide whether any GPL tools remain user-installed or are excluded entirely.
