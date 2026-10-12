# SentimentScope 评测

基础评测已接入研究页面，检查证据 ID 存在性和五维章节覆盖，不能据此声称事实正确或模型质量高。

RAGAS 适配器将已完成真实研究任务的证据和主持人回答转换为评测样本，计算五项指标并输出 CSV。模拟演示不作为质量评测数据。参考实现与许可见 [第三方说明](../../../THIRD_PARTY_NOTICES.md)。

准备人工核验的参考答案 `reference.md`，在 `apps/research-api` 目录执行：

```powershell
.venv/Scripts/python.exe evaluation/export_samples.py <research_id> --reference reference.md
.venv/Scripts/python.exe -m pip install -r evaluation/requirements.txt
# 在当前进程设置 EVAL_API_KEY、EVAL_MODEL、EVAL_EMBEDDING_MODEL；可另设两个 BASE_URL。
.venv/Scripts/python.exe evaluation/run_ragas.py ../../var/research/evaluation/samples.json
```

评分需要可用的评判模型与 embedding 服务，产生外部 API 调用。当前凭据未通过连通性测试，适配器尚未完成真实评分验证；任何缺失指标输出为空并以退出码 2 标记，不能作为通过。

建议固定三类回归样本：证据不足（不得推断总体比例）、双源冲突（保留时间与口径差异）、多平台同主题（去重但保留来源）。参考答案必须由人工确认，不能直接拿待测模型输出作为标准答案。
