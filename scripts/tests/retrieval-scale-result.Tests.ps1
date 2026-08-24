Describe 'Retrieval scale benchmark result' {
    It 'has a versioned result with machine metadata and measured sizes' {
        $resultPath = Join-Path $PSScriptRoot '../../backend/benchmarks/results/retrieval-scale-local.json'
        Test-Path $resultPath | Should -Be $true
        $result = Get-Content $resultPath -Raw | ConvertFrom-Json

        $result.benchmark | Should -Be 'local-rag-retrieval-scale'
        $result.metadata.python_version | Should -Not -BeNullOrEmpty
        $result.metadata.platform | Should -Not -BeNullOrEmpty
        @($result.sizes).Count | Should -BeGreaterThan 0
        @($result.sizes | Where-Object { $_.chunks -eq 1000 }).Count | Should -BeGreaterThan 0
    }
}
