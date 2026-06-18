param(
  [string]$OllamaBaseUrl = $(if ($env:OLLAMA_BASE_URL) { $env:OLLAMA_BASE_URL } else { "http://localhost:11434" }),
  [string]$ChatModel = $(if ($env:OLLAMA_CHAT_MODEL) { $env:OLLAMA_CHAT_MODEL } else { "gemma4" }),
  [string]$EmbedModel = $(if ($env:OLLAMA_EMBED_MODEL) { $env:OLLAMA_EMBED_MODEL } else { "embeddinggemma" }),
  [switch]$RunSmokeRequests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$baseUrl = $OllamaBaseUrl.TrimEnd("/")

function Test-ModelName {
  param(
    [string[]]$AvailableModels,
    [string]$ExpectedModel
  )

  if ($AvailableModels -contains $ExpectedModel) {
    return $true
  }

  if ($AvailableModels -contains "$ExpectedModel`:latest") {
    return $true
  }

  foreach ($model in $AvailableModels) {
    if ($model -like "$ExpectedModel*") {
      return $true
    }
  }

  return $false
}

Write-Host "Ollama smoke test"
Write-Host "Base URL: $baseUrl"
Write-Host "Chat model: $ChatModel"
Write-Host "Embedding model: $EmbedModel"
Write-Host ""

Write-Host "Checking Ollama API..."
try {
  $tagsResponse = Invoke-RestMethod -Uri "$baseUrl/api/tags" -Method Get -TimeoutSec 10
}
catch {
  Write-Host ""
  Write-Host "Could not reach Ollama at $baseUrl"
  Write-Host "Make sure Ollama is installed and running."
  Write-Host ""
  Write-Host "Expected local API:"
  Write-Host "$baseUrl/api/tags"
  throw
}

$models = @()

if ($null -ne $tagsResponse.models) {
  foreach ($model in $tagsResponse.models) {
    if ($model.name) {
      $models += [string]$model.name
    }
    elseif ($model.model) {
      $models += [string]$model.model
    }
  }
}

$models = @($models | Sort-Object -Unique)

Write-Host "Available local models:"
if ($models.Count -eq 0) {
  Write-Host "- No local models found."
}
else {
  foreach ($model in $models) {
    Write-Host "- $model"
  }
}

Write-Host ""

$chatAvailable = Test-ModelName -AvailableModels $models -ExpectedModel $ChatModel
$embedAvailable = Test-ModelName -AvailableModels $models -ExpectedModel $EmbedModel

if ($chatAvailable) {
  Write-Host "Chat model found: $ChatModel"
}
else {
  Write-Host "Chat model not found: $ChatModel"
  Write-Host "Suggested command:"
  Write-Host "ollama pull $ChatModel"
}

if ($embedAvailable) {
  Write-Host "Embedding model found: $EmbedModel"
}
else {
  Write-Host "Embedding model not found: $EmbedModel"
  Write-Host "Suggested command:"
  Write-Host "ollama pull $EmbedModel"
}

if (-not $chatAvailable -or -not $embedAvailable) {
  Write-Host ""
  Write-Host "Ollama is reachable, but one or more configured models are missing."
  Write-Host "You can either pull the missing models or change OLLAMA_CHAT_MODEL / OLLAMA_EMBED_MODEL in .env."
  exit 2
}

if ($RunSmokeRequests) {
  Write-Host ""
  Write-Host "Running chat smoke request..."

  $chatPayload = @{
    model = $ChatModel
    stream = $false
    messages = @(
      @{
        role = "user"
        content = "Reply with one short sentence confirming the local model is running."
      }
    )
  } | ConvertTo-Json -Depth 10

  $chatResponse = Invoke-RestMethod `
    -Uri "$baseUrl/api/chat" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $chatPayload `
    -TimeoutSec 120

  if ($chatResponse.message.content) {
    Write-Host "Chat response:"
    Write-Host $chatResponse.message.content
  }
  else {
    Write-Host "Chat response received, but no message.content field was found."
  }

  Write-Host ""
  Write-Host "Running embedding smoke request..."

  $embedPayload = @{
    model = $EmbedModel
    input = "SIALabs Local RAG local embedding smoke test."
  } | ConvertTo-Json -Depth 5

  $embedResponse = Invoke-RestMethod `
    -Uri "$baseUrl/api/embed" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $embedPayload `
    -TimeoutSec 120

  if ($embedResponse.embeddings) {
    $count = @($embedResponse.embeddings).Count
    Write-Host "Embedding response received. Embedding arrays: $count"
  }
  else {
    Write-Host "Embedding response received, but no embeddings field was found."
  }
}

Write-Host ""
Write-Host "Ollama smoke test passed."