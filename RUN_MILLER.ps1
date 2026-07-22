param(
    [string]$RepositoryPath = 'D:\_Codex\Miller',
    [string]$DatabasePath = '.miller\miller.sqlite3',
    [int]$Port = 8765,
    [switch]$NoBrowser
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
    $arguments = @('--db', $DatabasePath, 'web', '--port', $Port)
    if ($NoBrowser) {
        $arguments += '--no-browser'
    }
    Invoke-CheckedNative 'Miller editor launch' { uv run miller @arguments }
}
finally {
    Pop-Location
}
