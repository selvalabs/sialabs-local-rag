Describe 'groundedness and citation evidence' {
    BeforeAll {
        $root = Join-Path $PSScriptRoot '..\..'
        $report = Get-Content -Raw (Join-Path $root 'backend\evaluation\groundedness-citation-regression.json') | ConvertFrom-Json
        $docs = Get-Content -Raw (Join-Path $root 'docs\evidence\groundedness-citation-regression.md')
    }

    It 'records grounded, unsupported and refusal cases' {
        $report.cases.Count | Should -Be 3
        $report.unsupported_case_count | Should -Be 1
        [math]::Round($report.mean_grounded_claim_ratio, 4) | Should -Be 0.8333
    }

    It 'states that the metric is a regression signal rather than an LLM judge' {
        $report.metric_definition | Should -Match 'not an LLM judge'
        $docs | Should -Match 'not an LLM judge'
        (Test-Path (Join-Path $root 'backend\scripts\run_groundedness_evaluation.py')) | Should -Be $true
    }
}
