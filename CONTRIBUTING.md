# 开发与贡献

安装步骤见 [开发指南](docs/development.md)。开发前创建独立分支，例如 `feat/report-filter` 或 `fix/crawl-progress`，提交应围绕一个明确问题。

## 模块边界

- 界面分别在 `apps/research-web` 和 `apps/crawler-web`。
- API 分别在 `apps/research-api` 和 `apps/crawler-api`，两个 `app` 包分别运行和测试。
- Agent 逻辑在研究服务的 `engines`，跨角色维度与证据结构集中在 `engines/contracts`。
- 采集引擎适配在采集服务 `tools`，不要直接修改上游源码。
- 配置示例提交到 `config`；密钥、浏览器会话与运行产物保留在本机。

## 验证方式

根据变更范围执行相关检查。两个 API 的测试必须在各自目录执行，以保证 `app` 包导入正确；以下命令从项目根目录开始：

```powershell
cd apps/research-api
.venv/Scripts/python.exe -m pytest tests -q
cd ../crawler-api
.venv/Scripts/python.exe -m pytest tests -q
cd ../..
npm --prefix apps/research-web run build
npm --prefix apps/crawler-web run build
.\apps\research-api\.venv\Scripts\python.exe tools/check_repository.py
```

服务、数据库和采集引擎可用时，可从根目录执行 `.\scripts\check.ps1` 完成完整本机检查。常规测试使用替代外部调用和临时数据，不需要真实账号与模型密钥。真实采集、模型连通性和 RAGAS 评测单独验证。

GitHub CI 在 Windows 执行两套后端测试，在 Linux 构建两套前端，并检查文档链接与提交文件边界；不运行真实爬取、模型请求或本机数据库验收。

## 提交与评审

提交说明应写清问题及结果，例如 `Fix task status after crawler cancellation`。PR 说明填写复现条件、主要变更和实际验证结果。修改持久化结构时解释已有任务和报告的兼容方式。

第三方组件按 [许可说明](THIRD_PARTY_NOTICES.md) 使用，不移除版权声明，不将第三方能力描述为自行实现。
