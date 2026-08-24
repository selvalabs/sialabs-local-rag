Describe "frontend Dockerfile" {
  BeforeAll {
    $dockerfile = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\Dockerfile")
  }

  It "copies the npm lockfile before npm ci" {
    if ($dockerfile -notmatch 'COPY package\.json package-lock\.json \./') {
      throw 'frontend Dockerfile must copy package-lock.json with package.json'
    }
  }

  It "uses npm ci for the locked dependency graph" {
    if ($dockerfile -notmatch 'RUN npm ci') {
      throw 'frontend Dockerfile must use npm ci'
    }
  }

  It "does not install from package.json alone" {
    if ($dockerfile -match 'COPY package\.json \./') {
      throw 'frontend Dockerfile must not copy package.json without package-lock.json'
    }
  }
}
