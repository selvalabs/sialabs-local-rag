Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$env:UV_DEFAULT_INDEX = "https://pypi.org/simple"
$env:NPM_CONFIG_REGISTRY = "https://registry.npmjs.org/"

function Invoke-Checked {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$WorkingDirectory,
    [Parameter(Mandatory=$true)][string]$Command,
    [string[]]$Arguments = @()
  )

  Write-Host ""
  Write-Host "==> $Name"

  Push-Location $WorkingDirectory
  try {
    & $Command @Arguments
    $exitCode = $LASTEXITCODE
  }
  finally {
    Pop-Location
  }

  if ($null -ne $exitCode -and $exitCode -ne 0) {
    throw "$Name failed with exit code $exitCode"
  }
}

Invoke-Checked "backend: uv lock check" "backend" "uv" @("lock", "--check")
Invoke-Checked "backend: uv sync frozen" "backend" "uv" @("sync", "--frozen", "--dev")
Invoke-Checked "backend: ruff check" "backend" "uv" @("run", "ruff", "check", ".")
Invoke-Checked "backend: pytest" "backend" "uv" @("run", "pytest")
Invoke-Checked "backend: mypy" "backend" "uv" @("run", "mypy", "src")
Invoke-Checked "backend: export OpenAPI" "backend" "uv" @("run", "python", "scripts/export_openapi.py", "openapi.json")

if (Test-Path "frontend/package-lock.json") {
  Invoke-Checked "frontend: npm ci" "frontend" "npm" @("ci")
} else {
  Invoke-Checked "frontend: npm install" "frontend" "npm" @("install")
}

Invoke-Checked "frontend: generate OpenAPI" "frontend" "npm" @("run", "generate:api")
Invoke-Checked "openapi: generated diff" "." "git" @("diff", "--exit-code", "--", "backend/openapi.json", "frontend/src/generated/openapi.ts")
Invoke-Checked "frontend: audit" "frontend" "npm" @("audit", "--audit-level=high")
Invoke-Checked "frontend: test" "frontend" "npm" @("run", "test")
Invoke-Checked "frontend: typecheck" "frontend" "npm" @("run", "typecheck")
Invoke-Checked "frontend: build" "frontend" "npm" @("run", "build")

if (Get-Command docker -ErrorAction SilentlyContinue) {
  Invoke-Checked "docker compose config" "." "docker" @("compose", "config")
} else {
  Write-Host "Docker not found; skipping docker compose config."
}

Write-Host ""
Write-Host "Validation finished successfully. Review git status and diff before committing."
git status --short
git diff --stat
