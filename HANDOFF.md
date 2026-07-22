# Miller complete local handoff

This release is designed to be applied to `D:\_Codex\Miller`.

## Fastest path

Double-click `Install-Miller.cmd`, run `.\Install-Miller.cmd` from PowerShell, or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\APPLY_TO_D_CODEX_MILLER.ps1
```

The installer backs up existing work outside the Git worktree, preserves dirty Git
changes, creates a new branch when applicable, copies without deleting destination
files, installs locked dependency groups from public PyPI, runs 64 tests plus
lint/type/build checks, initializes safe local settings, writes a capability report,
and creates a desktop shortcut.

If installation previously stopped at dependency download, run
`Repair-Miller-Install.cmd` from this release to resume in place.

## Launch

```powershell
D:\_Codex\Miller\RUN_MILLER.ps1
```

## First video

Use `RUN_BASELINE.ps1` or the `baseline-video` CLI command. Start with a short
comic and narration and add `-NoOcr` for the first media-only acceptance run.

## Honest limits

Real OpenCLIP/SigLIP, WhisperX, BallonsTranslator, Revideo, Resolve, RTX 3070,
and subjective visual gates require the local machine and real approved media.
The project license also remains an owner decision.
