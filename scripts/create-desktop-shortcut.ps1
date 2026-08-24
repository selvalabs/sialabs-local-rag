param(
  [string]$ShortcutName = "SIALabs Local RAG"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$StartupScript = Join-Path $PSScriptRoot "start-local-app.ps1"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "$ShortcutName.lnk"
$PowerShellPath = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

if (-not (Test-Path $StartupScript)) {
  throw "Startup script not found: $StartupScript"
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PowerShellPath
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$StartupScript`""
$Shortcut.WorkingDirectory = $RepoRoot
$Shortcut.IconLocation = "$PowerShellPath,0"
$Shortcut.Description = "Start SIALabs Local RAG"
$Shortcut.WindowStyle = 7
$Shortcut.Save()

Write-Host "Shortcut created: $ShortcutPath"
