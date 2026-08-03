# Third-party notices

Generated: 2026-07-29 for `SEC-002`. This is a repository record of declared/observed license terms, not a
substitute for professional legal review, and not yet a release-ready notices file (full license texts are not
reproduced here; see each package's own distribution for that).

## Python dependencies (installed in this project's `.venv`)

Source: `docs/SBOM.json`, generated from `importlib.metadata` over 48 actually-installed packages (including the
`dev`/`web`/`export`/`retrieval` extras). All resolved licenses below are permissive (MIT/BSD/Apache-2.0/MPL-2.0/PSF
family); none are GPL/LGPL. `miller-video` is Miller's own package and is excluded (its license is the pending
owner decision `OD-001`).

| Package | Version | License |
|---|---|---|
| annotated-doc | 0.0.4 | MIT |
| annotated-types | 0.7.0 | MIT License |
| anyio | 4.14.1 | MIT |
| ast_serialize | 0.6.0 | MIT |
| build | 1.5.0 | MIT |
| certifi | 2026.6.17 | MPL-2.0 |
| click | 8.4.2 | BSD-3-Clause |
| colorama | 0.4.6 | BSD License |
| fastapi | 0.139.0 | MIT |
| grpcio | 1.81.1 | Apache-2.0 |
| h11 | 0.16.0 | MIT |
| h2 | 4.3.0 | MIT |
| hpack | 4.2.0 | MIT |
| httpcore | 1.0.9 | BSD-3-Clause |
| httpcore2 | 2.5.0 | BSD-3-Clause |
| httpx | 0.28.1 | BSD-3-Clause |
| httpx2 | 2.5.0 | BSD-3-Clause |
| hyperframe | 6.1.0 | MIT |
| idna | 3.18 | BSD-3-Clause |
| iniconfig | 2.3.0 | MIT |
| librt | 0.12.0 | MIT |
| mypy | 2.1.0 | MIT |
| mypy_extensions | 1.1.0 | MIT |
| numpy | 2.3.5 | BSD-3-Clause |
| OpenTimelineIO | 0.18.1 | Apache-2.0 |
| packaging | 26.2 | Apache-2.0 OR BSD-2-Clause |
| pathspec | 1.1.1 | MPL-2.0 |
| pillow | 12.3.0 | MIT-CMU |
| pip | 22.3 | MIT |
| pluggy | 1.6.0 | MIT |
| portalocker | 3.2.0 | BSD-3-Clause |
| protobuf | 7.35.1 | BSD-3-Clause |
| pydantic | 2.13.4 | MIT |
| pydantic_core | 2.46.4 | MIT |
| Pygments | 2.20.0 | BSD-2-Clause |
| pyproject_hooks | 1.2.0 | MIT License |
| pytest | 9.1.1 | MIT |
| pywin32 | 312 | PSF |
| qdrant-client | 1.18.0 | Apache-2.0 |
| ruff | 0.15.20 | MIT |
| setuptools | 65.5.0 | MIT License |
| starlette | 1.3.1 | BSD-3-Clause |
| truststore | 0.10.4 | MIT |
| typing-inspection | 0.4.2 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| urllib3 | 2.7.0 | MIT |
| uvicorn | 0.50.0 | BSD-3-Clause |

(`numpy`, `h2`, and `hyperframe` embed full BSD/MIT license text in their package metadata rather than a short SPDX
expression; the short form above matches that text's license family. See `docs/SBOM.json` for the raw metadata.)

## External tools invoked as subprocesses (never bundled)

| Tool | License | Notes |
|---|---|---|
| FFmpeg / FFprobe | **GPL v3** (this build) | `gyan.dev` "full" Windows build; `--enable-gpl --enable-version3`. See `docs/SEC-002-AUDIT.md` for the full build configuration and bundling caveat. |
| Tesseract | Apache-2.0 | OCR baseline/fallback. |
| WhisperX | BSD-2-Clause | Not installed; isolated worker environment spec only (`AUD-001`). |
| stable-ts | MIT | Not installed; isolated worker environment spec only (`AUD-001`). |
| Ollama | MIT | Local model gateway; invoked over its HTTP API, not bundled. |

## External projects studied or benchmarked, not adopted as dependencies

See `EXTERNAL_PROJECTS.md` for the full table and rationale. GPL-3.0 candidates (comic-text-detector,
BallonsTranslator, StoryToolkitAI) are recorded as **external/concepts-only**: Miller studies their design but does
not copy their code or depend on them at runtime, confirmed by this session's SBOM scan finding no GPL-family
license among the 48 installed Python packages.

## Models, weights, and datasets

No model weights or datasets are declared as dependencies. See `RESEARCH_CATALOG.md`, `EXTERNAL_PROJECTS.md`, and
`docs/upstream-lock.json` for candidate terms; none are installed or downloaded as of this report.
