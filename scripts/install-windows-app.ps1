param(
  [switch]$SkipFrontendBuild,
  [switch]$NoShortcut
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
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

Set-Location $RepoRoot

Assert-Command -Name "uv" -InstallHint "Install uv before preparing the local app."
Assert-Command -Name "npm" -InstallHint "Install Node.js/npm before building the frontend."

Push-Location $BackendDir
try {
  uv sync
} finally {
  Pop-Location
}

if (-not $SkipFrontendBuild) {
  Push-Location $FrontendDir
  try {
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
      npm install
    }
    npm run build
  } finally {
    Pop-Location
  }
}

if (-not $NoShortcut) {
  & (Join-Path $PSScriptRoot "create-desktop-shortcut.ps1")
}

Write-Host "SIALabs Local RAG Windows app setup complete."
Write-Host "Use the desktop shortcut or run:"
Write-Host ".\scripts\start-local-app.ps1"
