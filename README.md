# SentimentScope

舆情研判平台：采集社交平台与公开网页证据，运行 Insight / Media / Host Agent，查看讨论、导出报告并进行基础评测。

## 使用

```powershell
git clone https://github.com/GooChen55/SentimentScope.git
cd SentimentScope
.\Start.ps1
```

- 研究工作台：<http://127.0.0.1:3000>
- 采集控制台：<http://127.0.0.1:5173>
- 研究 API：<http://127.0.0.1:5001/docs>
- 采集 API：<http://127.0.0.1:9000/docs>

停止应用：`.\Stop.ps1`。已有数据库可用 `.\Start.ps1 -SkipDatabase`。MySQL 使用持久化命名卷 `sentiment-integration_sentiment_mysql`，停止应用保留数据库与历史数据。

首次使用请先按照 [开发指南](docs/development.md) 创建本机配置、安装应用依赖并初始化采集引擎。仓库不包含密钥、浏览器登录状态、运行产物与本地依赖环境。

## 目录

```text
SentimentScope/
├── apps/                       四个可独立运行的应用
│   ├── research-api/           FastAPI、研究编排、Agent、评测适配器与测试
│   ├── research-web/           Vue 研究工作台
│   ├── crawler-api/            采集调度、网页采集、入库、进度与测试
│   └── crawler-web/            Vue 采集控制台
├── config/                     本机配置与不含密钥的示例配置
├── infra/                      Docker Compose 与 MySQL 初始 SQL
├── vendor/                     官方采集引擎、兼容表结构与许可证
├── references/                 评估参考仓库，保留其 Git 历史
├── var/                        任务、证据、报告、浏览器状态、日志与备份
├── docs/                       架构、开发、使用指南与技术资料
├── scripts/                    启动、停止、引擎初始化脚本
├── tools/                      检查工具与环境入口维护工具
├── archive/                    历史代码与维护资料
├── Start.ps1
└── Stop.ps1
```

应用源码与运行数据分离。两个 API 使用各自的 `.venv`，官方采集引擎也使用独立环境；所有第三方爬取操作通过采集服务的子进程适配器执行。

## 文档入口

- [架构与模块职责](docs/architecture.md)
- [开发、安装与验证](docs/development.md)
- [平台使用指南](docs/guides/usage.md)
- [采集与登录说明](docs/guides/crawler.md)
- [评测适配器](apps/research-api/evaluation/README.md)
- [第三方依赖与许可](THIRD_PARTY_NOTICES.md)

本机配置位于 `config/*.env`，浏览器登录状态在 `var/browser/`，研究产物在 `var/research/`，采集输出在 `var/crawler/`。这些本地文件由 `.gitignore` 排除。
