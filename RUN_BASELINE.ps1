param(
    [string]$RepositoryPath = 'D:\_Codex\Miller',
    [Parameter(Mandatory)] [string]$ComicPath,
    [Parameter(Mandatory)] [string]$ScriptPath,
    [Parameter(Mandatory)] [string]$NarrationPath,
    [Parameter(Mandatory)] [string]$OutputPath,
    [string]$ProjectId = 'baseline_project',
    [string]$ProjectName = 'Baseline video',
    [string]$MusicPath,
    [string]$SubtitlePath,
    [switch]$NoOcr,
    [int]$Width = 1920,
    [int]$Height = 1080,
    [int]$Fps = 30
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$destination = (Resolve-Path -LiteralPath $RepositoryPath).Path

function Invoke-CheckedNative {
    param([string]$Description, [scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Description failed with exit code $LASTEXITCODE." }
}


Push-Location $destination
try {
    $env:UV_DEFAULT_INDEX = 'https://pypi.org/simple'
    Invoke-CheckedNative 'Dependency installation' { uv sync --frozen --extra web --extra export --extra retrieval }
    $arguments = @(
        '--db', '.miller\miller.sqlite3',
        'baseline-video',
        '--project-id', $ProjectId,
        '--project-name', $ProjectName,
        '--workspace', '.miller\workspace',
        '--comic', $ComicPath,
        '--script', $ScriptPath,
        '--narration', $NarrationPath,
        '--output', $OutputPath,
        '--width', $Width,
        '--height', $Height,
        '--fps', $Fps
    )
    if ($MusicPath) { $arguments += @('--music', $MusicPath) }
    if ($SubtitlePath) { $arguments += @('--subtitles', $SubtitlePath) }
    if ($NoOcr) { $arguments += '--no-ocr' }
    Invoke-CheckedNative 'Baseline video run' { uv run miller @arguments }
}
finally {
    Pop-Location
}
