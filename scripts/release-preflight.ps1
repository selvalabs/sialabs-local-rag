param(
  [string]$Version = "",
  [switch]$BuildPwaArchive,
  [switch]$AllowNonMain
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Invoke-Step {
  param(
    [string]$Name,
    [scriptblock]$Command
  )

  Write-Host "`n=== $Name ===" -ForegroundColor Cyan
  & $Command
}

function Invoke-NativeChecked {
  param(
    [string]$Name,
    [string]$Command,
    [string[]]$Arguments = @()
  )

  & $Command @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed with exit code $LASTEXITCODE."
  }
}

function Assert-CleanGitTree {
  $Dirty = git status --porcelain
  if ($LASTEXITCODE -ne 0) {
    throw "Could not inspect the git working tree."
  }
  if ($Dirty) {
    Write-Host $Dirty
    throw "Working tree is not clean. Commit, stash or discard changes before packaging."
  }
}

function Assert-MainBranch {
  if ($AllowNonMain) {
    return
  }

  $Branch = git branch --show-current
  if ($LASTEXITCODE -ne 0) {
    throw "Could not determine the current git branch."
  }
  if ($Branch -ne "main") {
    throw "Installer preflight must run from main. Current branch: $Branch. Use -AllowNonMain only for dry runs."
  }
}

function Assert-Version {
  if (-not $Version) {
    return
  }

  if ($Version -notmatch '^v\d+\.\d+\.\d+(-[A-Za-z0-9.-]+)?$') {
    throw "Version must look like v0.3.0 or v0.4.0-rc.1. Received: $Version"
  }
}

function Assert-MainSynchronized {
  if ($AllowNonMain) {
    return
  }

  Invoke-NativeChecked "git fetch origin/main" "git" @("fetch", "origin", "main", "--tags", "--quiet")

  $Head = git rev-parse HEAD
  if ($LASTEXITCODE -ne 0) {
    throw "Could not resolve HEAD."
  }
  $OriginMain = git rev-parse origin/main
  if ($LASTEXITCODE -ne 0) {
    throw "Could not resolve origin/main."
  }

  if ($Head.Trim() -ne $OriginMain.Trim()) {
    throw "Local main is not synchronized with origin/main. Fetch/pull the latest clean main before packaging."
  }
}

function Assert-VersionTagPointsToHead {
  if ($AllowNonMain -or -not $Version) {
    return
  }

  $TagCommit = git rev-list -n 1 $Version 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $TagCommit) {
    throw "Release tag $Version does not exist. Create the version tag on the validated main commit before packaging."
  }

  $Head = git rev-parse HEAD
  if ($LASTEXITCODE -ne 0) {
    throw "Could not resolve HEAD for release tag validation."
  }

  if ($TagCommit.Trim() -ne $Head.Trim()) {
    throw "Release tag $Version does not point to the current HEAD."
  }
}

function Invoke-DeterministicEvaluation {
  param([ValidateSet("dense", "hybrid")][string]$Mode)

  Push-Location (Join-Path $RepoRoot "backend")
  try {
    Invoke-NativeChecked "deterministic RAG evaluation ($Mode)" "uv" @(
      "run",
      "python",
      "-m",
      "sialabs_local_rag.evaluation",
      "--provider",
      "hash",
      "--mode",
      $Mode
    )
  } finally {
    Pop-Location
  }
}

function New-PwaArchive {
  if (-not $Version) {
    throw "-Version is required when using -BuildPwaArchive."
  }

  $FrontendDist = Join-Path $RepoRoot "frontend/dist"
  if (-not (Test-Path $FrontendDist)) {
    throw "frontend/dist does not exist. Run the frontend build before creating the archive."
  }

  $ReleaseDir = Join-Path $RepoRoot "dist/release/$Version"
  New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

  $ArchivePath = Join-Path $ReleaseDir "sialabs-local-rag-pwa-$Version.zip"
  if (Test-Path $ArchivePath) {
    Remove-Item $ArchivePath -Force
  }

  Compress-Archive -Path (Join-Path $FrontendDist "*") -DestinationPath $ArchivePath -Force
  Write-Host "Created PWA archive: $ArchivePath" -ForegroundColor Green
}

Invoke-Step "Git preflight" {
  Assert-Version
  Assert-CleanGitTree
  Assert-MainBranch
  git status -sb
  git log --oneline --decorate -3
}

Invoke-Step "Local validation suite" {
  & (Join-Path $RepoRoot "scripts/validate-local.ps1")
}

Invoke-Step "Deterministic RAG evaluation: dense" {
  Invoke-DeterministicEvaluation "dense"
}

Invoke-Step "Deterministic RAG evaluation: hybrid" {
  Invoke-DeterministicEvaluation "hybrid"
}

Invoke-Step "Frontend production build" {
  Push-Location (Join-Path $RepoRoot "frontend")
  try {
    Invoke-NativeChecked "frontend production build" "npm" @("run", "build")
  } finally {
    Pop-Location
  }
}

Invoke-Step "Release source verification" {
  Assert-CleanGitTree
  Assert-MainSynchronized
  Assert-VersionTagPointsToHead
}

if ($BuildPwaArchive) {
  Invoke-Step "PWA archive" {
    New-PwaArchive
  }
}

Write-Host "`nRelease preflight completed successfully." -ForegroundColor Green
