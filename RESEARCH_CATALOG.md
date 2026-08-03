# Miller research catalog

Research refreshed: **2026-07-21**  
Use: source discovery and decision support. `EXTERNAL_PROJECTS.md` contains adopt/adapt/reject decisions.

## Research method

- Prefer official repositories, papers, model cards, documentation, and dataset terms.
- Record exact version or revision before implementation.
- Separate code license, model-weight license, and dataset license.
- Community reports are operational hints, never acceptance evidence.
- Recheck maintenance and licensing at the sprint that integrates a dependency.

## Comic and manga datasets

| Resource | Purpose | Terms / risk | Miller use |
|---|---|---|---|
| [Manga109](https://www.manga109.org/en/) and [annotations](https://github.com/manga109/public-annotations) | pages, panels, characters, text | base corpus is tightly controlled; do not redistribute; commercial use restrictions require care | benchmark reference and schema inspiration only after terms review |
| [Manga109-v2026](https://arxiv.org/abs/2607.00679) | corrected dialogue annotations | current 2026 annotation update; same corpus restrictions apply | OCR/speaker benchmark reference |
| [ICDAR 2025 Comics Competition](https://rrc.cvc.uab.es/?ch=28) / CoMix | panels, text, balloons, characters, reading order | competition/dataset terms must be reviewed separately | benchmark definitions and metrics |
| [ComicsPAP](https://arxiv.org/abs/2504.01079) | comic page analysis | verify data/code terms before use | modern multi-task evaluation reference |
| [ComicScene154](https://arxiv.org/abs/2505.02185) | comic scene understanding | research dataset; verify availability/terms | scene-boundary and relationship inspiration |

Private owner-approved fixtures remain authoritative for product acceptance.

## Comic analysis and OCR

| Project / paper | Current finding | Decision |
|---|---|---|
| [comic-text-detector](https://github.com/dmMaze/comic-text-detector) | comic text/balloon detector; GPL-3.0 | benchmark or external adapter; no source copy into permissive core |
| [BallonsTranslator](https://github.com/dmMaze/BallonsTranslator) | detector → OCR → mask → inpainting workflow; GPL and GUI coupling | external process proof only; adapt interface concepts |
| [MAGI](https://github.com/ragavsachdeva/magi) | panels, characters, text, order, clustering, speaker association | research restrictions; study and benchmark, reject as core dependency |
| [manga-ocr](https://github.com/kha-white/manga-ocr) | manga-focused Japanese OCR, Apache-2.0 | adopt as optional isolated engine after benchmark |
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | multilingual OCR/detection | benchmark as optional engine; keep heavy environment isolated |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) | simple local baseline | retain deterministic baseline; do not assume comic accuracy |
| Modern YOLO comic detectors | 2026 model repositories can provide panel/text/balloon weights | benchmark only; trace training-data rights separately from code/model license |

## Vision-language and embedding models

| Candidate | License / size direction | Miller recommendation |
|---|---|---|
| [Qwen3-VL-2B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct) | Apache-2.0 model card; small multimodal candidate | first structured VLM benchmark through external worker |
| [Qwen3-VL-Embedding-2B](https://huggingface.co/Qwen/Qwen3-VL-Embedding-2B) | Apache-2.0; multimodal retrieval candidate | benchmark if 8 GB VRAM and process overhead are acceptable |
| [SigLIP 2 NaFlex](https://huggingface.co/google/siglip2-base-patch16-naflex) | Apache-2.0; variable-aspect support | priority retrieval benchmark for comic panels/pages |
| [OpenCLIP](https://github.com/mlfoundations/open_clip) | MIT code; checkpoint datasets/licenses vary | retain broad benchmark family, pin exact checkpoint and terms |
| [SAM 2](https://github.com/facebookresearch/sam2) | optional segmentation | selected scenes only; not base dependency |
| [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) | Small code/weights permit broader use; larger weights have restrictions | optional selective parallax after v1 |

Hardware fit is an empirical gate. A model card or community VRAM report is not proof on RTX 3070 8 GB.

## Retrieval and storage

| Project | Finding | Decision |
|---|---|---|
| [Qdrant](https://github.com/qdrant/qdrant) | metadata-aware vector search, Apache-2.0 | current adapter remains supported; SQLite remains authority |
| [sqlite-vec](https://github.com/asg017/sqlite-vec) | compact SQLite vector extension, pre-1.0/current development | benchmark for simpler local deployment; do not adopt without migration/portability proof |
| BM25 | transparent lexical floor | mandatory baseline and fallback |
| Reciprocal-rank fusion | robust rank-level combination | benchmark against min-max weighted fusion |
| Cross-encoder/VLM reranking | can improve top-N semantic fit | bounded optional stage after retrieval candidates exist |

## Audio and video

| Project | Finding | Decision |
|---|---|---|
| [WhisperX](https://github.com/m-bain/whisperX) | local word-level alignment, BSD-2-Clause | primary pinned external worker after real narration proof |
| [stable-ts](https://github.com/jianfch/stable-ts) | timestamp stabilization/forced alignment alternatives | fallback benchmark; do not install in core environment |
| [FFmpeg](https://ffmpeg.org/documentation.html) | stable low-level render/probe/audio engine | mandatory native backend |
| [Revideo](https://github.com/redotvideo/revideo) | MIT TypeScript declarative video framework | compare on same fixture; optional only |
| [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | Apache-2.0 editorial interchange model | retain optional export adapter |
| [StoryToolkitAI](https://github.com/octimot/StoryToolkitAI) | transcript/story/Resolve ideas; GPL-3.0 | concepts only; no core code reuse |

## Annotation and review tools

| Tool | Use | Decision |
|---|---|---|
| [CVAT](https://github.com/cvat-ai/cvat) | rich image annotation | optional for complex dataset work; too heavy for ordinary Miller labeling |
| Miller label UI | relevance, panels, reading order, OCR correction, human quality | build a small task-specific local tool so labels share Miller IDs and provenance |

## Agent orchestration research conclusion

Miller does not need LangGraph, CrewAI, AutoGen, Prefect, Temporal, n8n, or Node-RED for v1. The current SQLite state machine is easier to audit and recover. Agents prepare proposals and bounded code changes; core state transitions remain deterministic.

## Research update triggers

Refresh the relevant catalog entry when:

- a sprint selects or pins a dependency;
- the latest upstream release is older/newer than the audited revision;
- a license or model card changes;
- Windows/CUDA support changes;
- a benchmark rejects the current candidate;
- a security advisory affects a dependency.
