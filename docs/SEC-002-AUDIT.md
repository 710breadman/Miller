# SEC-002 dependency, model, data, SBOM, and license review

Audit date: 2026-07-29
Commit: `5a13895` (`SEC-001` head at audit time)
Evidence class: E3 for local Windows capability/vulnerability-scan observations recorded on this machine; upstream
license/legal conclusions remain declared, not a substitute for professional legal review.

This report extends `docs/INV-003-AUDIT.md` (2026-07-22) with the specific items it flagged as outstanding: a
current vulnerability scan, a machine-readable SBOM, an FFmpeg build/license record, and an explicit supply-chain
policy.

## Vulnerability scan (new since INV-003)

Ran `uv audit --locked` against the resolved dependency set. `uv audit` is an experimental built-in `uv` subcommand
(no new tool installed):

```text
$ uv audit --locked
Resolved 46 packages in 1ms
Found no known vulnerabilities and no adverse project statuses in 45 packages
exit code: 0
```

Machine-readable form (`--output-format json`, also experimental) confirms: `audited_packages: 45, vulnerabilities:
0, adverse_statuses: 0`. `uv` version at scan time: `0.11.25 (1fc7de7c4 2026-06-26 x86_64-pc-windows-msvc)`.

Caveats: `uv audit` is explicitly marked experimental by `uv` itself and its output schema may change; it reflects
the vulnerability database's state at scan time (2026-07-29) and must be re-run before release and periodically
thereafter, not treated as a one-time clearance.

## Software Bill of Materials (new since INV-003)

`docs/SBOM.json` is a machine-readable SBOM generated from `importlib.metadata` over every package actually
installed in this project's `.venv` (48 packages, including the `dev`/`web`/`export`/`retrieval` extras) — not a
transcription of `uv.lock`, but a direct read of installed package metadata, preferring each package's PEP 639
`License-Expression` field, falling back to the legacy `License` field, then a `License ::` trove classifier.

47 of 48 packages resolved a license this way; the one unresolved entry is `miller-video` itself (the project's own
package, whose license is the pending owner decision `OD-001`, not a third-party term).

Scanning the SBOM for any GPL-family license among these 48 *Python* dependencies found none (LGPL/GPL substring
match, excluding false positives). This confirms `EXTERNAL_PROJECTS.md`'s existing record that GPL-licensed
candidates (comic-text-detector, BallonsTranslator, StoryToolkitAI) are correctly kept external/concepts-only and
have not entered the installed dependency graph.

## FFmpeg build record (new since INV-003)

Ran `ffmpeg -version` on this machine. Full configuration is recorded verbatim below for reproducibility; the
license-relevant flags are `--enable-gpl --enable-version3`:

```text
ffmpeg version 8.1.1-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers
built with gcc 15.2.0 (Rev13, Built by MSYS2 project)
configuration: --enable-gpl --enable-version3 --enable-static --disable-w32threads --disable-autodetect
  --enable-cairo --enable-fontconfig --enable-iconv --enable-gnutls --enable-lcms2 --enable-libxml2 --enable-gmp
  --enable-bzlib --enable-lzma --enable-libsnappy --enable-zlib --enable-librist --enable-libsrt --enable-libssh
  --enable-libzmq --enable-avisynth --enable-libbluray --enable-libcaca --enable-libdvdnav --enable-libdvdread
  --enable-sdl2 --enable-libaribb24 --enable-libaribcaption --enable-libdav1d --enable-libdavs2
  --enable-libopenjpeg --enable-libquirc --enable-libuavs3d --enable-libxevd --enable-libzvbi --enable-liboapv
  --enable-libqrencode --enable-librav1e --enable-libsvtav1 --enable-libvvenc --enable-libwebp --enable-libx264
  --enable-libx265 --enable-libxavs2 --enable-libxeve --enable-libxvid --enable-libaom --enable-libjxl
  --enable-libsvtjpegxs --enable-libvpx --enable-mediafoundation --enable-libass --enable-frei0r
  --enable-libfreetype --enable-libfribidi --enable-libharfbuzz --enable-liblensfun --enable-libvidstab
  --enable-libvmaf --enable-libzimg --enable-amf --enable-cuda-llvm --enable-cuvid --enable-dxva2 --enable-d3d11va
  --enable-d3d12va --enable-ffnvcodec --enable-libvpl --enable-nvdec --enable-nvenc --enable-vaapi
  --enable-libshaderc --enable-vulkan --enable-libplacebo --enable-opencl --enable-libcdio --enable-openal
  --enable-libgme --enable-libmodplug --enable-libopenmpt --enable-libopencore-amrwb --enable-libmp3lame
  --enable-libshine --enable-libtheora --enable-libtwolame --enable-libvo-amrwbenc --enable-libcodec2
  --enable-libilbc --enable-libgsm --enable-liblc3 --enable-libopencore-amrnb --enable-libopus --enable-libspeex
  --enable-libvorbis --enable-ladspa --enable-libbs2b --enable-libflite --enable-libmysofa --enable-librubberband
  --enable-libsoxr --enable-chromaprint --enable-whisper
libavutil      60. 26.101 / 60. 26.101
libavcodec     62. 28.101 / 62. 28.101
libavformat    62. 12.101 / 62. 12.101
libavdevice    62.  3.101 / 62.  3.101
libavfilter    11. 14.101 / 11. 14.101
libswscale      9.  5.101 /  9.  5.101
libswresample   6.  3.101 /  6.  3.101
```

