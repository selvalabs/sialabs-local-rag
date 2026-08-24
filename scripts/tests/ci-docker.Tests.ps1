Describe "CI Docker gate" {
  BeforeAll {
    $workflow = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\.github\workflows\ci.yml")
  }

  It "builds both application images" {
    if ($workflow -notmatch 'docker compose build backend frontend') {
      throw 'CI must build the backend and frontend Compose services'
    }
  }

  It "starts the application and checks both HTTP surfaces" {
    foreach ($required in @(
        'docker compose up -d backend frontend',
        'curl --fail --retry',
        'http://127\.0\.0\.1:8000/health',
        'http://127\.0\.0\.1:5173/'
      )) {
      if ($workflow -notmatch $required) {
        throw "CI Docker smoke gate is missing: $required"
      }
    }
  }

  It "prepares the bind-mounted data directory for the non-root backend" {
    $workflow | Should -Match 'mkdir -p data'
    $workflow | Should -Match 'chown -R 10001:10001 data'
  }

  It "cleans up the Compose stack" {
    if ($workflow -notmatch 'docker compose down -v') {
      throw 'CI Docker smoke gate must clean up its Compose stack'
    }
  }
}
