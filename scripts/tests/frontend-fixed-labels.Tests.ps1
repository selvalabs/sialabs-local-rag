Describe 'Frontend translated fixed labels' {
    It 'translates accessibility, theme, collection and metric labels' {
        $app = Get-Content (Join-Path $PSScriptRoot '../../frontend/src/App.tsx') -Raw

        foreach ($key in @('skipMain', 'darkTheme', 'lightTheme', 'activeSources', 'documentCount', 'chunkCount', 'characterCount')) {
            ([regex]::Matches($app, "${key}:")).Count | Should -Be 2
        }

        $app | Should -Match '\{t\.skipMain as string\}'
        $app | Should -Match 't\.darkTheme as string'
        $app | Should -Match 't\.lightTheme as string'
        $app | Should -Match 't\.activeSources as \(count: number\) => string'
        $app | Should -Match 't\.documentCount as \(count: number\) => string'
        $app | Should -Match 't\.chunkCount as \(count: number\) => string'
        $app | Should -Match 't\.characterCount as \(count: number\) => string'
    }
}