Build distribution: `gyan.dev` "full" Windows build (`ffmpeg version 8.1.1-full_build-www.gyan.dev`).

**License finding**: `--enable-gpl --enable-version3` means this specific FFmpeg build is licensed under **GPL
v3**, not LGPL — because it links GPL-only components (at minimum `libx264`, `libx265`, `libxvid`, `frei0r`, and
others enabled above are GPL-licensed encoders/filters). This is *not* currently a problem for Miller: Miller
invokes this binary as a separate subprocess (`shutil.which("ffmpeg")` + `subprocess.run([...])` in
`video/ffmpeg.py`), never links or bundles it, and subprocess invocation of a separately-installed GPL program does
not impose GPL obligations on the calling code. It *would* become relevant if a future release (`REL-001`/`REL-002`)
chooses to bundle this exact `ffmpeg.exe` inside a Miller installer: a bundled GPLv3 binary would carry a
source-offer and license-notice obligation for that binary specifically. Recorded here so that decision is made
knowingly rather than discovered late; see the new risk entry below.

## Notices

`docs/NOTICES.md` (new) consolidates: the Python dependency licenses from `docs/SBOM.json`, the external-tool
license records already in `EXTERNAL_PROJECTS.md` (Tesseract Apache-2.0, WhisperX BSD-2-Clause, Qdrant client and
OpenTimelineIO Apache-2.0, Revideo MIT, GPL-3.0 concepts-only-external items), and this FFmpeg build record.

## Model, weight, and dataset terms

Unchanged from `docs/INV-003-AUDIT.md`: no model weights or datasets are declared in `pyproject.toml` or `uv.lock`.
`AUD-001` (this session, prior sprint) added a pinned *specification* for an isolated WhisperX/stable-ts worker
environment (`src/miller/audio/worker/requirements.txt`) but did not install it or download any weights — exact
checkpoint hashes and training-data rights remain unverified and out of this report's scope (deferred to whichever
sprint actually installs and runs those workers).

## Supply-chain policy (new since INV-003)

1. All Python dependencies are resolved and pinned through `uv.lock`; no ad hoc `pip install` outside the lock.
2. `uv audit --locked` should be re-run before any release and on a regular cadence (e.g., alongside dependency
   bumps); a non-zero vulnerability count blocks release until triaged.
3. `docs/SBOM.json` should be regenerated whenever `uv.lock` changes materially (new/removed/major-bumped
   dependency), by re-running the generation approach recorded in this report (`importlib.metadata` over the
   synced `.venv`).
4. External tools invoked as subprocesses (FFmpeg, Tesseract, Ollama) are never bundled into the Python package;
   each remains a separately-installed system dependency with its own license terms recorded here and in
   `EXTERNAL_PROJECTS.md`.
5. Before any dependency is added, its license and the checklist in `EXTERNAL_PROJECTS.md`'s "Dependency acceptance
   checklist" apply; GPL-family candidates default to external/concepts-only per existing decisions (D-001 lineage;
   see `DECISIONS.md`).
6. If a future release bundles a GPL-licensed binary (e.g., a `gyan.dev` "full" FFmpeg build, see above), that
   specific binary's GPLv3 source-offer/notice obligations must be satisfied for that release; this does not extend
   to Miller's own Python code under the current subprocess-invocation architecture.

## Risks and owner decisions (delta from INV-003)

- **New**: if `REL-001`/`REL-002` bundle FFmpeg into an installer, the specific build's GPLv3 status
  (`--enable-gpl --enable-version3`) requires a source-offer/notice; an LGPL-only rebuild (`--disable-gpl`, dropping
  GPL-only encoders like libx264/libx265) is the likely mitigation if GPL obligations are undesirable for
  distribution.
- Resolved from INV-003: "run an approved vulnerability scan before release" — done this session (`uv audit`, 0
  findings); re-run before actual release since findings are point-in-time.
- Still open: exact model-weight/data manifests and hashes (blocked on `AUD-002`/model installation); Miller's own
  software license remains an owner decision (`OD-001`); public/commercial distribution intent remains an owner
  decision (`OD-008`).

## Next checkpoint

SBOM, notices, FFmpeg build/license record, and a current vulnerability scan are now on record. Remaining before
`REL-001`/`REL-002`: owner license decision (`OD-001`), exact model-weight/data manifests once model workers are
actually installed, and a fresh `uv audit` + FFmpeg-bundling decision at release time.
