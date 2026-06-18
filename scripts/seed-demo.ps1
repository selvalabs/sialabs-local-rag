param(
  [string]$ApiUrl = "http://localhost:8000",
  [string]$FilePath = ".\examples\sialabs-demo-context.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$title = "SIALabs Local RAG Demo Context"

if (!(Test-Path $FilePath)) {
  throw "Demo file not found: $FilePath"
}

$content = Get-Content $FilePath -Raw

Write-Host "Checking API health at $ApiUrl/health ..."
Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get | Out-Null

Write-Host "Checking existing documents ..."
$documentsResponse = Invoke-RestMethod -Uri "$ApiUrl/api/documents" -Method Get
$existing = @($documentsResponse.documents) | Where-Object { $_.title -eq $title } | Select-Object -First 1

if ($null -ne $existing) {
  Write-Host ""
  Write-Host "Demo document already exists. Skipping seed."
  $existing | ConvertTo-Json -Depth 5
  exit 0
}

$payload = @{
  title = $title
  content = $content
  source_type = "demo-seed"
} | ConvertTo-Json -Depth 5

Write-Host "Posting demo document to $ApiUrl/api/documents ..."
$response = Invoke-RestMethod `
  -Uri "$ApiUrl/api/documents" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $payload

Write-Host ""
Write-Host "Demo document created:"
$response | ConvertTo-Json -Depth 5