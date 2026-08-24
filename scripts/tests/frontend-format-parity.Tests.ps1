Describe "frontend supported upload formats" {
  BeforeAll {
    $app = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\App.tsx")
  }

  It "offers every backend-supported document extension in the file picker" {
    foreach ($extension in @('.txt', '.md', '.markdown', '.pdf', '.docx', '.pptx', '.xlsx', '.png', '.jpg', '.jpeg', '.tif', '.tiff')) {
      if ($app -notmatch [regex]::Escape($extension)) {
        throw "Frontend file picker is missing $extension"
      }
    }
  }

  It "does not describe the upload flow as text-only" {
    if ($app -match 'TXT, Markdown ou PDF com texto selecionável|TXT, Markdown or selectable-text PDF') {
      throw 'Frontend upload copy is stale and still describes only text formats'
    }
  }
}
