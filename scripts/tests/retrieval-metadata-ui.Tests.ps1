Describe "retrieval metadata UI contract" {
  BeforeAll {
    $types = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\types.ts")
    $app = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\App.tsx")
    $sourceCard = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\SourceCard.tsx")
    $frontendSurface = "$app`n$sourceCard"
    $schema = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\backend\src\sialabs_local_rag\schemas.py")
  }

  It "models retrieval mode and channel scores" {
    foreach ($field in @('retrieval_mode', 'dense_score', 'dense_rank', 'lexical_rank', 'fusion_score', 'retrieval_channels')) {
      if (($types + $schema) -notmatch $field) { throw "Missing retrieval metadata field: $field" }
    }
  }

  It "shows retrieval metadata in the chat response" {
    foreach ($field in @('retrieval_mode', 'retrieval_channels', 'fusion_score')) {
      if ($frontendSurface -notmatch $field) { throw "Frontend does not display $field" }
    }
  }
}
