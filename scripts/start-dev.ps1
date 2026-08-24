Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Start backend in one terminal:"
Write-Host "cd backend; uv run uvicorn sialabs_local_rag.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host ""
Write-Host "Start frontend in another terminal:"
Write-Host "cd frontend; npm run dev"
