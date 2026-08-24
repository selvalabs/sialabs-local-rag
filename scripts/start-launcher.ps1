$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Get-Command python -ErrorAction SilentlyContinue) {
  python .\launcher\local_launcher.py
  exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
  py .\launcher\local_launcher.py
  exit $LASTEXITCODE
}

Write-Error "Python was not found. Install Python 3.12+ or add it to PATH."
