param(
    [string]$RepositoryPath = 'D:\_Codex\Miller',
    [switch]$SkipVerify,
    [switch]$SkipCommit
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-CheckedNative {
    param(
        [Parameter(Mandatory)] [string]$Description,
        [Parameter(Mandatory)] [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}


if (-not (Test-Path -LiteralPath $RepositoryPath)) {
    throw "Miller was not found at $RepositoryPath"
}

$destination = (Resolve-Path -LiteralPath $RepositoryPath).Path
$sourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repairFiles = @(
    'uv.lock',
    'APPLY_TO_D_CODEX_MILLER.ps1',
    'VERIFY_MILLER.ps1',
    'RUN_MILLER.ps1',
    'RUN_BASELINE.ps1',
    'README.md',
    'HANDOFF.md',
    '.gitignore',
    'Repair-Miller-Install.ps1',
    'Repair-Miller-Install.cmd'
)
foreach ($repairFile in $repairFiles) {
    $repairSource = Join-Path $sourceRoot $repairFile
    if (Test-Path -LiteralPath $repairSource) {
        Copy-Item -LiteralPath $repairSource -Destination (Join-Path $destination $repairFile) -Force
    }
}
Write-Host 'Applied corrected installer and dependency metadata.'

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    throw 'uv is required. Re-run Install-Miller.cmd or install uv with Winget first.'
}

$lockPath = Join-Path $destination 'uv.lock'
if (-not (Test-Path -LiteralPath $lockPath)) {
    throw "uv.lock was not found at $lockPath"
}

$oldIndex = 'https://packages.applied-caas-gateway1.internal.api.openai.org/artifactory/api/pypi/pypi-public/simple'
$oldFiles = 'https://packages.applied-caas-gateway1.internal.api.openai.org/artifactory/api/pypi/pypi-public/packages/packages/'
$lockText = [System.IO.File]::ReadAllText($lockPath)
$fixedLock = $lockText.Replace($oldIndex, 'https://pypi.org/simple').Replace($oldFiles, 'https://files.pythonhosted.org/packages/')

if ($fixedLock -ne $lockText) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($lockPath, $fixedLock, $utf8NoBom)
    Write-Host 'Repaired uv.lock to use public PyPI.'
}

if ([System.IO.File]::ReadAllText($lockPath).Contains('applied-caas-gateway')) {
    throw 'uv.lock still contains an internal package URL. Use the corrected Miller release.'
}

$backupParent = Split-Path -Parent $destination
$backupRoot = Join-Path $backupParent '.Miller-backups'
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$env:UV_DEFAULT_INDEX = 'https://pypi.org/simple'

Push-Location $destination
try {
    Write-Host 'Resuming Miller dependency installation from public PyPI...'
    Invoke-CheckedNative 'Dependency installation' { uv sync --frozen --extra dev --extra web --extra export --extra retrieval }

    if (-not (Test-Path -LiteralPath 'config.toml')) {
        Invoke-CheckedNative 'Configuration initialization' { uv run miller config-init --path config.toml }
    }

    if (-not $SkipVerify) {
        Invoke-CheckedNative 'Ruff verification' { uv run ruff check . }
        Invoke-CheckedNative 'Mypy verification' { uv run mypy src }
        Invoke-CheckedNative 'Pytest verification' { uv run pytest }
        Invoke-CheckedNative 'Package build' { uv build }
        $capabilities = & uv run miller capabilities
        if ($LASTEXITCODE -ne 0) {
            throw "Capability detection failed with exit code $LASTEXITCODE."
        }
        $capabilities | Out-File `
            -LiteralPath (Join-Path $backupRoot "capabilities-$timestamp.json") -Encoding utf8
        Write-Host 'Verification passed.'
    }

    $git = Get-Command git -ErrorAction SilentlyContinue
    $isGit = [bool]($git -and (Test-Path -LiteralPath (Join-Path $destination '.git')))
    if ($isGit -and -not $SkipCommit) {
        Invoke-CheckedNative 'Git add' { git add --all }
        $changes = @(git status --porcelain)
        if ($changes.Count -gt 0) {
            Invoke-CheckedNative 'Git commit' { git commit -m 'feat: complete local Miller installation' }
        }
        else {
            Write-Host 'No repository changes to commit.'
        }
    }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Miller installation is complete.'
Write-Host "Location: $destination"
Write-Host "Launch:  $destination\RUN_MILLER.ps1"
