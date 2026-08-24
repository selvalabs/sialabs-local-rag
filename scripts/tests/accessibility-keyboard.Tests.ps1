Describe 'frontend keyboard accessibility' {
    It 'provides a skip link, target landmark and visible focus styles' {
        $app = Get-Content frontend/src/App.tsx -Raw
        $styles = Get-Content frontend/src/styles.css -Raw

        (Select-String -InputObject $app -Pattern 'skip-link') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $app -Pattern 'id="main-content"') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $styles -Pattern '\.skip-link:focus-visible') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $styles -Pattern 'button:focus-visible') | Should -Not -BeNullOrEmpty
    }
}
