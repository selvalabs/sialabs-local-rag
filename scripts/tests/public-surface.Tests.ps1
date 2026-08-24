Describe 'Public repository surface' {
    It 'does not include internal planning artifacts' {
        $internalFiles = @(
            '../../docs/superpowers/specs/2026-08-24-public-readme-parity-design.md',
            '../../docs/superpowers/plans/2026-08-24-public-readme-parity.md'
        ) | ForEach-Object { Join-Path $PSScriptRoot $_ }

        foreach ($path in $internalFiles) {
            Test-Path $path | Should -Be $false
        }
    }
}
