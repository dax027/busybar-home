$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dashboard = Join-Path $projectRoot ".venv\Scripts\busybar-home-web.exe"

if (-not (Test-Path -LiteralPath $dashboard)) {
    throw "The project environment is missing. Open a terminal here and run: uv sync"
}

$env:BUSYBAR_CLIENT = "official"
$env:BUSYBAR_ALLOW_HARDWARE = "true"
if (-not $env:BUSYBAR_DEVICE_ADDRESS) {
    $env:BUSYBAR_DEVICE_ADDRESS = "10.0.4.20"
}

Write-Host "BUSY Bar Home is starting at http://127.0.0.1:8765"
Write-Host "Press Ctrl+C in this window to stop it."
& $dashboard
