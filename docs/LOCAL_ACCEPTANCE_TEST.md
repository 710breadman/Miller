# First local acceptance test

Purpose: prove the current Miller baseline on the owner’s Windows machine without changing source media or claiming AI quality.

## Inputs

- current clean or safely preserved Miller checkout;
- 1 short comic folder or CBZ, preferably 6–20 pages;
- 30–90 second finished script;
- matching edited narration WAV;
- output folder outside source media;
- at least 10 GB free disk.

Do not use irreplaceable media for the first run. Do not commit the fixture.

## 1. Preserve local state

```powershell
git status --short --branch
git diff --binary > .miller\pre-acceptance-working.patch
git diff --cached --binary > .miller\pre-acceptance-staged.patch
```

Record repository path, workspace path, branch, and commit. Do not stash or switch branches automatically without understanding the current worktree.

## 2. Capability and quality gate

```powershell
uv --version
ffmpeg -version
tesseract --version
nvidia-smi
uv sync --frozen --extra dev --extra web --extra export --extra retrieval
uv run ruff check .
uv run mypy src
uv run pytest
uv build
uv run miller capabilities > .miller\acceptance-capabilities.json
uv run python scripts/validate_planning.py
```

Save exact failures. Missing optional tools are not core failure unless the test needs them.

## 3. Source manifest

Create SHA-256 hashes before processing:

```powershell
Get-FileHash -Algorithm SHA256 "X:\Path\To\Comic.cbz" | Format-List | Out-File .miller\fixture-source-before.txt
Get-FileHash -Algorithm SHA256 "X:\Path\To\narration.wav" | Format-List | Out-File -Append .miller\fixture-source-before.txt
```

For a folder, hash every source file and sort by path.

## 4. No-OCR run

Use a new project ID and non-existing output:

```powershell
uv run miller --db .miller\miller.sqlite3 baseline-video `
  --project-id acceptance_short_noocr `
  --workspace .miller\workspace `
  --comic "X:\Path\To\Comic.cbz" `
  --script "X:\Path\To\script.txt" `
  --narration "X:\Path\To\narration.wav" `
  --output ".miller\acceptance\short-noocr.mp4" `
  --no-ocr
```

Capture console output, elapsed time, peak RAM, disk growth, and `nvidia-smi` even if GPU is unused.

## 5. Verify artifact

```powershell
ffprobe -v error -show_streams -show_format -of json .miller\acceptance\short-noocr.mp4 > .miller\acceptance\short-noocr.ffprobe.json
Get-FileHash -Algorithm SHA256 .miller\acceptance\short-noocr.mp4 | Out-File .miller\acceptance\short-noocr.sha256.txt
```

Open the video and score: plays fully, narration present, no black/missing scenes, timing coverage, crops, obvious duplicate/relevance problems, and warnings.

## 6. OCR run

Repeat with a new project/output and OCR enabled. Record OCR availability, time increase, errors, and whether retrieval/scene choices visibly improve or worsen.

## 7. Source integrity

Repeat source hashes and compare byte-for-byte with before manifests. Any change is an automatic failure and escalation.

## 8. Recovery check

Start a separate disposable run, stop it during a bounded stage or render, restart Miller, and record behavior. The current direct baseline may not resume at stage granularity; record this honestly as evidence for `ARC-002` rather than trying to repair it during acceptance.

## Pass criteria

- quality gate passes or every environment failure is precisely documented;
- a valid MP4 is produced without overwriting;
- source hashes are unchanged;
- database/project documents and render manifest exist;
- errors and warnings are visible;
- manual review is recorded;
- no claim above E3 is made.

## Output

Write `.miller/acceptance/ENV-001-003-report.json` plus a short Markdown summary. Update `CURRENT_STATE.md`, `BLOCKERS.md`, `HANDOFF.md`, and `SPRINT_STATE.json` only after independent review.
