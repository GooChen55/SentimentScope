import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.app import app
from app.dependencies import get_report_service
from app.services.report.report_service import ReportService
from app.services.report.task_store import ReportTaskStatus, ReportTaskStore


def make_service(root: Path) -> ReportService:
    directories = {role: root / role for role in ("insight", "media", "host")}
    for folder in directories.values():
        folder.mkdir()
    return ReportService(ReportTaskStore(), directories, root / "output")


def write_input(root: Path, role: str, query: str, content: str) -> None:
    (root / role / f"{role}_{query}_20261011_100000.md").write_text(content, encoding="utf-8")


def test_missing_or_unrelated_reports_do_not_create_a_task(tmp_path):
    service = make_service(tmp_path)
    write_input(tmp_path, "insight", "主题甲", "私域甲")
    write_input(tmp_path, "media", "主题乙", "媒体乙")
    assert service.get_report_status("主题甲")["inputs_ready"] is False
    with pytest.raises(ValueError, match="尚未齐备"):
        service.start_generate_report_task("主题甲")
    assert not service.task_store.tasks_registry


def test_combined_report_preserves_sources_and_marks_missing_host(tmp_path):
    service = make_service(tmp_path)
    write_input(tmp_path, "insight", "主题甲", "私域甲：样本中存在负面评论。")
    write_input(tmp_path, "media", "主题甲", "媒体甲：官方回应尚未发布。")
    write_input(tmp_path, "host", "主题乙", "其他主题的裁判结果")

    async def generate():
        task = service.start_generate_report_task("主题甲")
        await asyncio.gather(*service._workers)
        return task

    task = asyncio.run(generate())
    assert task.status == ReportTaskStatus.COMPLETED
    content = Path(task.markdown_file_path).read_text(encoding="utf-8")
    assert "私域甲" in content and "媒体甲" in content
    assert "主持人研判尚未提供" in content
    assert "其他主题的裁判结果" not in content
    assert "insight_主题甲_20261011_100000.md" in content
    for extension in ("md", "html"):
        assert Path(service.get_download_file(task.task_id, extension)["file_path"]).is_file()


def test_host_included_and_html_script_escaped(tmp_path):
    service = make_service(tmp_path)
    for role in ("insight", "media", "host"):
        write_input(tmp_path, role, "主题甲", f"{role}的结论\n<script>alert(1)</script>")

    async def generate():
        task = service.start_generate_report_task("主题甲")
        await asyncio.gather(*service._workers)
        return task

    task = asyncio.run(generate())
    assert "host的结论" in task.html_content
    assert "主持人研判尚未提供" not in task.html_content
    assert "<script>" not in task.html_content
    assert "&lt;script&gt;" in task.html_content


def test_write_failure_has_observable_error(tmp_path):
    service = make_service(tmp_path)
    for role in ("insight", "media"):
        write_input(tmp_path, role, "主题甲", role)
    service._output_dir.write_text("output is a file", encoding="utf-8")

    async def generate():
        task = service.start_generate_report_task("主题甲")
        await asyncio.gather(*service._workers)
        return task

    task = asyncio.run(generate())
    assert task.status == ReportTaskStatus.ERROR
    assert task.error
    with pytest.raises(RuntimeError):
        service.get_download_file(task.task_id, "html")


def test_task_ids_do_not_collide_and_running_task_is_exclusive():
    store = ReportTaskStore()
    first = store.create_generate_task()
    with pytest.raises(RuntimeError):
        store.create_generate_task()
    first.update_status(ReportTaskStatus.COMPLETED)
    second = store.create_generate_task()
    assert first.task_id != second.task_id
    assert len(store.tasks_registry) == 2


def test_registered_routes_and_client_errors(tmp_path):
    service = make_service(tmp_path)
    app.dependency_overrides[get_report_service] = lambda: service
    try:
        with TestClient(app) as client:
            assert client.get("/health").json() == {"status": "ok"}
            assert client.get("/api/report/status", params={"query": "主题甲"}).json()["inputs_ready"] is False
            assert client.post("/api/report/generate", json={"query": "主题甲"}).status_code == 422
            assert client.get("/api/report/task/missing").status_code == 404
            assert client.get("/api/report/result/missing").status_code == 404
            assert client.get("/api/report/download/missing/md").status_code == 404
            assert client.get("/api/report/download/missing/exe").status_code == 422
    finally:
        app.dependency_overrides.clear()
