Describe 'OpenAPI drift gate' {
    BeforeAll {
        $ci = Get-Content (Join-Path $PSScriptRoot '../../.github/workflows/ci.yml') -Raw
        $validate = Get-Content (Join-Path $PSScriptRoot '../validate-local.ps1') -Raw
    }

    It 'exports backend OpenAPI and checks generated artifacts in CI' {
        $ci | Should -Match 'scripts/export_openapi\.py openapi\.json'
        $ci | Should -Match 'npm run generate:api'
        $ci | Should -Match 'git diff --exit-code'
    }

    It 'runs the same generation and diff checks locally' {
        $validate | Should -Match 'scripts/export_openapi\.py'
        $validate | Should -Match 'frontend: generate OpenAPI'
        $validate | Should -Match 'openapi: generated diff'
    }
}
