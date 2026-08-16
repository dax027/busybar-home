param(
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $projectRoot "start-busybar-home-at-login.ps1"
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "BUSY Bar Home.lnk"

if ($Remove) {
    if (Test-Path -LiteralPath $shortcutPath) {
        Remove-Item -LiteralPath $shortcutPath
        Write-Host "Removed BUSY Bar Home from Windows startup."
    }
    else {
        Write-Host "BUSY Bar Home is not installed in Windows startup."
    }
    exit
}

if (-not (Test-Path -LiteralPath $launcher)) {
    throw "Startup launcher not found: $launcher"
}

$powerShell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $powerShell
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcher`""
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Start the BUSY Bar Home local server"
$shortcut.WindowStyle = 7
$shortcut.Save()

Write-Host "BUSY Bar Home will start at your next Windows sign-in."
Write-Host "Shortcut: $shortcutPath"
