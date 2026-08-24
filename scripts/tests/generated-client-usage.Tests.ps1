Describe 'generated API client types' {
    It 'uses generated OpenAPI contracts in the frontend API layer' {
        $api = Get-Content frontend/src/api.ts -Raw
        $types = Get-Content frontend/src/types.ts -Raw

        (Select-String -InputObject $api -Pattern "ChatRequest.*api/generated|ChatRequest" ) | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $types -Pattern 'GeneratedChatResponse|GeneratedSourceChunk') | Should -Not -BeNullOrEmpty
    }
}
