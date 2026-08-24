Describe 'OpenAPI generated client' {
    It 'keeps the export and generation commands versioned' {
        $backendScript = Test-Path backend/scripts/export_openapi.py
        $package = Get-Content frontend/package.json -Raw
        $lock = Get-Content frontend/package-lock.json -Raw

        $backendScript | Should -Be $true
        (Select-String -InputObject $package -Pattern 'generate:api') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $lock -Pattern '"openapi-typescript": "7.13.0"') | Should -Not -BeNullOrEmpty
    }

    It 'commits the generated type module' {
        Test-Path frontend/src/generated/openapi.ts | Should -Be $true
    }
}
