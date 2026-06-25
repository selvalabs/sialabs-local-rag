param(
  [int]$LauncherPort = 8765,
  [int]$FrontendPort = 4182,
  [switch]$NoBackend,
  [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
$FrontendDist = Join-Path $FrontendDir "dist"
$LauncherScript = Join-Path $PSScriptRoot "start-launcher.ps1"
$LauncherUrl = "http://127.0.0.1:$LauncherPort"
$FrontendUrl = "http://127.0.0.1:$FrontendPort"

function Test-HttpReachable {
  param([string]$Url)

  try {
    $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2 -UseBasicParsing
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
  } catch {
    return $false
  }
}

function Wait-HttpReachable {
  param(
    [string]$Url,
    [int]$TimeoutSeconds = 25
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpReachable -Url $Url) {
      return $true
    }
    Start-Sleep -Milliseconds 500
  }

  return $false
}

function Get-PythonCommand {
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return "python"
  }
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return "py"
  }
  throw "Python was not found. Install Python 3.12+ or add it to PATH."
}

function Start-LauncherProcess {
  if (Test-HttpReachable -Url "$LauncherUrl/health") {
    return
  }

  Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $LauncherScript) `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Minimized

  if (-not (Wait-HttpReachable -Url "$LauncherUrl/health" -TimeoutSeconds 30)) {
    throw "Launcher did not become reachable at $LauncherUrl."
  }
}

function Build-FrontendIfNeeded {
  $indexPath = Join-Path $FrontendDist "index.html"
  if (Test-Path $indexPath) {
    return
  }

  if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found. Install Node.js or build frontend/dist before starting the app."
  }

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

function Start-FrontendProcess {
  if (Test-HttpReachable -Url $FrontendUrl) {
    return
  }

  Build-FrontendIfNeeded
  $python = Get-PythonCommand

  Start-Process `
    -FilePath $python `
    -ArgumentList @("-m", "http.server", $FrontendPort.ToString(), "--bind", "127.0.0.1") `
    -WorkingDirectory $FrontendDist `
    -WindowStyle Minimized

  if (-not (Wait-HttpReachable -Url $FrontendUrl -TimeoutSeconds 20)) {
    throw "Frontend did not become reachable at $FrontendUrl."
  }
}

function Start-BackendThroughLauncher {
  if ($NoBackend) {
    return
  }

  Invoke-RestMethod `
    -Uri "$LauncherUrl/backend/start" `
    -Method Post `
    -ContentType "application/json" `
    -Body "{}" | Out-Null
}

Set-Location $RepoRoot
Start-LauncherProcess
Start-FrontendProcess
Start-BackendThroughLauncher

if (-not $NoOpen) {
  Start-Process $FrontendUrl
}

Write-Host "SIALabs Local RAG is running at $FrontendUrl"
Write-Host "Launcher is running at $LauncherUrl"
