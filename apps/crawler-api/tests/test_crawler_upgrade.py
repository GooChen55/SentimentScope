import asyncio
import json
import multiprocessing
import pytest
from sqlalchemy import MetaData, Table, Column, Integer, BigInteger, Text, select, func
from sqlalchemy.ext.asyncio import create_async_engine
from app.deep_sentiment.ingest import ingest_records
from app.web.schemas import TaskInfo, TaskType, TaskStatus, CrawlStartRequest
from app.web.services.task_manager import TaskManager
from app.web.services.web_collector import validate_url, save_document

def finish_immediately(conn):
    conn.send(json.dumps({"type": "result", "success": True, "data": {"ok": True}}))
    conn.close()

def idle_worker():
    import time
    time.sleep(60)

@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setenv("CRAWLER_TASK_STATE", str(tmp_path / "tasks.json"))
    TaskManager._instance = None
    tm = TaskManager()
    yield tm
    TaskManager._instance = None

def add_task(tm):
    task = TaskInfo(task_id="test", type=TaskType.deep_sentiment, status=TaskStatus.running,
                    created_at="2026-10-11T00:00:00Z", config={"keywords": ["测试"]})
    tm._tasks[task.task_id] = task
    tm._active_task_id = task.task_id
    return task

@pytest.mark.asyncio
async def test_fast_exit_drains_result(manager):
    task = add_task(manager)
    parent, child = multiprocessing.Pipe()
    proc = multiprocessing.Process(target=finish_immediately, args=(child,))
    proc.start()
    child.close()
    await asyncio.to_thread(proc.join, 10)
    await manager._read_pipe(task.task_id, proc, parent)
    assert task.status == TaskStatus.completed and task.result == {"ok": True}
    assert manager._active_task_id is None

@pytest.mark.asyncio
async def test_stop_releases_task_slot(manager):
    task = add_task(manager)
    parent, child = multiprocessing.Pipe()
    proc = multiprocessing.Process(target=idle_worker)
    proc.start()
    child.close()
    manager._processes[task.task_id] = proc
    assert manager.stop_task(task.task_id)
    await manager._read_pipe(task.task_id, proc, parent)
    assert task.status == TaskStatus.stopped and manager._active_task_id is None
    assert not proc.is_alive()

def test_restart_marks_interrupted(manager):
    add_task(manager)
    manager._persist()
    TaskManager._instance = None
    restored = TaskManager()
    assert restored.get_task("test").status == TaskStatus.failed
    assert restored.get_task("test").config["keywords"] == ["测试"]

def test_retry_has_new_identity(manager, monkeypatch):
    task = add_task(manager)
    task.status = TaskStatus.failed
    manager._active_task_id = None
    monkeypatch.setattr(manager, "_spawn_worker", lambda _: None)
    new_id = manager.retry_task("test")
    assert new_id != "test" and manager.get_task(new_id).config["retry_of"] == "test"

@pytest.mark.asyncio
async def test_import_idempotent_and_transactional(tmp_path):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    meta = MetaData()
    for name, key in [("douyin_aweme", "aweme_id"), ("douyin_aweme_comment", "comment_id")]:
        Table(name, meta, Column("id", Integer, primary_key=True), Column(key, BigInteger),
              Column("title", Text), Column("content", Text), Column("last_modify_ts", BigInteger))
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)
    content = {"aweme_id": "123", "title": "fixture only"}
    comments = {"comment_id": "456", "content": "test comment"}
    (tmp_path / "search_contents_2026.jsonl").write_text(json.dumps(content) + "\n" + json.dumps(content), encoding="utf-8")
    (tmp_path / "search_comments_2026.jsonl").write_text(json.dumps(comments), encoding="utf-8")
    first = await ingest_records(tmp_path, "dy", engine)
    second = await ingest_records(tmp_path, "dy", engine)
    assert first["new_notes"] == first["new_comments"] == 1
    assert second["new_notes"] == second["new_comments"] == 0
    assert second["updated_records"] == 2 and second["duplicate_records"] == 1
    (tmp_path / "search_contents_2026.jsonl").write_text(json.dumps({**content, "title": "must rollback"}) + '\n' + json.dumps({"aweme_id": "not integer"}), encoding="utf-8")
    with pytest.raises(ValueError):
        await ingest_records(tmp_path, "dy", engine)
    async with engine.connect() as conn:
        assert (await conn.execute(select(meta.tables["douyin_aweme"].c.title))).scalar() == "fixture only"
        assert (await conn.execute(select(func.count()).select_from(meta.tables["douyin_aweme"]))).scalar() == 1
    await engine.dispose()

@pytest.mark.asyncio
async def test_document_url_dedup():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    doc = dict(id="a" * 64, url="https://example.com/a", title="Test", content="Text",
               topic="test", source="example.com", published_at=None, collected_at=1, content_hash="b" * 64)
    assert await save_document(doc, engine) == "new"
    assert await save_document(doc, engine) == "duplicate"
    assert await save_document({**doc, "content_hash": "c" * 64}, engine) == "updated"
    await engine.dispose()

@pytest.mark.parametrize("url", ["file:///tmp/a", "http://127.0.0.1/", "http://[::1]/", "http://192.168.1.1/", "https://user:pwd@example.com/", "http://example.com:9000/"])
def test_reject_non_public_urls(url):
    with pytest.raises(ValueError):
        validate_url(url)

def test_limits_validated():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CrawlStartRequest(max_notes=-1)

@pytest.mark.asyncio
async def test_actual_worker_returns_failed_collection(manager):
    from app.web.services.task_manager import _run_worker_in_subprocess
    task = add_task(manager)
    parent, child = multiprocessing.Pipe()
    proc = multiprocessing.Process(target=_run_worker_in_subprocess,
        args=({"type": "web_page", "urls": ["http://127.0.0.1/"], "topic": "fixture"}, child))
    proc.start()
    child.close()
    await manager._read_pipe(task.task_id, proc, parent)
    assert task.status == TaskStatus.failed
    assert task.result["failures"][0]["error"] == "不支持本机、内网或保留地址"

def test_windows_job_closes_process_tree():
    import os, subprocess, sys
    if os.name != "nt":
        pytest.skip("Windows process supervision")
    from app.web.services.process_job import WindowsProcessJob
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        job = WindowsProcessJob(proc.pid)
        job.close()
        proc.wait(timeout=5)
        assert proc.poll() is not None
    finally:
        if proc.poll() is None:
            proc.kill()

def test_dates_require_explicit_publication_metadata():
    from app.web.services.web_collector import explicit_publish_date
    assert explicit_publish_date('<html><body>Copyright 2015-12-03</body></html>') is None
    assert explicit_publish_date('<html><meta property="article:published_time" content="2023-10-02" /></html>') == "2023-10-02"
