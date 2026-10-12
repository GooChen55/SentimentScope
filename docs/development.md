# 开发与验证

所有命令从工作区根目录执行。应用环境、前端依赖和第三方引擎分别维护。

## 初始化依赖

准备 Python 3.12、Node.js、Docker 与 uv。将 `config/*.env.example` 复制为对应 `.env` 文件并填写本机配置；已有本机配置请勿覆盖。新建数据库时设置密码，已有数据库迁移继续使用已有凭据和命名卷。

应用的已验证版本固定在各自的 `requirements-runtime.lock.txt`，安装时以这些文件为准：

```powershell
uv venv apps/research-api/.venv --python 3.12
uv pip install --python apps/research-api/.venv/Scripts/python.exe -r apps/research-api/requirements-runtime.lock.txt
uv venv apps/crawler-api/.venv --python 3.12
uv pip install --python apps/crawler-api/.venv/Scripts/python.exe -r apps/crawler-api/requirements-runtime.lock.txt
npm --prefix apps/research-web ci
npm --prefix apps/crawler-web ci
.\scripts\setup-engine.ps1
.\Start.ps1
```

采集引擎使用独立环境和自己的 `uv.lock`，应用服务使用各自的运行依赖锁文件。`vendor/content-schema` 提供内容表元数据。第三方说明见 [依赖与许可](../THIRD_PARTY_NOTICES.md)。

## 日常检查

GitHub CI 对每次推送到 `main` 和 PR 执行隔离的后端测试、两套前端构建及仓库文件检查，不依赖本机数据库、登录账号或模型密钥。提交前也可运行 `.\apps\research-api\.venv\Scripts\python.exe tools/check_repository.py` 检查本地文档链接与文件边界。

```powershell
.\scripts\check.ps1
```

统一脚本在各应用目录内分别执行测试和前端构建，然后运行浏览器冒烟检查与 `tools/check_project.py`。两个 API 的 `app` 包不在同一 Python 进程里混用。

`check_project.py` 检查服务、数据库连接、研究历史、SQLite 完整性、现有报告下载和采集引擎锁定状态，不创建任务，也不调用模型或社交平台。结果保存在 `var/runtime/project-check.json`。浏览器冒烟检查使用临时配置目录，不修改已登录账号的状态。

研究端到端模拟验证会创建一条明确标记模拟模式的任务，需主动执行：

```powershell
.\apps\research-api\.venv\Scripts\python.exe apps/research-api/tools/verify_integration.py
```

真实模型连通性与 RAGAS 评测可能产生外部 API 调用，不在常规检查脚本中运行。

## 可选评测参考环境

常规启动不依赖评测参考仓库。运行 RAGAS 适配器前，从项目根目录获取固定版本：

```powershell
git clone --branch 0119 https://gitee.com/windyzj/shopkeeper_brain.git references/evaluation
git -C references/evaluation checkout --detach dc5ba7f761ecb2e8d721b0afbcd25412448e39ac
```

评测依赖、人工参考答案与模型配置见 [评测指南](../apps/research-api/evaluation/README.md)。

## 修改约定

- 前端修改各自的 `apps/*-web/src`，API 修改各自的 `apps/*-api`。
- 运行数据写入 `var`；配置写入 `config`；不要在源码中硬编码本机绝对路径。
- 上游适配放在采集 API 的 `tools/engine_runtime.py`，升级引擎先更新锁定版本并重新验收。
- 技术参考资料在 `docs/reference`，历史代码在 `archive`，两者均不作为运行入口。
- 测试将研究产物和任务状态隔离到临时目录，避免污染已有研究数据。
