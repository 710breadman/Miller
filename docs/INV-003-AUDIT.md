# INV-003 dependency, data, and license audit

Audit date: 2026-07-22  
Commit: `954390b82e077852439636ef7e6aadff03341615`  
Evidence class: E3 for local Windows capability observations; dependency/license conclusions remain declared or unverified unless stated.

## Python/runtime inventory

Declared in `pyproject.toml`: Python `>=3.11`; runtime `pydantic>=2.10,<3`, `pillow>=11,<13`; optional development `build>=1.2`, `mypy>=1.15`, `pytest>=8.3`, `ruff>=0.11`; optional web `fastapi>=0.139.0`, `uvicorn>=0.50.0`; optional export `opentimelineio>=0.18.1`; optional retrieval `qdrant-client>=1.18.0`, `numpy>=1.26,<2.4`; dev group `httpx2>=2.5.0`.

Pinned by `uv.lock`: annotated-doc 0.0.4; annotated-types 0.7.0; anyio 4.14.1; build 1.5.0; fastapi 0.139.0; httpx 0.28.1; httpx2 2.5.0; mypy 2.1.0; numpy 2.3.5; opentimelineio 0.18.1; pillow 12.3.0; pydantic 2.13.4; pytest 9.1.1; qdrant-client 1.18.0; ruff 0.15.20; uvicorn 0.50.0. These are lock resolutions, not a claim that every package is installed on every machine.

## Executables and local capability

Recorded local probe: Python 3.11.0, FFmpeg/FFprobe 8.1.1, NVIDIA GeForce RTX 3070 with 8192 MB, Ollama 0.32.1, Node 24.18.0, Tesseract 5.4.0.20240606. Qdrant health endpoint was unavailable at probe time. The repository CI declares Ubuntu/Windows and Python 3.11/3.13 matrices, but CI configuration is not proof of a completed run.

Local Ollama inventory observed during ENV-001: `gemma4:12b`, `gemma4:26b`, `gemma4:e4b`, `qwen3-vl:8b-instruct`, `qwen2.5-coder:7b`, and `qwen3-embedding:0.6b`. This is machine-local, not a repository dependency or distribution commitment.

## Models, weights, datasets, and media

No model weights or datasets are declared in `pyproject.toml` or `uv.lock`. Model candidates and terms are documented in `RESEARCH_CATALOG.md`, `EXTERNAL_PROJECTS.md`, and `docs/upstream-lock.json`; exact checkpoint hashes, downloaded-weight provenance, and training-data rights remain unverified. The repository treats comics, scripts, narration, and user media as read-only. ENV-001 artifacts use managed synthetic script/audio plus a local derived image fixture; no media is committed by this audit.

## License and source boundaries

Repository-owned Miller software license remains an owner decision (`README.md`, `docs/OWNER_DECISIONS.md`). Existing records identify Tesseract as Apache-2.0, WhisperX as BSD-2-Clause, Qdrant client and OpenTimelineIO as Apache-2.0, Revideo as MIT, and GPL components such as comic-text-detector, BallonsTranslator, and StoryToolkitAI as external/concepts-only. These are repository records, not a replacement for current upstream license review. FFmpeg licensing depends on build configuration/codecs and requires release-specific notices. OpenCLIP checkpoint terms vary. Dataset and model-weight rights are separate from code licenses and remain open.

## Risks and owner decisions

- Lockfile versions can drift from current upstream security advisories; run an approved vulnerability scan before release.
- Optional model weights, checkpoints, and datasets lack complete hash/terms manifests.
- FFmpeg build/codec notices and final SBOM are not complete.
- Miller public/commercial distribution intent and software license are unresolved.
- Owner must approve private corpus policy, model downloads, and any public fixture.
- Qdrant is optional and currently not health-verified.

## Next checkpoint

`INV-003` audit artifact complete for declared inventory and known local probe. Remaining proof: owner/license decisions, exact model-weight/data manifests, SBOM/notices, and current vulnerability scan. Next sprint: `SEC-002` only after Codex review and state advancement; keep `ENV-002` blocked on approved fixture.
