# Local Windows setup

Target: detected owner checkout/workspace; current owner-reported repo path: `V:\AI\Miller`

## Automatic installation

From the extracted release folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\APPLY_TO_D_CODEX_MILLER.ps1
```

The script:

1. Creates managed workspace only when absent; never assumes a fixed repository path.
2. Backs up existing non-generated files.
3. Saves dirty Git status/diffs and stashes changes when applicable.
4. Creates a timestamped implementation branch.
5. Copies the overlay without mirroring or deleting destination files.
6. Installs the locked dev, web, export, and retrieval groups.
7. Runs Ruff, strict Mypy, all tests, package build, and capability detection.
8. Optionally commits and launches the editor.

## Manual verification

```powershell
cd V:\AI\Miller
.\VERIFY_MILLER.ps1
uv run miller capabilities
uv run miller --help
```

## First real acceptance project

Use a short comic and a 30–90 second edited narration. Start with `--no-ocr` to
prove the media flow, then repeat with Tesseract enabled. Use small dimensions
for the first run:

```powershell
uv run miller --db .miller\miller.sqlite3 baseline-video `
  --project-id first_acceptance `
  --workspace .miller\workspace `
  --comic "D:\Comics\Test.cbz" `
  --script "D:\Scripts\test.txt" `
  --narration "D:\Audio\test.wav" `
  --output "D:\Renders\test-baseline.mp4" `
  --no-ocr --width 1280 --height 720 --fps 30
```

Never point `--workspace` at the comic library.
