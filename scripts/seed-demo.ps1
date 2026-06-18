param(
  [string]$ApiUrl = "http://localhost:8000",
  [string]$FilePath = ".\examples\sialabs-demo-context.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$title = "SIALabs Local RAG Demo Context"
$resolvedFilePath = (Resolve-Path $FilePath).Path

if (!(Test-Path $resolvedFilePath)) {
  throw "Demo file not found: $FilePath"
}

# Use .NET ReadAllText to avoid Windows PowerShell serializing Get-Content
# strings with PSPath/PSParentPath metadata inside ConvertTo-Json.
$content = [System.IO.File]::ReadAllText(
  $resolvedFilePath,
  [System.Text.Encoding]::UTF8
)

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

$payloadObject = @{
  title = $title
  content = [string]$content
  source_type = "demo-seed"
}

$payload = $payloadObject | ConvertTo-Json -Depth 5

Write-Host "Posting demo document to $ApiUrl/api/documents ..."
$response = Invoke-RestMethod `
  -Uri "$ApiUrl/api/documents" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $payload

Write-Host ""
Write-Host "Demo document created:"
$response | ConvertTo-Json -Depth 5