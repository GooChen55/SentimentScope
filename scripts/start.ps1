param([switch]$SkipDatabase)
$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$runtimeDir = Join-Path $workspaceRoot 'var/runtime'
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$databaseFile = Join-Path $workspaceRoot 'config/database.env'
if (!(Test-Path -LiteralPath $databaseFile)) { throw 'Missing config/database.env; copy database.env.example first.' }
$database = @{}
foreach ($line in Get-Content -LiteralPath $databaseFile -Encoding UTF8) {
    if ($line.Trim() -and !$line.Trim().StartsWith('#')) {
        $pair = $line -split '=',2
        if ($pair.Count -eq 2) { $database[$pair[0].Trim()] = $pair[1].Trim().Trim('"').Trim("'") }
    }
}
foreach ($key in @('MYSQL_USER','MYSQL_PASSWORD','MYSQL_DATABASE','DB_HOST','DB_PORT')) {
    if (!$database.ContainsKey($key)) { throw "Missing database setting: $key" }
}
if (!$SkipDatabase) {
    docker compose --env-file $databaseFile -p sentiment-integration -f (Join-Path $workspaceRoot 'infra/compose.yaml') up -d --wait --wait-timeout 90
    if ($LASTEXITCODE -ne 0) { throw 'MySQL did not become ready.' }
}
$nodePath = (Get-Command node -ErrorAction Stop).Source
$components = @(
    @{Name='research-api';Port=5001;Exe='apps/research-api/.venv/Scripts/python.exe';Script='apps/research-api/tools/serve.py';Dir='apps/research-api';Args=''},
    @{Name='research-web';Port=3000;Exe=$nodePath;Script='apps/research-web/node_modules/vite/bin/vite.js';Dir='apps/research-web';Args='--host 127.0.0.1 --port 3000 --strictPort'},
    @{Name='crawler-api';Port=9000;Exe='apps/crawler-api/.venv/Scripts/python.exe';Script='apps/crawler-api/tools/serve.py';Dir='apps/crawler-api';Args=''},
    @{Name='crawler-web';Port=5173;Exe=$nodePath;Script='apps/crawler-web/node_modules/vite/bin/vite.js';Dir='apps/crawler-web';Args='--host 127.0.0.1 --port 5173 --strictPort'}
)
$entries = @()
$pidFile = Join-Path $runtimeDir 'processes.json'
if (Test-Path -LiteralPath $pidFile) {
    $saved = Get-Content -LiteralPath $pidFile -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($item in $saved) { $entries += $item }
}
$environment = @{
    DB_HOST=$database.DB_HOST; DB_PORT=$database.DB_PORT; DB_USER=$database.MYSQL_USER;
    DB_PASSWORD=$database.MYSQL_PASSWORD; DB_NAME=$database.MYSQL_DATABASE;
    INSIGHT_VECTOR_ENABLED='false'; INSIGHT_CLUSTERING_ENABLED='false'; CRAWLER_IGNORE_SAVED_DB='1';
    PYTHONIOENCODING='utf-8'; PYTHONUNBUFFERED='1'
}
$previous = @{}
try {
    foreach ($key in $environment.Keys) {
        $previous[$key] = [Environment]::GetEnvironmentVariable($key,'Process')
        [Environment]::SetEnvironmentVariable($key,$environment[$key],'Process')
    }
    foreach ($component in $components) {
        $exe = if ([IO.Path]::IsPathRooted($component.Exe)) { $component.Exe } else { Join-Path $workspaceRoot $component.Exe }
        $script = Join-Path $workspaceRoot $component.Script
        $directory = Join-Path $workspaceRoot $component.Dir
        if (!(Test-Path -LiteralPath $exe) -or !(Test-Path -LiteralPath $script)) { throw "Missing runtime: $($component.Name)" }
        $listeners = @(Get-NetTCPConnection -LocalPort $component.Port -State Listen -ErrorAction SilentlyContinue)
        if ($listeners.Count) {
            $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($listeners[0].OwningProcess)"
            if ($owner.CommandLine -and $owner.CommandLine.Contains($script)) { Write-Host "$($component.Name) already running"; continue }
            throw "Port $($component.Port) is owned by another application."
        }
        $process = Start-Process -FilePath $exe -ArgumentList ('"' + $script + '" ' + $component.Args) -WorkingDirectory $directory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeDir ($component.Name + '.out.log')) -RedirectStandardError (Join-Path $runtimeDir ($component.Name + '.err.log')) -PassThru
        $entries = @($entries | Where-Object name -ne $component.Name) + @{name=$component.Name;pid=$process.Id;script=$script}
        $entries | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $pidFile -Encoding UTF8
    }
} finally {
    foreach ($key in $previous.Keys) { [Environment]::SetEnvironmentVariable($key,$previous[$key],'Process') }
}
Write-Host 'Research: http://127.0.0.1:3000'
Write-Host 'Crawler:  http://127.0.0.1:5173'
Write-Host "Logs: $runtimeDir"
