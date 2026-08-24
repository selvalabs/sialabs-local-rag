Describe 'Docker quick start' {
    BeforeAll {
        $readme = Get-Content (Join-Path $PSScriptRoot '../../README.md') -Raw
    }

    It 'creates the local Compose environment before starting Docker' {
        $copyIndex = $readme.IndexOf('Copy-Item .env.example .env')
        $composeIndex = $readme.IndexOf('docker compose')

        $copyIndex | Should -BeGreaterThan -1
        $composeIndex | Should -BeGreaterThan -1
        $copyIndex | Should -BeLessThan $composeIndex
    }
}
