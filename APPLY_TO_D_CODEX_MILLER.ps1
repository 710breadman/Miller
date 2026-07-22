param(
    [string]$RepositoryPath = 'D:\_Codex\Miller',
    [bool]$InstallMissingTools = $true,
    [bool]$CreateDesktopShortcut = $true,
    [switch]$SkipVerify,
    [switch]$SkipCommit,
    [switch]$Launch
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$sourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'


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

function Refresh-CommandPath {
    $candidatePaths = @(
        (Join-Path $env:USERPROFILE '.local\bin'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links')
    )
    foreach ($candidate in $candidatePaths) {
        if ((Test-Path -LiteralPath $candidate) -and ($env:Path -notlike "*$candidate*")) {
            $env:Path = "$candidate;$env:Path"
        }
    }
}

function Install-WingetPackage {
    param(
        [Parameter(Mandatory)] [string]$Id,
        [Parameter(Mandatory)] [string]$DisplayName,
        [bool]$Required = $false
    )

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        if ($Required) {
            throw "$DisplayName is required and Winget is unavailable. Install $DisplayName manually."
        }
        Write-Warning "Winget unavailable; skipping optional $DisplayName installation."
        return $false
    }

    Write-Host "Installing $DisplayName through Winget ($Id)..."
    & winget install --id $Id --exact --source winget `
        --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        if ($Required) {
            throw "Winget could not install required package $DisplayName ($Id)."
        }
        Write-Warning "Winget could not install optional package $DisplayName ($Id)."
        return $false
    }
    Refresh-CommandPath
    return $true
}

if (-not (Test-Path -LiteralPath $RepositoryPath)) {
    New-Item -ItemType Directory -Path $RepositoryPath -Force | Out-Null
}
$destination = (Resolve-Path -LiteralPath $RepositoryPath).Path

Refresh-CommandPath
$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv -and $InstallMissingTools) {
    Install-WingetPackage -Id 'astral-sh.uv' -DisplayName 'uv' -Required $true | Out-Null
    $uv = Get-Command uv -ErrorAction SilentlyContinue
}
if (-not $uv) {
    throw 'uv is required. Install it, reopen PowerShell, then run this script again.'
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -and $InstallMissingTools) {
    Install-WingetPackage -Id 'Gyan.FFmpeg' -DisplayName 'FFmpeg' | Out-Null
}
if (-not (Get-Command tesseract -ErrorAction SilentlyContinue) -and $InstallMissingTools) {
    Install-WingetPackage -Id 'UB-Mannheim.TesseractOCR' -DisplayName 'Tesseract OCR' | Out-Null
}

$git = Get-Command git -ErrorAction SilentlyContinue
$isGit = [bool]($git -and (Test-Path -LiteralPath (Join-Path $destination '.git')))

$backupParent = Split-Path -Parent $destination
$backupRoot = Join-Path $backupParent '.Miller-backups'
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$backupArchive = Join-Path $backupRoot "pre-apply-$timestamp.zip"

$backupItems = @(
    Get-ChildItem -LiteralPath $destination -Force | Where-Object {
        $_.Name -notin @('.git', '.venv', '.miller', '.miller-backups', 'cache', 'projects', 'renders')
    }
)
if ($backupItems.Count -gt 0) {
    Compress-Archive -Path $backupItems.FullName -DestinationPath $backupArchive -CompressionLevel Fastest
    Write-Host "Backup created: $backupArchive"
}

if ($isGit) {
    Push-Location $destination
    try {
        $dirty = @(git status --porcelain)
        $dirty | Out-File -LiteralPath (Join-Path $backupRoot "git-status-$timestamp.txt") -Encoding utf8
        git diff --binary | Out-File -LiteralPath (Join-Path $backupRoot "working-$timestamp.patch") -Encoding utf8
        git diff --cached --binary | Out-File -LiteralPath (Join-Path $backupRoot "staged-$timestamp.patch") -Encoding utf8
        if ($dirty.Count -gt 0) {
            Invoke-CheckedNative 'Git stash' { git stash push --include-untracked -m "Miller pre-apply backup $timestamp" }
            Write-Host 'Existing changes were preserved in a Git stash.'
        }
        $branch = "assistant/full-local-foundation-$timestamp"
        Invoke-CheckedNative 'Git branch creation' { git switch -c $branch }
        Write-Host "Created branch: $branch"
    }
    finally {
        Pop-Location
    }
}

$excludeDirs = @(
    '.git', '.venv', '.mypy_cache', '.pytest_cache', '.ruff_cache',
    'dist', '__pycache__', '.miller-backups'
)
$robocopyArgs = @(
    $sourceRoot,
    $destination,
    '/E', '/COPY:DAT', '/DCOPY:DAT', '/R:1', '/W:1', '/NFL', '/NDL', '/NP',
    '/XD'
) + $excludeDirs

& robocopy @robocopyArgs | Out-Host
$robocopyCode = $LASTEXITCODE
if ($robocopyCode -gt 7) {
    throw "robocopy failed with exit code $robocopyCode"
}
Write-Host "Miller copied to $destination"

Push-Location $destination
try {
    $env:UV_DEFAULT_INDEX = 'https://pypi.org/simple'
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    New-Item -ItemType Directory -Path '.miller\workspace' -Force | Out-Null
    New-Item -ItemType Directory -Path 'renders' -Force | Out-Null

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

    if ($isGit -and -not $SkipCommit) {
        Invoke-CheckedNative 'Git add' { git add --all }
        $changes = @(git status --porcelain)
        if ($changes.Count -gt 0) {
            Invoke-CheckedNative 'Git commit' { git commit -m 'feat: implement local comic-to-video foundation' }
        }
        else {
            Write-Host 'No repository changes to commit.'
        }
    }
}
finally {
    Pop-Location
}

if ($CreateDesktopShortcut) {
    try {
        $desktop = [Environment]::GetFolderPath('Desktop')
        $shortcutPath = Join-Path $desktop 'Miller.lnk'
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = (Get-Command powershell.exe).Source
        $shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$destination\RUN_MILLER.ps1`""
        $shortcut.WorkingDirectory = $destination
        $shortcut.Description = 'Launch the Miller comic-to-video editor'
        $shortcut.Save()
        Write-Host "Desktop shortcut created: $shortcutPath"
    }
    catch {
        Write-Warning "Could not create the desktop shortcut: $($_.Exception.Message)"
    }
}

Write-Host ''
Write-Host 'Miller is ready.'
Write-Host "Location: $destination"
Write-Host "Verify:  $destination\VERIFY_MILLER.ps1"
Write-Host "Launch:  $destination\RUN_MILLER.ps1"

if ($Launch) {
    & powershell -ExecutionPolicy Bypass -File (Join-Path $destination 'RUN_MILLER.ps1')
}
