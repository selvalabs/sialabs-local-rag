Describe 'Conversation request construction' {
    It 'does not retain the removed string-encoded conversation parser' {
        $api = Get-Content (Join-Path $PSScriptRoot '../../frontend/src/api.ts') -Raw

        $api | Should -Not -Match 'legacy parser removed'
        $api | Should -Not -Match 'Recent conversation context:'
        $api | Should -Not -Match 'Contexto recente da conversa:'
    }
}
