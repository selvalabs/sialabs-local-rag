Describe "collections UI contract" {
  BeforeAll {
    $api = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\api.ts")
    $types = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\types.ts")
    $app = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\App.tsx")
  }

  It "has typed collection summaries and a list API" {
    if ($types -notmatch 'CollectionSummary') { throw 'Frontend types must define CollectionSummary' }
    if ($types -notmatch 'CollectionListResponse') { throw 'Frontend types must define CollectionListResponse' }
    if ($api -notmatch 'getCollections') { throw 'Frontend API must expose getCollections' }
  }

  It "sends the selected collection with chat requests" {
    if ($api -notmatch 'collection_id') { throw 'Chat API must send collection_id' }
    if ($app -notmatch 'activeCollectionId') { throw 'App must track the active collection' }
    if ($app -notmatch '<select') { throw 'App must render a collection selector' }
  }
}
