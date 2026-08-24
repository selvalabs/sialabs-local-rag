Describe 'Validation documentation' {
    It 'documents the local and CI gates that are implemented' {
        $testing = Get-Content (Join-Path $PSScriptRoot '../../docs/TESTING.md') -Raw
        $validation = Get-Content (Join-Path $PSScriptRoot '../../docs/VALIDATION.md') -Raw

        $testing | Should -Match 'Vitest'
        $testing | Should -Match 'npm audit --audit-level=high'
        $testing | Should -Match 'OpenAPI'
        $testing | Should -Match 'Pester'
        $validation | Should -Match 'OpenAPI'
        $validation | Should -Match 'retrieval-scale-local.json'
    }
}
