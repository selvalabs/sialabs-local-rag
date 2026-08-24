Describe 'frontend quality gates' {
    BeforeAll {
        $ci = Get-Content (Join-Path $PSScriptRoot '../../.github/workflows/ci.yml') -Raw
        $validate = Get-Content (Join-Path $PSScriptRoot '../validate-local.ps1') -Raw
    }

    It 'runs Vitest and high-severity dependency audit in CI' {
        $ci | Should -Match 'npm run test'
        $ci | Should -Match 'npm audit --audit-level=high'
    }

    It 'runs the same frontend gates locally' {
        $validate | Should -Match 'frontend: audit'
        $validate | Should -Match 'npm.*audit.*--audit-level=high'
        $validate | Should -Match 'frontend: test'
        $validate | Should -Match 'npm.*run.*test'
    }
}
