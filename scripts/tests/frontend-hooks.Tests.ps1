Describe 'frontend document hook extraction' {
    It 'keeps document loading and deletion API logic outside App' {
        $app = Get-Content frontend/src/App.tsx -Raw
        $hook = Get-Content frontend/src/hooks/useDocuments.ts -Raw

        (Select-String -InputObject $app -Pattern 'useDocuments') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $app -Pattern '\blistDocuments\b|\bdeleteDocument\b') | Should -BeNullOrEmpty
        (Select-String -InputObject $hook -Pattern 'refreshDocuments|removeDocument') | Should -Not -BeNullOrEmpty
    }
}
