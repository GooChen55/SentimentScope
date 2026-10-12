# 第三方依赖与许可

SentimentScope 的第三方组件遵循各自许可证。本文件集中记录采集引擎和评测参考实现的来源；各组件中的版权头、许可证和 Git 历史保留。

| 组件 | 来源与用途 | 本地位置 |
| --- | --- | --- |
| MediaCrawler | [NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)，社交平台采集引擎；固定提交见引擎锁文件 | `vendor/mediacrawler` |
| 内容表结构 | MediaCrawler 的 `database/models.py`，提供兼容内容表元数据 | `vendor/content-schema` |
| Trafilatura | [adbar/trafilatura](https://github.com/adbar/trafilatura)，公开网页正文提取，版本固定于运行依赖锁文件 | 采集服务依赖 |
| 评测参考实现 | [windyzj/shopkeeper_brain](https://gitee.com/windyzj/shopkeeper_brain)，`0119` 分支，为 RAGAS 样本、指标和输出适配提供参考 | `references/evaluation` |

MediaCrawler 使用 NON-COMMERCIAL LEARNING LICENSE 1.1，具体条款以 [上游 LICENSE](vendor/mediacrawler/LICENSE) 为准。兼容表结构的许可见 [LICENSE](vendor/content-schema/LICENSE)。其他依赖按其包内许可证使用。

应用通过独立工作进程适配采集引擎；研究评测适配器位于 `apps/research-api/evaluation`。历史源码和资料保存在 `archive` 与 `docs/reference`，不参与应用启动。
