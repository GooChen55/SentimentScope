$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$pidFile = Join-Path $workspaceRoot 'var/runtime/processes.json'
if (!(Test-Path -LiteralPath $pidFile)) { Write-Host 'No managed processes.'; return }
$saved = Get-Content -LiteralPath $pidFile -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($entry in $saved) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($entry.pid)"
    if ($process -and $process.CommandLine -and $process.CommandLine.Contains($entry.script)) {
        Stop-Process -Id $entry.pid
        Write-Host "Stopped $($entry.name)"
    }
}
Write-Host 'MySQL is still running; data is preserved.'
