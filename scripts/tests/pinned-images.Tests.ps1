Describe 'container image pinning' {
    It 'uses immutable image digests for runtime images' {
        $backend = Get-Content backend/Dockerfile -Raw
        $frontend = Get-Content frontend/Dockerfile -Raw
        $compose = Get-Content docker-compose.yml -Raw

        (Select-String -InputObject $backend -Pattern 'FROM python:.*@sha256:') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $frontend -Pattern 'FROM node:.*@sha256:') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $frontend -Pattern 'FROM nginxinc/nginx-unprivileged:.*@sha256:') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $compose -Pattern 'image: ollama/ollama@sha256:') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $compose -Pattern 'image: .*:latest') | Should -BeNullOrEmpty
    }
}
