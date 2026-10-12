# -*- coding: utf-8 -*-
"""
TaskManager — 在独立子进程中运行爬虫任务，通过管道读取进度事件，广播给 WebSocket 订阅者。

单例模式，内存存储，强制串行执行（仅允许一个活跃任务）。
"""

import asyncio
import json
import multiprocessing
import os
import signal
import sys
import time
import uuid
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from loguru import logger

from app.config import SUPPORTED_PLATFORMS
from app.paths import DATA_ROOT
from app.web.schemas import TaskType, TaskStatus, TaskInfo, TaskSummary, TaskProgress


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskManager:
    """爬虫任务管理器（单例）"""

    _instance: Optional["TaskManager"] = None

    def __new__(cls) -> "TaskManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._tasks: Dict[str, TaskInfo] = {}
        self._active_task_id: Optional[str] = None
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._log_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._processes: Dict[str, multiprocessing.Process] = {}
        self._readers = {}
        self._jobs = {}
        self._state_file = Path(os.getenv("CRAWLER_TASK_STATE", str(DATA_ROOT / "tasks.json")))
        if self._state_file.exists():
            for raw in json.loads(self._state_file.read_text(encoding="utf-8")):
                task = TaskInfo.model_validate(raw)
                if task.status in (TaskStatus.pending, TaskStatus.running, TaskStatus.stopping):
                    task.status = TaskStatus.failed
                    task.error = "服务重启导致任务中断，可手动重试"
                    task.ended_at = _now_iso()
                self._tasks[task.task_id] = task
        self._persist()

    def _persist(self):
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        temp = self._state_file.with_suffix(".tmp")
        temp.write_text(json.dumps([t.model_dump(mode="json") for t in self._tasks.values()], ensure_ascii=False), encoding="utf-8")
        temp.replace(self._state_file)

    async def shutdown(self):
        for task_id in list(self._processes):
            self.stop_task(task_id)
        if self._readers:
            await asyncio.gather(*list(self._readers.values()), return_exceptions=True)

    def retry_task(self, task_id):
        task = self._tasks.get(task_id)
        if not task or task.status not in (TaskStatus.failed, TaskStatus.stopped):
            raise ValueError("只有失败或已停止的任务可以重试")
        return self.start_task(task.type, {**task.config, "retry_of": task_id})

    # ====================== 公开方法 ======================

    def start_task(
        self,
        task_type: TaskType,
        config: Dict[str, Any],
        on_started: Optional[Callable] = None,
    ) -> str:
        """启动一个新任务，返回 task_id。如果有活跃任务则抛出 RuntimeError。"""
        if self._active_task_id is not None:
            active = self._tasks.get(self._active_task_id)
            if active and active.status in (TaskStatus.pending, TaskStatus.running, TaskStatus.stopping):
                raise RuntimeError(
                    f"当前已有任务正在运行 (task_id: {self._active_task_id})，请先停止或等待完成"
                )

        task_id = str(uuid.uuid4())[:8]
        now = _now_iso()

        task = TaskInfo(
            task_id=task_id,
            type=task_type,
            status=TaskStatus.pending,
            created_at=now,
            config=config,
        )
        self._tasks[task_id] = task
        self._active_task_id = task_id
        self._log_buffers[task_id] = []

        if on_started:   # TODO 扩展钩子回调
            on_started()

        self._persist()
        try:
            self._spawn_worker(task_id)
        except Exception:
            task.status = TaskStatus.failed
            task.error = "工作进程启动失败"
            task.ended_at = _now_iso()
            self._active_task_id = None
            self._persist()
            raise
        return task_id

    def stop_task(self, task_id: str) -> bool:
        """请求停止任务。返回 True 表示成功发送停止信号。"""
        task = self._tasks.get(task_id)
        if task is None:
            return False
        if task.status not in (TaskStatus.pending, TaskStatus.running):
            return False

        task.status = TaskStatus.stopping
        self._broadcast(task_id, {
            "type": "status_change",
            "from": "running",
            "to": "stopping",
            "timestamp": _now_iso(),
        })

        proc = self._processes.get(task_id)
        if proc and proc.is_alive():
            if os.name == "nt":
                # Only the worker PID owned by this manager and its descendants.
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            else:
                proc.terminate()
        self._persist()

        return True

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 20) -> Dict[str, Any]:
        """返回活跃任务 + 最近任务列表。"""
        active = self._tasks.get(self._active_task_id) if self._active_task_id else None
        if active and active.status not in (TaskStatus.pending, TaskStatus.running, TaskStatus.stopping):
            active = None

        sorted_tasks = sorted(
            self._tasks.values(),
            key=lambda t: t.created_at,
            reverse=True,
        )
        recents = [
            TaskSummary(
                task_id=t.task_id,
                type=t.type,
                status=t.status,
                created_at=t.created_at,
                ended_at=t.ended_at,
                error=t.error,
            )
            for t in sorted_tasks[:limit]
        ]

        return {"active": active, "recent": recents}

    def subscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        """订阅某个任务的进度事件。"""
        if task_id not in self._subscribers:
            self._subscribers[task_id] = []
        self._subscribers[task_id].append(queue)

        # 回放已有日志
        for log_entry in self._log_buffers.get(task_id, []):
            try:
                queue.put_nowait(log_entry)
            except asyncio.QueueFull:
                # 直接把这条进度丢弃，绝对不允许你卡住我发给其他人的进度
                pass
        task = self._tasks.get(task_id)
        if task and task.status in (TaskStatus.completed, TaskStatus.failed, TaskStatus.stopped):
            queue.put_nowait({"type": "result", "success": task.status == TaskStatus.completed,
                "data": task.result, "error": task.error or ("任务已停止" if task.status == TaskStatus.stopped else None),
                "elapsed_seconds": task.progress.elapsed_seconds, "timestamp": _now_iso()})

    def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        """取消订阅。"""
        queues = self._subscribers.get(task_id, [])
        if queue in queues:
            queues.remove(queue)


    def _spawn_worker(self, task_id: str) -> None:
        """在子进程中启动爬虫 worker。"""
        task = self._tasks[task_id]

        # 获取 父子进程连接
        parent_conn, child_conn = multiprocessing.Pipe()

        worker_config = {
            **task.config,
            "type": task.type.value,
            "target_date": task.config.get("target_date"),
            "platforms": task.config.get("platforms"),
            "sources": task.config.get("sources"),
            "max_keywords": task.config.get("max_keywords"),
            "max_notes": task.config.get("max_notes"),
            "login_type": task.config.get("login_type"),
        }

        # 父进程操作子进程的句柄对象
        proc = multiprocessing.Process(
            target=_run_worker_in_subprocess,
            args=(worker_config, child_conn),
            daemon=True,
        )
        proc.start()
        child_conn.close()
        self._processes[task_id] = proc
        if os.name == "nt":
            from app.web.services.process_job import WindowsProcessJob
            try:
                self._jobs[task_id] = WindowsProcessJob(proc.pid)
            except Exception:
                proc.terminate()
                proc.join(timeout=2)
                parent_conn.close()
                self._processes.pop(task_id, None)
                raise

        task.status = TaskStatus.running
        task.started_at = _now_iso()

        # 向当前事件循环的线程里扔了一个“后台协程任务”
        self._persist()
        self._readers[task_id] = asyncio.create_task(self._read_pipe(task_id, proc, parent_conn))

    async def _read_pipe(
        self,
        task_id: str,
        proc: multiprocessing.Process,
        conn,
    ) -> None:
        """异步读取子进程的 stdout 管道，解析 JSON 事件并广播。"""
        task = self._tasks.get(task_id)
        start_time = time.time()

        loop = asyncio.get_event_loop()

        def _read_line() -> Optional[str]:
            """阻塞读取一行，在子进程结束后返回 None。"""
            try:
                if conn.poll(0.5):
                    return conn.recv()
                return None
            except (EOFError, BrokenPipeError):
                return None

        while True:
            line = await loop.run_in_executor(None, _read_line)
            if line:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"[TaskManager] 无法解析 worker 输出: {line[:200]}")
                    continue

                elapsed = time.time() - start_time
                event["elapsed_seconds"] = round(elapsed, 1)

                event_type = event.get("type", "")

                if event_type == "result":
                    if task.status == TaskStatus.stopping:
                        continue
                    task.result = event.get("data", {})
                    # 任务结束
                    if event.get("success"):
                        task.status = TaskStatus.completed
                        task.result = event.get("data", {})
                    else:
                        task.status = TaskStatus.failed
                        task.error = event.get("error", "未知错误")
                    task.ended_at = _now_iso()
                    task.progress.elapsed_seconds = round(elapsed, 1)

                elif event_type == "progress":
                    task.progress = TaskProgress(
                        stage=task.progress.stage,
                        current_platform=event.get("platform"),
                        platforms_completed=event.get("platforms_completed", []),
                        keywords_total=event.get("keywords_total", 0),
                        keywords_processed=event.get("keywords_done", event.get("keywords_processed", 0)),
                        notes_collected=event.get("notes", event.get("notes_collected", 0)),
                        comments_collected=event.get("comments", task.progress.comments_collected),
                        elapsed_seconds=round(elapsed, 1),
                    )

                elif event_type == "stage":
                    task.progress.stage = event.get("stage", "")
                    self._log(task_id, "info", event.get("message", ""))

                elif event_type == "log":
                    self._log(task_id, event.get("level", "info"), event.get("message", ""))

                self._broadcast(task_id, event)
                self._persist()
            elif not proc.is_alive():
                break

        # 进程已退出，检查是否异常退出
        if task and task.status in (TaskStatus.running, TaskStatus.stopping):
            if task.status == TaskStatus.stopping:
                task.status = TaskStatus.stopped
                task.error = "任务已停止"
                task.ended_at = _now_iso()
                self._broadcast(task_id, {"type": "result", "success": False, "error": task.error,
                    "elapsed_seconds": round(time.time() - start_time, 1), "timestamp": _now_iso()})
            else:
                task.status = TaskStatus.failed
                task.error = f"工作进程退出但未返回结果 (exitcode={proc.exitcode})"
                task.ended_at = _now_iso()
                self._active_task_id = None
                self._broadcast(task_id, {
                    "type": "result",
                    "success": False,
                    "error": task.error,
                    "elapsed_seconds": round(time.time() - start_time, 1),
                    "timestamp": _now_iso(),
                })

        # 清理
        conn.close()
        proc.join(timeout=1)
        job = self._jobs.pop(task_id, None)
        if job:
            job.close()
        if self._active_task_id == task_id:
            self._active_task_id = None
        self._persist()
        self._readers.pop(task_id, None)
        if task_id in self._processes:
            del self._processes[task_id]

    def _log(self, task_id: str, level: str, message: str) -> None:
        """记录日志到缓冲区（上限 500 条）。"""
        entry = {
            "type": "log",
            "level": level,                 # 日志级别
            "message": message,             # 日志内容
            "timestamp": _now_iso(),        # 日志时间
        }
        buf = self._log_buffers.setdefault(task_id, [])
        buf.append(entry)
        if len(buf) > 500:
            self._log_buffers[task_id] = buf[-500:]

    def _broadcast(self, task_id: str, event: Dict[str, Any]) -> None:
        """向所有订阅者广播事件。"""
        queues = self._subscribers.get(task_id, [])
        dead = []
        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass
            except Exception:
                dead.append(q)
        for q in dead:
            queues.remove(q)


