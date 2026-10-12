param([switch]$SkipDatabase)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'scripts/start.ps1') -SkipDatabase:$SkipDatabase
