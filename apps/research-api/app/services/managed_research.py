import asyncio
import json
import time
from pathlib import Path
from engines.contracts.config import get_settings, PROJECT_ROOT
from engines.contracts.paths import DATA_ROOT
from engines.common.eventing.bus import subscribe, unsubscribe
from engines.common.eventing.event import EventType
from engines.common.runtime.research_context import research_id, artifact_dir
from app.services.research_store import ResearchStore


class ManagedResearchService:
    def __init__(self, store=None):
        self.store = store or ResearchStore()
        self.workers = {}
        self.subscribers = set()
        self.listener = None
        self.started = False

    def activate(self):
        if self.started:
            return
        for event in EventType:
            subscribe(event, self.record_event)
        self.started = True
        for task in self.store.list():
            if task["status"] in {"queued", "running"}:
                task.update(status="interrupted", error="服务重启中断了研究，请重试")
                self.store.save(task)

    def record_event(self, event_type, data):
        event = {"event": event_type.value, "data": data}
        event["id"] = self.store.append_event(event)
        for queue in list(self.subscribers):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(event)

    def start_research(self, query, mode="live"):
        self.activate()
        if any(not worker.done() for worker in self.workers.values()):
            raise RuntimeError("已有研究运行中，请等待完成或取消")
        if mode not in {"demo", "live"}:
            raise ValueError("无效分析模式")
        if mode == "demo" and query != "示例品牌配送调整":
            raise ValueError("模拟模式仅支持主题：示例品牌配送调整")
        if mode == "live":
            settings = get_settings()
            missing = [name for name in ("INSIGHT_ENGINE_API_KEY", "MEDIA_ENGINE_API_KEY", "HOST_API_KEY", "HOST_MODEL_NAME") if not getattr(settings, name)]
            search_key = {"TavilyAPI": "TAVILY_API_KEY", "BochaAPI": "BOCHA_API_KEY", "AnspireAPI": "ANSPIRE_API_KEY"}[settings.SEARCH_SWITCH]
            if not getattr(settings, search_key):
                missing.append(search_key)
            if missing:
                raise ValueError("真实分析缺少配置：" + ", ".join(missing))
        task = self.store.create(query, mode)
        self.workers[task["research_id"]] = asyncio.create_task(self._run(task))
        return {"started": True, "research_id": task["research_id"], "mode": mode}

    async def _run(self, task):
        token = research_id.set(task["research_id"])
        started = time.perf_counter()
        listener = None
        try:
            task["status"] = "running"
            self.store.save(task)
            from engines.host_agent.listener import SectionReadyListener
            if task["mode"] == "demo":
                from engines.demo import DemoJudge, run_demo, DEMO_EVIDENCE
                listener = SectionReadyListener(DemoJudge())
                runner = run_demo
                artifact_dir().mkdir(parents=True, exist_ok=True)
                (artifact_dir() / "evidence.json").write_text(json.dumps(DEMO_EVIDENCE, ensure_ascii=False), encoding="utf-8")
            else:
                from engines.orchestration.research import run_research
                listener = SectionReadyListener()
                runner = run_research
            self.listener = listener
            listener.start()
            await asyncio.wait_for(runner(task["query"]), timeout=1800)
            await asyncio.wait_for(listener.wait_complete(), timeout=600)
            task["results"] = self._load_results(task["research_id"])
            if not {"insight", "media", "host"} <= task["results"].keys():
                raise RuntimeError("研究产物不完整")
            task["status"] = "completed"
        except asyncio.CancelledError:
            task.update(status="cancelled", error="研究已取消")
        except Exception as exc:
            task.update(status="error", error=str(exc))
        finally:
            if listener:
                worker = listener._worker
                listener.stop()
                if worker:
                    await asyncio.gather(worker, return_exceptions=True)
            self.listener = None
            task["metrics"] = {"elapsed_seconds": round(time.perf_counter() - started, 3), "mode": task["mode"]}
            self.store.save(task)
            self.record_event(EventType.ROLE_PROGRESS, {"role": "host", "status": task["status"], "message": task.get("error") or "研究完成", "progress_pct": 100 if task["status"] == "completed" else 0, "research_id": task["research_id"]})
            research_id.reset(token)

    def _load_results(self, task_id):
        results = {}
        for role in ("insight", "media", "host"):
            folder = DATA_ROOT / "runs" / task_id / role
            files = sorted(folder.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                results[role] = {"final_report": files[0].read_text(encoding="utf-8"), "report_file": files[0].name}
        return results

    def get_research_result(self, task_id=None):
        if task_id:
            return self._load_results(self.store.get(task_id)["research_id"])
        tasks = self.store.list()
        return self._load_results(tasks[0]["research_id"]) if tasks else {}

    async def cancel(self, task_id):
        task = self.store.get(task_id)
        worker = self.workers.get(task_id)
        if worker and not worker.done():
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)
            current = self.store.get(task_id)
            if current["status"] in {"queued", "running"}:
                current.update(status="cancelled", error="研究已取消")
                self.store.save(current)
        return self.store.get(task_id)

    async def close(self):
        for worker in self.workers.values():
            if not worker.done():
                worker.cancel()
        await asyncio.gather(*self.workers.values(), return_exceptions=True)
        unsubscribe(self.record_event)
        self.started = False