def _run_worker_in_subprocess(config: Dict[str, Any], child_conn) -> None:
    """在子进程中运行 worker，通过 Pipe 发送进度事件。"""
    import json as _json
    import sys as _sys
    import traceback as _tb

    # 将项目根目录加入 sys.path，确保 import app 能找到
    worker_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_root = os.path.dirname(worker_dir)
    if project_root not in _sys.path:
        _sys.path.insert(0, project_root)

    try:
        from app.web.services.crawl_worker import run_worker

        class PipeWriter:
            def __init__(self, c):
                self._conn = c

            def write(self, s: str) -> int:
                s = s.strip()
                if s:
                    self._conn.send(s)
                return len(s)

            def flush(self) -> None:
                pass

        pipe_writer = PipeWriter(child_conn)
        old_stdout = _sys.stdout
        _sys.stdout = pipe_writer

        try:
            run_worker(config)
        finally:
            _sys.stdout = old_stdout

    except Exception:
        _tb.print_exc(file=_sys.stderr)
        try:
            child_conn.send(_json.dumps({
                "type": "result",
                "success": False,
                "error": "工作进程执行失败，请查看本地服务日志",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, ensure_ascii=False))
        except Exception:
            pass
        finally:
            child_conn.close()
    else:
        child_conn.close()
