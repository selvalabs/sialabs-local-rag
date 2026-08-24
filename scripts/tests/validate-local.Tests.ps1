Describe "validate-local.ps1" {
  BeforeAll {
    $scriptPath = Join-Path $PSScriptRoot "..\validate-local.ps1"
    $scriptText = Get-Content -Raw $scriptPath
  }

  It "checks the existing lockfile instead of refreshing dependencies" {
    if ($scriptText -notmatch '"lock", "--check"') {
      throw 'validate-local.ps1 must check the existing lockfile'
    }
    if ($scriptText -match '"lock", "--refresh"') {
      throw 'validate-local.ps1 must not refresh dependencies'
    }
  }

  It "runs Ruff in check-only mode" {
    if ($scriptText -notmatch '"run", "ruff", "check", "\."') {
      throw 'validate-local.ps1 must run Ruff check'
    }
    if ($scriptText -match '"run", "ruff", "check", "\.", "--fix"') {
      throw 'validate-local.ps1 must not run Ruff autofix'
    }
  }

  It "uses frozen backend dependencies" {
    if ($scriptText -notmatch '"sync", "--frozen", "--dev"') {
      throw 'validate-local.ps1 must use frozen backend dependencies'
    }
  }

  It "does not create or overwrite environment files during validation" {
    if ($scriptText -match 'Copy-Item\s+"\.env\.example"\s+"\.env"') {
      throw 'validate-local.ps1 must not create or overwrite .env'
    }
  }
}
