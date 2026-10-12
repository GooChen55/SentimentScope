# SentimentScope 采集指南

采集控制台负责社交平台采集、公开网页证据提取、进度跟踪与入库。社交采集引擎为 MediaCrawler，网页正文提取使用 Trafilatura 2.3.1；依赖与许可证见 [第三方说明](../../THIRD_PARTY_NOTICES.md)。

## 社交采集

采集引擎版本记录于 `apps/crawler-api/crawler-engine.lock.json`，源码位于 `vendor/mediacrawler`，使用独立 Python 3.12 环境。采集服务通过工作进程调用引擎，内容表元数据由 `vendor/content-schema` 提供。

控制台“深度舆情”支持手动关键词，逗号或换行分隔；留空才读取日期话题。默认微博、抖音，可选全部七个平台。首次登录或会话过期时，在采集浏览器完成登录；有效会话复用 `var/browser/mediacrawler` 中的缓存，重启应用后仍可使用已有登录状态。

微博标准模式通过本地运行适配层使用 Playwright 对应的 Chromium，不依赖系统 Chrome 版本。扫码完成后不要关闭采集浏览器，它还需要跳转移动站、读取登录状态并搜索；等控制台显示采集完成后再关闭。浏览器连接中断会明确显示 `browser_closed` 诊断，不能把日志中的登录成功提示当作采集完成。

采集期间每 2 秒更新已读取内容/评论数量和阶段，采集结束后统一入库；浏览器不会逐条展示通过接口读取的内容。微博评论接口明确返回“暂无评论”时按空评论正常结束，不再反复重试；其他错误按重试策略处理。已实际验证关键词“考研趋势”成功采集并新增入库 26 条内容、128 条评论。

JSONL 与原始日志保存在 `var/crawler/crawl-runs/<批次>/`。导入层按平台、记录类型及远端 ID 去重，同一事务更新现有内容/评论表和 `crawler_record` 台账。旧记录更新，历史重复行不自动清理。实际数量分别记录内容、评论、新增、更新和批内重复；零内容不报成功，部分失败保留可用数据和各平台结果。统计单位为平台批次，不能把平台总数重复计入每个关键词。

单平台 30 分钟超时、单并发、评论上限 20/条，不下载视频。Windows Job Object 和停止操作管理工作进程及后代，避免浏览器残留。原始诊断日志和浏览器缓存可能包含会话信息，请保留在本机。

## 网页证据

正文提取项目：https://github.com/adbar/trafilatura 。在“网页证据”填写关联话题和每行一个公开网址，最多 10 个，无需大模型。遵守 robots.txt，限制页面大小，拒绝本机/内网地址及非标准网页端口，校验重定向。

正文存入 `crawler_document`，按最终 URL 去重更新。同一 URL 当前只关联一个话题，跨话题再次采集会更新关联。发布日期只读取显式发布元数据，未知留空；超过 60 KB 的正文明确标记截断，以适配 MySQL TEXT 字段。

Media Agent 按**完全相同的研究主题**读取本地网页证据，保留 `web:<ID>` 和原网址，加入研究证据快照。最多 10 条，每条研判输入截取 8000 字符并标记；完整内容可查看来源。需要登录、验证码或脚本渲染的网页暂不支持，会返回失败原因。

## 任务与环境

任务配置、状态和结果保存在 `var/crawler/tasks.json`。重启后中断任务标为失败；失败或停止任务可以新 ID 重试，旧记录保留。刷新控制台恢复活跃任务订阅。仍为单机、单 API 进程运行，没有分布式调度。

```powershell
.\scripts\setup-engine.ps1
.\vendor\mediacrawler\.venv\Scripts\python.exe apps/crawler-api/tools/check_crawler_engine.py
.\scripts\check.ps1
```

应用依赖固定于 `requirements-runtime.lock.txt`。上游采用官方 `uv.lock`，额外代理依赖固定为 `socksio==1.0.0`。不自动拉取新版本。MediaCrawler 非商业学习许可与 LICENSE 均保留，用于个人学习和实习展示。

公开网页验收来源为 Python 官方文档 `https://docs.python.org/3.12/whatsnew/3.12.html`，关联“Python 3.12 发布”。微博已通过真实采集验收；抖音等其他平台仍需用户完成登录后验证。模型配置和研究服务的验收情况见 [平台使用指南](usage.md)。
