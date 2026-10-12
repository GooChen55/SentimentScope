$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$serviceDir = Join-Path $workspaceRoot 'apps/crawler-api'
$manifest = Get-Content (Join-Path $serviceDir 'crawler-engine.lock.json') -Raw | ConvertFrom-Json
$engineDir = [IO.Path]::GetFullPath((Join-Path $serviceDir $manifest.directory))
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
$uvPath = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE '.local/bin/uv.exe' }
if (-not (Test-Path -LiteralPath $uvPath)) { throw '请先安装 uv' }
if (-not (Test-Path -LiteralPath (Join-Path $engineDir '.git'))) {
    git clone $manifest.repository $engineDir
    if ($LASTEXITCODE -ne 0) { throw '采集引擎下载失败' }
}
git -C $engineDir diff --exit-code --quiet
if ($LASTEXITCODE -ne 0) { throw '上游源码有本地修改，请先保存后再初始化' }
git -C $engineDir checkout --detach $manifest.revision
if ($LASTEXITCODE -ne 0) { throw '无法切换到锁定版本' }
& $uvPath sync --project $engineDir --frozen --python 3.12
if ($LASTEXITCODE -ne 0) { throw '采集引擎环境安装失败' }
$pythonPath = Join-Path $engineDir '.venv/Scripts/python.exe'
& $uvPath pip install --python $pythonPath 'socksio==1.0.0'
if ($LASTEXITCODE -ne 0) { throw '代理依赖安装失败' }
& $pythonPath -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw '采集浏览器安装失败' }
Write-Host '采集引擎初始化完成（固定版本、独立环境）'
