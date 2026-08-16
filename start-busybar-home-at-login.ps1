$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dashboard = Join-Path $projectRoot ".venv\Scripts\busybar-home-web.exe"

if (-not (Test-Path -LiteralPath $dashboard)) {
    throw "The project environment is missing. Open a terminal here and run: uv sync"
}

function Test-DashboardPort {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.BeginConnect("127.0.0.1", 8765, $null, $null)
        return $connection.AsyncWaitHandle.WaitOne(250) -and $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

if (-not (Test-DashboardPort)) {
    $env:BUSYBAR_CLIENT = "official"
    $env:BUSYBAR_ALLOW_HARDWARE = "true"
    if (-not $env:BUSYBAR_DEVICE_ADDRESS) {
        $env:BUSYBAR_DEVICE_ADDRESS = "10.0.4.20"
    }

    Start-Process -FilePath $dashboard -WorkingDirectory $projectRoot -WindowStyle Hidden

    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if (Test-DashboardPort) {
            break
        }
        Start-Sleep -Milliseconds 250
    }
}
