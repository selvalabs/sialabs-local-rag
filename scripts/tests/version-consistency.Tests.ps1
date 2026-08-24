Describe "release version consistency" {
  BeforeAll {
    $root = Join-Path $PSScriptRoot "..\.."
    $files = @(
      (Join-Path $root "backend\pyproject.toml"),
      (Join-Path $root "backend\uv.lock"),
      (Join-Path $root "backend\src\sialabs_local_rag\__init__.py"),
      (Join-Path $root "backend\src\sialabs_local_rag\main.py"),
      (Join-Path $root "backend\openapi.json"),
      (Join-Path $root "frontend\package.json"),
      (Join-Path $root "frontend\package-lock.json")
    )
    $target = '0.3.1'
  }

  It "uses the same product version in runtime and package metadata" {
    foreach ($file in $files) {
      $content = Get-Content -Raw $file
      if ($content -notmatch [regex]::Escape($target)) {
        throw "$file must contain version $target"
      }
    }
  }

  It "does not use the stale v0.4.0 release examples" {
    foreach ($path in @(
        (Join-Path $root "docs\INSTALLERS.md"),
        (Join-Path $root "docs\RELEASE_READINESS.md"),
        (Join-Path $root "installer\windows\README.md")
      )) {
      if ((Get-Content -Raw $path) -match 'v0\.4\.0') {
        throw "$path still references the stale v0.4.0 release example"
      }
    }
  }
}
