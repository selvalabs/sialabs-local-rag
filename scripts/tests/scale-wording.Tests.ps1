Describe 'Scale wording' {
    It 'anchors the README limitation to the versioned benchmark' {
        $readme = Get-Content (Join-Path $PSScriptRoot '../../README.md') -Raw

        $readme | Should -Match '50,000'
        $readme | Should -Match 'machine-specific'
        $readme | Should -Match 'ADR_RETRIEVAL_SCALE.md'
        $readme | Should -Not -Match 'not large-scale vector search\.'
    }
}
