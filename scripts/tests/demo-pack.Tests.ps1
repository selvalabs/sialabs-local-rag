Describe 'public showcase demo pack' {
    It 'documents a reproducible capture and does not claim missing screenshots' {
        $pack = Get-Content docs/DEMO_PACK.md -Raw

        (Select-String -InputObject $pack -Pattern 'seed-demo.ps1') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $pack -Pattern 'workspace-grounded-answer.png') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $pack -Pattern 'no committed screenshot or video asset') | Should -Not -BeNullOrEmpty
    }
}
