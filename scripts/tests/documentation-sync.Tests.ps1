Describe 'public documentation synchronization' {
    BeforeAll {
        $root = Join-Path $PSScriptRoot '..\..'
        $architecture = Get-Content -Raw (Join-Path $root 'docs\ARCHITECTURE.md')
        $demo = Get-Content -Raw (Join-Path $root 'docs\DEMO.md')
        $localAi = Get-Content -Raw (Join-Path $root 'docs\LOCAL_AI.md')
        $validation = Get-Content -Raw (Join-Path $root 'docs\VALIDATION.md')
    }

    It 'describes the implemented retrieval architecture' {
        foreach ($term in @('FTS5', 'RRF', 'hybrid', 'collections', 'Office', 'OCR')) {
            (Select-String -InputObject $architecture -Pattern $term -CaseSensitive:$false) | Should -Not -BeNullOrEmpty
        }
        $architecture | Should -Not -Match 'The retriever calculates cosine similarity against stored chunks\.'
    }

    It 'keeps demo instructions local and product-complete' {
        $demo | Should -Not -Match '--host 0\.0\.0\.0'
        foreach ($term in @('collection', 'hybrid', 'locator', 'no-answer', 'DOCX', 'PPTX', 'XLSX')) {
            (Select-String -InputObject $demo -Pattern $term -CaseSensitive:$false) | Should -Not -BeNullOrEmpty
        }
    }

    It 'documents dense and hybrid local AI modes' {
        foreach ($term in @('hybrid', 'FTS5', 'RRF', 'collections')) {
            (Select-String -InputObject $localAi -Pattern $term -CaseSensitive:$false) | Should -Not -BeNullOrEmpty
        }
    }

    It 'links the current evaluation evidence and limits' {
        foreach ($term in @('hybrid', 'retrieval-scale', 'category', 'no-answer', 'not a universal benchmark')) {
            (Select-String -InputObject $validation -Pattern $term -CaseSensitive:$false) | Should -Not -BeNullOrEmpty
        }
        $validation | Should -Not -Match 'No load, retrieval-quality or answer-quality benchmark is claimed\.'
    }
}
