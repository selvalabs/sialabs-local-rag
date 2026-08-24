Describe 'Playwright E2E smoke' {
    It 'declares the local workspace smoke test' {
        $package = Get-Content frontend/package.json -Raw
        $config = Get-Content frontend/playwright.config.ts -Raw
        $spec = Get-Content frontend/e2e/workspace.spec.ts -Raw
        $lock = Get-Content frontend/package-lock.json -Raw

        (Select-String -InputObject $package -Pattern 'test:e2e') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $config -Pattern '127.0.0.1:5173') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $spec -Pattern 'Chat with the base') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $lock -Pattern '"@playwright/test": "1.62.1"') | Should -Not -BeNullOrEmpty
    }
}
