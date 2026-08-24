Describe 'Conversation context cleanup' {
    It 'does not retain the unused string-concatenation context builder' {
        $app = Get-Content (Join-Path $PSScriptRoot '../../frontend/src/App.tsx') -Raw

        $app | Should -Not -Match 'function buildContextualQuestion'
        $app | Should -Match 'function buildConversationContext'
    }
}
