param(
    [string]$RepositoryPath = 'D:\_Codex\Miller',
    [switch]$SkipVerify,
    [switch]$SkipCommit,
    [switch]$Launch
)

$script = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'APPLY_TO_D_CODEX_MILLER.ps1'
& $script -RepositoryPath $RepositoryPath -SkipVerify:$SkipVerify -SkipCommit:$SkipCommit -Launch:$Launch
exit $LASTEXITCODE
