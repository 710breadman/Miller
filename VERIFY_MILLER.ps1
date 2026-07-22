param(
    [string]$RepositoryPath = 'D:\_Codex\Miller'
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
    Invoke-CheckedNative 'Dependency installation' { uv sync --frozen --extra dev --extra web --extra export --extra retrieval }
    Invoke-CheckedNative 'Ruff verification' { uv run ruff check . }
    Invoke-CheckedNative 'Mypy verification' { uv run mypy src }
    Invoke-CheckedNative 'Pytest verification' { uv run pytest }
    Invoke-CheckedNative 'Package build' { uv build }
    Invoke-CheckedNative 'Capability detection' { uv run miller capabilities }
}
finally {
    Pop-Location
}
