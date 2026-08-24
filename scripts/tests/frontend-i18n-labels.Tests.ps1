Describe 'Frontend translated labels' {
    It 'defines and consumes copy and runtime fallback labels for both languages' {
        $app = Get-Content (Join-Path $PSScriptRoot '../../frontend/src/App.tsx') -Raw

        ([regex]::Matches($app, 'copyAnswer:')).Count | Should -Be 2
        ([regex]::Matches($app, 'copied:')).Count | Should -Be 2
        ([regex]::Matches($app, 'keepAliveAuto:')).Count | Should -Be 2
        $app | Should -Not -Match "\? 'Copied' : 'Copy answer'"
        $app | Should -Not -Match "\|\| 'keep_alive auto'"
    }
}
