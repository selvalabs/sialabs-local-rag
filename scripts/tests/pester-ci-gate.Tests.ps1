Describe 'Pester CI gate' {
    BeforeAll {
        $ci = Get-Content (Join-Path $PSScriptRoot '../../.github/workflows/ci.yml') -Raw
    }

    It 'runs the contract suite on a Windows runner with a compatible Pester version' {
        $ci | Should -Match 'runs-on: windows-latest'
        $ci | Should -Match 'Get-Module Pester -ListAvailable'
        $ci | Should -Match 'Install-Module Pester -MinimumVersion 5\.5\.0'
        $ci | Should -Not -Match 'Install-Module Pester -RequiredVersion'
        $ci | Should -Match 'Import-Module \$pester\.Path -Force'
        $ci | Should -Match 'Invoke-Pester -Path scripts/tests -CI'
    }
}
