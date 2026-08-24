Describe 'answer copy and source IDs' {
    It 'keeps answer copying text-only and labels retrieved sources' {
        $app = Get-Content frontend/src/App.tsx -Raw
        $sourceCard = Get-Content frontend/src/SourceCard.tsx -Raw
        $surface = "$app`n$sourceCard"

        (Select-String -InputObject $app -Pattern 'navigator\.clipboard\.writeText') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $app -Pattern 'Copy answer') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $surface -Pattern 'sourceIndex \+ 1') | Should -Not -BeNullOrEmpty
    }
}
