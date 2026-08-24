Describe 'Integrated Playwright E2E gate' {
    It 'keeps a real-stack flow and runs it in CI' {
        $spec = Get-Content (Join-Path $PSScriptRoot '../../frontend/e2e/integrated.spec.ts') -Raw
        $workflow = Get-Content (Join-Path $PSScriptRoot '../../.github/workflows/ci.yml') -Raw

        $spec | Should -Match 'API_URL.*api/documents'
        $spec | Should -Match 'React to FastAPI to SQLite to hash retrieval'
        $spec | Should -Not -Match 'page\.route'
        $workflow | Should -Match 'npx playwright install --with-deps chromium'
        $workflow | Should -Match 'run: npx playwright test'
    }
}
