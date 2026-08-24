Describe 'Generated API contracts' {
    It 'uses generated OpenAPI types as the public frontend response contracts' {
        $types = Get-Content (Join-Path $PSScriptRoot '../../frontend/src/types.ts') -Raw

        $types | Should -Match 'export type SourceChunk = GeneratedSourceChunk'
        $types | Should -Match 'export type ChatResponse = GeneratedChatResponse'
        $types | Should -Not -Match 'export type SourceChunk = \{'
        $types | Should -Not -Match 'export type ChatResponse = \{'
    }
}
