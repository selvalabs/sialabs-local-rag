Describe "index health UI contract" {
  BeforeAll {
    $api = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\api.ts")
    $types = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\types.ts")
    $app = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\App.tsx")
  }

  It "has typed status and reset API methods" {
    foreach ($name in @('IndexStatusResponse', 'IndexResetResponse', 'getIndexStatus', 'resetIndex')) {
      if (($types + $api) -notmatch $name) { throw "Missing index health contract: $name" }
    }
  }

  It "renders index state and exposes reset when reindex is required" {
    foreach ($name in @('indexStatus', 'reindex_required', 'resetIndex', 'Index health')) {
      if ($app -notmatch [regex]::Escape($name)) { throw "Missing index health UI behavior: $name" }
    }
  }
}
