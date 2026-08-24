Describe "structured source cards" {
  BeforeAll {
    $app = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\App.tsx")
    $sourceCard = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\SourceCard.tsx")
    $sourceCardSurface = "$app`n$sourceCard"
  }

  It "formats the persisted locator fields for display" {
    foreach ($field in @('source_locator', 'page_number', 'section_title', 'slide_number', 'sheet_name', 'cell_range')) {
      if ($sourceCardSurface -notmatch [regex]::Escape($field)) {
        throw "Source cards do not use $field"
      }
    }
  }

  It "renders a dedicated locator element" {
    if ($sourceCardSurface -notmatch 'source-locator') {
      throw 'Source cards must render a dedicated source-locator element'
    }
  }
}
