Describe 'frontend unit test runner' {
    It 'declares and runs Vitest' {
        $package = Get-Content frontend/package.json -Raw
        $lock = Get-Content frontend/package-lock.json -Raw

        (Select-String -InputObject $package -Pattern '"test": "vitest run') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $lock -Pattern '"vitest": "4.1.11"') | Should -Not -BeNullOrEmpty
        Test-Path frontend/src/api.test.ts | Should -Be $true
    }
}
