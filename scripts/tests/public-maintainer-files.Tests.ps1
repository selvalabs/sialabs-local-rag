Describe 'public maintainer artifacts' {
    It 'includes contribution, changelog and third-party notice documents' {
        Test-Path CONTRIBUTING.md | Should -Be $true
        Test-Path CHANGELOG.md | Should -Be $true
        Test-Path THIRD_PARTY_NOTICES.md | Should -Be $true
    }
}
