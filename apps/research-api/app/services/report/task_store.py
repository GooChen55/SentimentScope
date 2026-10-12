from dataclasses import dataclass, asdict
import json
from pathlib import Path
from enum import Enum
from uuid import uuid4
from typing import Optional


class ReportTaskStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ReportTask:
    task_id: str
    status: ReportTaskStatus = ReportTaskStatus.RUNNING
    html_content: str = ""
    report_file_path: str = ""
    report_file_name: str = ""
    markdown_file_path: str = ""
    markdown_file_name: str = ""
    error: str = ""

    def update_status(self, status: ReportTaskStatus) -> None:
        self.status = status


class ReportTaskStore:

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.current_task: Optional[ReportTask] = None
        self.tasks_registry: dict[str, ReportTask] = {}
        if path and path.is_file():
            for record in json.loads(path.read_text(encoding='utf-8')):
                task = ReportTask(**record)
                task.status = ReportTaskStatus(task.status)
                if task.status == ReportTaskStatus.RUNNING:
                    task.status, task.error = ReportTaskStatus.ERROR, '服务重启中断了报告生成，请重新生成'
                self.tasks_registry[task.task_id] = task

    def persist(self):
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps([asdict(task) for task in self.tasks_registry.values()], ensure_ascii=False), encoding='utf-8')
            temporary.replace(self.path)

    def create_generate_task(self) -> ReportTask:
        if self.current_task and self.current_task.status == ReportTaskStatus.RUNNING:
            raise RuntimeError("已有报告生成任务在运行中")
        if self.current_task and self.current_task.status in (
                ReportTaskStatus.COMPLETED,
                ReportTaskStatus.ERROR,
        ):
            self.current_task = None

        task = ReportTask(f"report_{uuid4().hex}")
        self.current_task = task
        self.tasks_registry[task.task_id] = task
        self.persist()
        return task

    def get_generate_task(self, task_id: str) -> Optional[ReportTask]:
        return self.tasks_registry.get(task_id)
