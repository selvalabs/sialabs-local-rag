Describe 'frontend dependency reproducibility' {
    It 'does not use floating latest dependency declarations' {
        $package = Get-Content frontend/package.json -Raw
        $lock = Get-Content frontend/package-lock.json -Raw

        (Select-String -InputObject $package -Pattern '"latest"') | Should -BeNullOrEmpty
        (Select-String -InputObject $lock -Pattern '"latest"') | Should -BeNullOrEmpty
    }
}
