Describe "backend Dockerfile" {
  BeforeAll {
    $dockerfile = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\backend\Dockerfile")
  }

  It "copies the backend lockfile before dependency installation" {
    if ($dockerfile -notmatch 'COPY pyproject\.toml uv\.lock README\.md \./') {
      throw 'backend Dockerfile must copy uv.lock with the project metadata'
    }
  }

  It "installs dependencies in frozen mode" {
    if ($dockerfile -notmatch 'uv sync --frozen --no-dev --no-install-project') {
      throw 'backend Dockerfile must install dependencies with uv sync --frozen'
    }
    if ($dockerfile -notmatch 'uv sync --frozen --no-dev(?! --no-install-project)') {
      throw 'backend Dockerfile must sync the project after copying source files'
    }
  }

  It "does not resolve dependencies without the lockfile" {
    if ($dockerfile -match 'uv sync --no-dev(?!\s+--frozen)') {
      throw 'backend Dockerfile must not run an unfrozen uv sync'
    }
  }
}
