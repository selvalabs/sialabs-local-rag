Describe 'public README parity' {
    BeforeAll {
        $root = Join-Path $PSScriptRoot '..\..'
        $readme = Get-Content -Raw (Join-Path $root 'README.md')
    }

    It 'describes the public showcase capabilities and evidence' {
        foreach ($claim in @(
            'hybrid retrieval',
            'collections',
            'structured source',
            'DOCX',
            'PPTX',
            'XLSX',
            'deterministic',
            'EmbeddingGemma',
            'CASE_STUDY.md',
            'DEMO_PACK.md',
            'SECURITY_PRIVACY.md'
        )) {
            (Select-String -InputObject $readme -Pattern $claim -CaseSensitive:$false) | Should -Not -BeNullOrEmpty
        }
    }

    It 'does not retain claims contradicted by the integrated implementation' {
        foreach ($staleClaim in @(
            'No performance benchmark or answer-quality benchmark is claimed',
            'cosine similarity retrieval',
            'Scanned PDFs, OCR, image extraction and table reconstruction are not supported'
        )) {
            (Select-String -InputObject $readme -Pattern $staleClaim -CaseSensitive:$false) | Should -BeNullOrEmpty
        }
    }

    It 'links only existing public evidence files' {
        foreach ($relativePath in @(
            'docs/CASE_STUDY.md',
            'docs/DEMO_PACK.md',
            'docs/RETRIEVAL_EVALUATION.md',
            'docs/SECURITY_PRIVACY.md',
            'CONTRIBUTING.md',
            'CHANGELOG.md',
            'THIRD_PARTY_NOTICES.md'
        )) {
            $readme | Should -Match ([regex]::Escape($relativePath))
            Test-Path (Join-Path $root $relativePath) | Should -Be $true
        }
    }
}
