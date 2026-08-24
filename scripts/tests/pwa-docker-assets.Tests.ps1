Describe 'frontend PWA assets in Docker' {
    BeforeAll {
        $dockerfile = Get-Content (Join-Path $PSScriptRoot '../../frontend/Dockerfile') -Raw
        $publicAssets = @(
            'manifest.webmanifest',
            'service-worker.js',
            'icon.svg',
            'maskable-icon.svg'
        )
    }

    It 'copies the public directory before the production build' {
        $dockerfile | Should -Match 'COPY public ./public'
        $dockerfile.IndexOf('COPY public ./public') | Should -BeLessThan $dockerfile.IndexOf('RUN npm run build')
    }

    It 'keeps all required PWA assets in the source tree' {
        foreach ($asset in $publicAssets) {
            Test-Path (Join-Path $PSScriptRoot "../../frontend/public/$asset") | Should -Be $true
        }
    }
}
