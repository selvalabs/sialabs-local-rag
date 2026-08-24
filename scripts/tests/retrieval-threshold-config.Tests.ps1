Describe 'calibrated retrieval threshold configuration' {
    BeforeAll {
        $exampleEnv = Get-Content (Join-Path $PSScriptRoot '../../.env.example') -Raw
        $settings = Get-Content (Join-Path $PSScriptRoot '../../backend/src/sialabs_local_rag/settings.py') -Raw
        $evidence = Get-Content (Join-Path $PSScriptRoot '../../docs/evidence/embeddinggemma-threshold-sweep.md') -Raw
    }

    It 'keeps the example environment at the calibrated threshold' {
        $exampleEnv | Should -Match 'RETRIEVAL_MIN_SCORE=0\.25'
    }

    It 'keeps runtime default and evidence aligned to 0.25' {
        $settings | Should -Match 'retrieval_min_score: float = Field\(default=0\.25'
        $evidence | Should -Match 'calibrated default is \*\*0\.25\*\*'
    }
}
