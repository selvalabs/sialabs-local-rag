Describe "typed conversation context" {
  BeforeAll {
    $api = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\api.ts")
    $app = Get-Content -Raw (Join-Path $PSScriptRoot "..\..\frontend\src\App.tsx")
  }

  It "does not serialize or parse legacy contextual question strings" {
    if ($api -match 'parseLegacyContextualQuestion|conversationContextOrRuntime') {
      throw 'Frontend API still contains the legacy contextual question transport'
    }
  }

  It "sends typed conversation messages separately from the current question" {
    if ($app -notmatch 'buildConversationContext') { throw 'App must build typed conversation context' }
    if ($app -notmatch 'askQuestion\(\s*submittedQuestion') {
      throw 'App must send the current question separately from conversation context'
    }
  }
}
