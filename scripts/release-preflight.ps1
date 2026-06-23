param(
  [string]$Version = "",
  [switch]$BuildPwaArchive,
  [switch]$AllowNonMain
)

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

function Assert-CleanGitTree {
  $Dirty = git status --porcelain
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

Invoke-Step "Frontend production build" {
  Push-Location (Join-Path $RepoRoot "frontend")
  try {
    npm run build
  } finally {
    Pop-Location
  }
}

if ($BuildPwaArchive) {
  Invoke-Step "PWA archive" {
    New-PwaArchive
  }
}

Write-Host "`nRelease preflight completed successfully." -ForegroundColor Green
