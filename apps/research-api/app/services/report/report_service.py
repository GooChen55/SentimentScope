"""Aggregate role reports without inventing an additional LLM judgement."""
import asyncio
import html
import re
from pathlib import Path
from typing import Any

import mistune

from app.services.report.task_store import ReportTaskStore, ReportTask, ReportTaskStatus
from engines.contracts.config import PROJECT_ROOT, get_settings
from engines.contracts.paths import DATA_ROOT


class ReportService:
    def __init__(self, task_store: ReportTaskStore, role_dirs: dict[str, Path] | None = None,
                 output_dir: Path | None = None, research_store=None) -> None:
        self.task_store = task_store
        self._role_dirs = role_dirs
        self._output_dir = output_dir
        self.research_store = research_store
        self._workers: set[asyncio.Task] = set()

    @staticmethod
    def _resolve(directory: str) -> Path:
        path = Path(directory)
        if path.is_absolute():
            return path
        if path.parts and path.parts[0] == 'data':
            return DATA_ROOT / Path(*path.parts[1:])
        return PROJECT_ROOT / path

    def _directories(self, research_id: str | None = None) -> dict[str, Path]:
        if research_id:
            from app.services.research_store import ResearchStore
            task = (self.research_store or ResearchStore()).get(research_id)
            if task['status'] != 'completed':
                raise ValueError('请先完成所选研究任务')
            return {role: DATA_ROOT / 'runs' / task['research_id'] / role
                    for role in ('insight', 'media', 'host')}
        if self._role_dirs is not None:
            return self._role_dirs
        settings = get_settings()
        return {"insight": self._resolve(settings.INSIGHT_REPORT_DIR),
                "media": self._resolve(settings.MEDIA_REPORT_DIR),
                "host": self._resolve(settings.HOST_REPORT_DIR)}

    def _find_inputs(self, query: str | None = None, research_id: str | None = None) -> dict[str, Path]:
        result = {}
        for role, folder in self._directories(research_id).items():
            files = sorted(folder.glob(f"{role}_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            for path in files:
                match = re.fullmatch(rf"{role}_(.+)_\d{{8}}_\d{{6}}(?:_[a-f0-9]{{8}})?", path.stem)
                if not research_id and query is not None and (not match or match.group(1) != query):
                    continue
                if path.read_text(encoding="utf-8").strip():
                    result[role] = path
                    break
        return result

    def get_report_status(self, query: str | None = None, research_id: str | None = None) -> dict[str, Any]:
        inputs = self._find_inputs(query, research_id)
        return {"inputs_ready": {"insight", "media"} <= inputs.keys(),
                "files_found": [path.name for path in inputs.values()]}

    def start_generate_report_task(self, query: str, research_id: str | None = None) -> ReportTask:
        query = query.strip()
        if not query:
            raise ValueError("报告主题不能为空")
        inputs = self._find_inputs(query, research_id)
        if not {"insight", "media"} <= inputs.keys():
            raise ValueError("该主题的 Insight 和 Media 报告尚未齐备，请先完成研究")
        task = self.task_store.create_generate_task()
        worker = asyncio.create_task(self._run_report_generation(task, query, inputs))
        self._workers.add(worker)
        worker.add_done_callback(self._workers.discard)
        return task

    def get_generate_report_task(self, task_id: str) -> ReportTask:
        task = self.task_store.get_generate_task(task_id)
        if task is None:
            raise KeyError("报告任务不存在")
        return task

    async def close(self):
        # File aggregation is short; finish writes before application shutdown.
        await asyncio.gather(*self._workers, return_exceptions=True)

    def get_download_file(self, task_id: str, file_type: str) -> dict[str, Any]:
        if file_type not in {"md", "html"}:
            raise ValueError("仅支持 md 和 html 格式")
        task = self.get_generate_report_task(task_id)
        if task.status != ReportTaskStatus.COMPLETED:
            raise RuntimeError("报告尚未完成")
        path = Path(task.markdown_file_path if file_type == "md" else task.report_file_path)
        if not path.is_file():
            raise FileNotFoundError("报告文件不存在")
        return {"file_path": str(path), "file_name": path.name,
                "media_type": "text/markdown" if file_type == "md" else "text/html"}

    async def _run_report_generation(self, task: ReportTask, query: str, inputs: dict[str, Path]) -> None:
        try:
            await asyncio.to_thread(self._write_report, task, query, inputs)
            task.update_status(ReportTaskStatus.COMPLETED)
        except Exception as exc:
            task.error = str(exc)
            task.update_status(ReportTaskStatus.ERROR)
        finally:
            self.task_store.persist()

    def _write_report(self, task: ReportTask, query: str, inputs: dict[str, Path]) -> None:
        sections = [f"# {query}\n", "> 本报告汇集各研究角色的原始产物；汇编本身不构成额外的事实核验。\n"]
        if "host" not in inputs:
            sections.append("> 主持人研判尚未提供，当前报告仅含私域和公域研究，不能视为已完成综合裁判。\n")
        for role, title in (("host", "主持人研判"), ("insight", "私域证据分析"), ("media", "公开媒体分析")):
            if role in inputs:
                path = inputs[role]
                sections.extend([f"## {title}\n", f"来源文件：`{path.name}`\n", path.read_text(encoding="utf-8")])
        markdown = "\n\n".join(sections)
        renderer = mistune.create_markdown(escape=True)
        content = ("<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
                   "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
                   f"<title>{html.escape(query)}</title>"
                   "<style>body{max-width:960px;margin:40px auto;padding:0 24px;line-height:1.8;"
                   "font-family:system-ui,sans-serif;overflow-wrap:anywhere}pre{overflow:auto}</style>"
                   f"</head><body>{renderer(markdown)}</body></html>")
        output = self._output_dir or self._resolve(get_settings().OUTPUT_DIR) / "combined"
        output.mkdir(parents=True, exist_ok=True)
        md_path, html_path = output / f"{task.task_id}.md", output / f"{task.task_id}.html"
        md_path.write_text(markdown, encoding="utf-8")
        html_path.write_text(content, encoding="utf-8")
        task.html_content = content
        task.markdown_file_path, task.markdown_file_name = str(md_path), md_path.name
        task.report_file_path, task.report_file_name = str(html_path), html_path.name
