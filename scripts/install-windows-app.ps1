param(
  [switch]$SkipFrontendBuild,
  [switch]$NoShortcut
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
$FrontendDist = Join-Path $FrontendDir "dist"
$BackendDir = Join-Path $RepoRoot "backend"

function Assert-Command {
  param(
    [string]$Name,
    [string]$InstallHint
  )

  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name was not found. $InstallHint"
  }
}

function Assert-PythonAvailable {
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return
  }
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return
  }
  throw "Python was not found. Install Python 3.12+ or add python/py to PATH before preparing the local app."
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

function Assert-FrontendBuildExists {
  $IndexPath = Join-Path $FrontendDist "index.html"
  if (-not (Test-Path $IndexPath)) {
    throw "Frontend build is missing at $IndexPath. Run the build or omit -SkipFrontendBuild."
  }
}

Set-Location $RepoRoot

Assert-PythonAvailable
Assert-Command -Name "uv" -InstallHint "Install uv before preparing the local app."
Assert-Command -Name "npm" -InstallHint "Install Node.js/npm before building the frontend."

Push-Location $BackendDir
try {
  Invoke-NativeChecked "backend dependency sync" "uv" @("sync")
} finally {
  Pop-Location
}

if ($SkipFrontendBuild) {
  Assert-FrontendBuildExists
} else {
  Push-Location $FrontendDir
  try {
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
      Invoke-NativeChecked "frontend dependency install" "npm" @("install")
    }
    Invoke-NativeChecked "frontend production build" "npm" @("run", "build")
  } finally {
    Pop-Location
  }
  Assert-FrontendBuildExists
}

if (-not $NoShortcut) {
  & (Join-Path $PSScriptRoot "create-desktop-shortcut.ps1")
  if (-not $?) {
    throw "Desktop shortcut creation failed."
  }
}

Write-Host "SIALabs Local RAG Windows app setup complete."
Write-Host "Use the desktop shortcut or run:"
Write-Host ".\scripts\start-local-app.ps1"
