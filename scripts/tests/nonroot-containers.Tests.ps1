Describe 'non-root container hardening' {
    It 'uses non-root runtime identities and the unprivileged nginx image' {
        $backend = Get-Content backend/Dockerfile -Raw
        $frontend = Get-Content frontend/Dockerfile -Raw
        $nginx = Get-Content frontend/nginx.conf -Raw
        $compose = Get-Content docker-compose.yml -Raw

        (Select-String -InputObject $backend -Pattern 'USER appuser') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $frontend -Pattern 'nginx-unprivileged') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $frontend -Pattern 'package-lock.json') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $nginx -Pattern 'listen 8080') | Should -Not -BeNullOrEmpty
        (Select-String -InputObject $compose -Pattern '5173:8080') | Should -Not -BeNullOrEmpty
    }
}
