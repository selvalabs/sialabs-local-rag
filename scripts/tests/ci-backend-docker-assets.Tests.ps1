Describe 'CI backend and Docker gates' {
    It 'uses frozen development dependencies in the backend job' {
        $workflow = Get-Content (Join-Path $PSScriptRoot '../../.github/workflows/ci.yml') -Raw

        $workflow | Should -Match 'run: uv sync --frozen --dev'
    }

    It 'smoke-tests every public PWA asset from the container' {
        $workflow = Get-Content (Join-Path $PSScriptRoot '../../.github/workflows/ci.yml') -Raw

        foreach ($path in @('manifest.webmanifest', 'service-worker.js', 'icon.svg', 'maskable-icon.svg')) {
            $workflow | Should -Match ("curl --fail .*http://127\.0\.0\.1:5173/{0}" -f [regex]::Escape($path))
        }
    }
}
