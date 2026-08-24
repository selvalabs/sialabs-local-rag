Describe 'Retrieval metrics documentation' {
    It 'matches the versioned hash baseline' {
        $baseline = Get-Content (Join-Path $PSScriptRoot '../../backend/evaluation/baseline-hash.json') -Raw | ConvertFrom-Json
        $docs = Get-Content (Join-Path $PSScriptRoot '../../docs/RETRIEVAL_EVALUATION.md') -Raw

        $format = [Globalization.CultureInfo]::InvariantCulture
        $docs | Should -Match ('Document hit@1 \| {0}' -f $baseline.metrics.document_hit_at_1.ToString('0.0000', $format))
        $docs | Should -Match ('Macro evidence recall@requested-k \| {0}' -f $baseline.metrics.macro_evidence_recall_at_requested_k.ToString('0.0000', $format))
        $docs | Should -Match ('MRR \| {0}' -f $baseline.metrics.mean_reciprocal_rank.ToString('0.0000', $format))
        $docs | Should -Match ('Query success rate \| {0}' -f $baseline.metrics.query_success_rate.ToString('0.0000', $format))
    }
}
