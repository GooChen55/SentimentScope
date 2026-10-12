"""Read safe counters from complete JSONL records while the engine is running."""
import json
from app.deep_sentiment.ingest import TABLES

def live_counts(output, platform):
    ids = {"contents": set(), "comments": set()}
    for file in output.rglob("*.jsonl"):
        kind = "contents" if "contents_" in file.name else "comments" if "comments_" in file.name else None
        if not kind:
            continue
        field = TABLES[platform][0 if kind == "contents" else 1][1]
        # A writer may still be appending the last line; never count incomplete data.
        for line in file.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True):
            if not line.endswith("\n"):
                continue
            try:
                value = json.loads(line).get(field)
                if value:
                    ids[kind].add(str(value))
            except (ValueError, AttributeError):
                continue
    return len(ids["contents"]), len(ids["comments"])

def live_stage(output, notes, comments):
    if comments:
        return "采集正文与评论"
    if notes:
        return "采集正文"
    log = (output / "engine.log").read_text(encoding="utf-8", errors="replace")[-20000:]
    if "Begin search" in log:
        return "检索关键词"
    if "Login successful" in log or "redirect weibo mobile homepage" in log:
        return "同步登录状态"
    if "Waiting for scan code login" in log:
        return "等待登录确认"
    return "启动采集浏览器"
