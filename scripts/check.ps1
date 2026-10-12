$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path $PSScriptRoot -Parent
foreach ($application in @('research-api','crawler-api')) {
    $directory = Join-Path $workspaceRoot ('apps/' + $application)
    Push-Location $directory
    try {
        & (Join-Path $directory '.venv/Scripts/python.exe') -m pytest tests -q
        if ($LASTEXITCODE -ne 0) { throw "$application tests failed" }
    } finally { Pop-Location }
}
foreach ($application in @('research-web','crawler-web')) {
    Push-Location (Join-Path $workspaceRoot ('apps/' + $application))
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "$application build failed" }
    } finally { Pop-Location }
}
& (Join-Path $workspaceRoot 'vendor/mediacrawler/.venv/Scripts/python.exe') (Join-Path $workspaceRoot 'apps/crawler-api/tools/check_crawler_engine.py')
if ($LASTEXITCODE -ne 0) { throw 'Crawler engine smoke check failed' }
& (Join-Path $workspaceRoot 'apps/research-api/.venv/Scripts/python.exe') (Join-Path $workspaceRoot 'tools/check_project.py')
if ($LASTEXITCODE -ne 0) { throw 'Running project smoke check failed; start the platform first.' }
Write-Host 'All checks passed.'
