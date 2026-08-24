Describe 'Public security claims' {
    It 'does not claim security workflows that are absent from the repository' {
        $readme = Get-Content (Join-Path $PSScriptRoot '../../README.md') -Raw
        $caseStudy = Get-Content (Join-Path $PSScriptRoot '../../docs/CASE_STUDY.md') -Raw

        $readme | Should -Not -Match 'CodeQL/secret-scan workflow|SBOM artifact workflow'
        $caseStudy | Should -Not -Match 'CodeQL/secret-scan workflow|SBOM artifact workflow'
    }
}
