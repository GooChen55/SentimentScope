# 第三方依赖

`mediacrawler/` 是官方独立采集引擎，由 `scripts/setup-engine.ps1` 按 `apps/crawler-api/crawler-engine.lock.json` 初始化；使用独立 `.venv` 和原始 `uv.lock`，本地适配器位于采集 API，原许可证保留。

`content-schema/` 是旧内容表定义的最小兼容副本，随本项目代码保留，包含原版权头和许可证。完整旧引擎已经归档，不参与实际采集。
