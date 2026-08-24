Describe 'OpenAPI contract gate' {
    It 'keeps the backend contract test present' {
        Test-Path backend/tests/test_openapi_contract.py | Should -Be $true
    }
}
