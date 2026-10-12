import json
from app.deep_sentiment.live_progress import live_counts, live_stage

def test_live_counts_dedup_and_skip_partial_writes(tmp_path):
    note = json.dumps({"note_id": "123"})
    (tmp_path / "search_contents_today.jsonl").write_text(note + '\n' + note + '\n' + '{"note_id":', encoding="utf-8")
    (tmp_path / "search_comments_today.jsonl").write_text(json.dumps({"comment_id": "456"}) + '\n', encoding="utf-8")
    assert live_counts(tmp_path, "wb") == (1, 1)
    assert live_stage(tmp_path, 1, 1) == "采集正文与评论"

def test_stage_does_not_expose_cookie_or_raw_logs(tmp_path):
    (tmp_path / "engine.log").write_text("cookie=private\nWaiting for scan code login", encoding="utf-8")
    assert live_stage(tmp_path, 0, 0) == "等待登录确认"

async def fake_ingest(output, platform):
    return {"notes_count": 1, "comments_count": 0}

import pytest
@pytest.mark.asyncio
async def test_progress_emitted_before_engine_finishes(tmp_path, monkeypatch):
    import asyncio
    from app.deep_sentiment import platform_crawler as adapter
    from app.web.services import crawl_worker
    events = []
    class Process:
        returncode = None
        async def communicate(self, data):
            request = json.loads(data)
            from pathlib import Path
            (Path(request["output_path"]) / "search_contents_today.jsonl").write_text(json.dumps({"note_id": "123"}) + '\n', encoding="utf-8")
            await asyncio.sleep(2.2)
            self.returncode = 0
            return None, None
    async def spawn(*args, **kwargs):
        return Process()
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    monkeypatch.setattr(adapter, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(adapter, "engine_info", lambda: {"ready": True})
    monkeypatch.setattr(adapter, "ingest_records", fake_ingest)
    monkeypatch.setattr(adapter.asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(crawl_worker, "_emit", events.append)
    result = await adapter.PlatformCrawler()._run_crawler_async("wb", ["fixture"], "qrcode", 1)
    assert result["success"]
    assert any(e["type"] == "progress" and e["notes"] == 1 and e["keywords_done"] == 0 for e in events)
