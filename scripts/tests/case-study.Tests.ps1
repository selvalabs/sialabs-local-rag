Describe 'technical case study' {
    It 'documents architecture, evidence and security boundaries' {
        $caseStudy = Get-Content docs/CASE_STUDY.md -Raw

        (Select-String -InputObject $caseStudy -Pattern 'Architecture and choices') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $caseStudy -Pattern 'Security boundary') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $caseStudy -Pattern 'not a universal benchmark') | Should -Not -BeNullOrEmpty
    }
}
