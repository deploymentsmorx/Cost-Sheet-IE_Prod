# Build the Cost Sheet Windows desktop executable.
# Requires Node.js, Rust, Visual Studio C++ Build Tools, and WebView2 Runtime.
$ErrorActionPreference = "Stop"
$Frontend = Split-Path -Parent $PSScriptRoot
$Cargo = Join-Path $env:USERPROFILE ".cargo\bin\cargo.exe"
if (-not (Test-Path $Cargo)) {
  throw "Rust Cargo was not found at $Cargo. Install Rust before building the EXE."
}
$env:Path = "$(Split-Path -Parent $Cargo);$env:Path"
$env:CARGO = $Cargo

Push-Location $Frontend
try {
  npm install
  npm run tauri:build -- --no-bundle

  $Exe = Join-Path $Frontend "src-tauri\target\release\costsheet.exe"
  $OutputDir = Join-Path $Frontend "dist-desktop"
  $Output = Join-Path $OutputDir "CostSheet.exe"
  if (-not (Test-Path $Exe)) {
    throw "Tauri completed without producing $Exe"
  }

  New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
  Copy-Item -LiteralPath $Exe -Destination $Output -Force
  Write-Host "Built: $Output"
} finally {
  Pop-Location
}
