Describe 'EmbeddingGemma threshold calibration' {
    BeforeAll {
        $root = Join-Path $PSScriptRoot '..\..'
        $report = Get-Content -Raw (Join-Path $root 'backend\evaluation\threshold-sweep-embeddinggemma.json') | ConvertFrom-Json
        $settings = Get-Content -Raw (Join-Path $root 'backend\src\sialabs_local_rag\settings.py')
        $evidence = Get-Content -Raw (Join-Path $root 'docs\evidence\embeddinggemma-threshold-sweep.md')
    }

    It 'records a model-specific calibrated gate' {
        $report.embedding_provider | Should -Be 'ollama'
        $report.embedding_model | Should -Be 'embeddinggemma'
        $report.recommended_minimum_score | Should -Be 0.25
        $settings | Should -Match 'retrieval_min_score: float = Field\(default=0\.25'
    }

    It 'publishes the command and caveat with the evidence' {
        $evidence | Should -Match 'run_threshold_sweep.py'
        $evidence | Should -Match 'not a universal semantic threshold'
        (Test-Path (Join-Path $root 'backend\scripts\run_threshold_sweep.py')) | Should -Be $true
    }
}
