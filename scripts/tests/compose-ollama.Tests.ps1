Describe "Docker Compose Ollama networking" {
  BeforeAll {
    $compose = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\docker-compose.yml")
  }

  It "points the backend at the Ollama service name" {
    if ($compose -notmatch '(?s)backend:.*?OLLAMA_BASE_URL:\s*http://ollama:11434') {
      throw 'Compose backend must use http://ollama:11434 for the bundled Ollama service'
    }
  }

  It "defines an Ollama service on the Compose network" {
    if ($compose -notmatch '(?m)^\s{2}ollama:\s*$') {
      throw 'Compose must define an ollama service'
    }
  }

  It "does not configure the backend container to call localhost for Ollama" {
    if ($compose -match '(?s)backend:.*?OLLAMA_BASE_URL:\s*http://localhost:11434') {
      throw 'The backend container must not use localhost to reach Ollama'
    }
  }
}
