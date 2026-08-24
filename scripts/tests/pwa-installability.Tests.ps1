Describe 'PWA installability' {
    It 'pre-caches the navigation shell for offline startup' {
        $serviceWorker = Get-Content frontend/public/service-worker.js -Raw
        $manifest = Get-Content frontend/public/manifest.webmanifest -Raw
        $index = Get-Content frontend/index.html -Raw

        (Select-String -InputObject $serviceWorker -Pattern "'/index.html'") | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $manifest -Pattern '"display": "standalone"') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $index -Pattern 'manifest.webmanifest') | Should -Not -BeNullOrEmpty
    }
}
