Describe 'frontend API contract types' {
    It 'represents backend source and chat metadata' {
        $types = (Get-Content frontend/src/types.ts -Raw) + (Get-Content frontend/src/generated/openapi.ts -Raw)

        (Select-String -InputObject $types -Pattern "collection_id\?: string \| null") | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $types -Pattern 'dense_score\?: number \| null') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $types -Pattern 'fusion_score\?: number \| null') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $types -Pattern "retrieval_channels\??:.*dense.*lexical") | Should -Not -BeNullOrEmpty
    }

    It 'sends collection scope in chat requests' {
        $api = Get-Content frontend/src/api.ts -Raw

        (Select-String -InputObject $api -Pattern 'collectionId\?: string') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $api -Pattern 'collection_id: collectionId') | Should -Not -BeNullOrEmpty
    }
}
