# 历史归档

这里保留原始来源，目录中的脚本和配置可能仍引用旧布局，不作为当前项目入口。

- `legacy-mediacrawler/`：完整旧爬虫，仅保留历史；当前采集引擎见 `vendor/mediacrawler`，表结构兼容见 `vendor/content-schema`。
- `maintenance/`：旧中文启动入口、一次性解压及迁移脚本。
- `manifests/`：原应用依赖清单的历史快照。
- `research-examples/`：原教学和模型实验脚本，不属于轻量回归测试。
- `macos-metadata/`：压缩包自带的 `__MACOSX` 元数据。

当前入口是根目录 `Start.ps1` / `Stop.ps1`；开发方式见 `docs/development.md`。
