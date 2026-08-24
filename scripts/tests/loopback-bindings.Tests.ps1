Describe "local runtime bindings" {
  BeforeAll {
    $root = Join-Path $PSScriptRoot "..\.."
    $compose = Get-Content -Raw (Join-Path $root "docker-compose.yml")
    $setup = Get-Content -Raw (Join-Path $root "docs\LOCAL_SETUP.md")
    $backendReadme = Get-Content -Raw (Join-Path $root "backend\README.md")
    $startDev = Get-Content -Raw (Join-Path $root "scripts\start-dev.ps1")
    $frontendPackage = Get-Content -Raw (Join-Path $root "frontend\package.json")
  }

  It "publishes Compose services only on loopback" {
    foreach ($port in @('8000', '5173', '11434')) {
      $internalPort = $port -replace '^5173$', '8080'
      if ($compose -notmatch ('"127\.0\.0\.1:' + $port + ':' + $internalPort + '"')) {
        throw "Compose port $port must be published on 127.0.0.1"
      }
    }
  }

  It "documents backend development on loopback" {
    foreach ($content in @($setup, $backendReadme, $startDev)) {
      if ($content -match '0\.0\.0\.0') {
        throw 'Manual backend startup must not advertise a non-loopback bind'
      }
    }
  }

  It "keeps frontend development on loopback" {
    if ($frontendPackage -match 'vite --host 0\.0\.0\.0|preview --host 0\.0\.0\.0') {
      throw 'Frontend development scripts must bind to loopback'
    }
  }
}
