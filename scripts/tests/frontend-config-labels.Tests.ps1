Describe 'Frontend configuration metric labels' {
    It 'uses translated character and overlap labels' {
        $app = Get-Content (Join-Path $PSScriptRoot '../../frontend/src/App.tsx') -Raw

        ([regex]::Matches($app, 'overlap:')).Count | Should -Be 2
        $app | Should -Match 't\.characterCount as \(count: number\) => string\)\(config\.chunk_size\)'
        $app | Should -Match 't\.overlap as string'
        $app | Should -Not -Match "config\.chunk_size\} chars"
    }
}
