"""Pinned engine, isolated interpreter, replayable output and accurate counts."""
import asyncio
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from app.config import DEFAULT_MAX_NOTES, DEFAULT_LOGIN_TYPE, SUPPORTED_PLATFORMS, CRAWLER_HEADLESS, CRAWLER_ENABLE_CDP_MODE
from app.deep_sentiment.ingest import ingest_records
from app.paths import DATA_ROOT, PROFILE_ROOT

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT / "crawler-engine.lock.json").read_text(encoding="utf-8"))
MEDIACRAWLER_PATH = (ROOT / MANIFEST["directory"]).resolve()

def engine_info():
    revision = subprocess.check_output(["git", "-C", str(MEDIACRAWLER_PATH), "rev-parse", "HEAD"], text=True).strip()
    python = MEDIACRAWLER_PATH / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    clean = subprocess.run(["git", "-C", str(MEDIACRAWLER_PATH), "diff", "--quiet", "HEAD"], capture_output=True).returncode == 0
    return {**MANIFEST, "installed_revision": revision, "ready": revision == MANIFEST["revision"] and python.exists() and clean}

class PlatformCrawler:
    def __init__(self):
        self.crawl_stats = {}

    async def _run_crawler_async(self, platform, keywords, login_type, max_notes, progress_context=None):
        if platform not in SUPPORTED_PLATFORMS or not keywords:
            raise ValueError("请选择支持的平台并填写关键词")
        if not engine_info()["ready"]:
            raise RuntimeError("爬虫版本或独立环境不匹配，请运行环境初始化脚本")
        started = time.monotonic()
        output = DATA_ROOT / "crawl-runs" / uuid.uuid4().hex
        output.mkdir(parents=True)
        python = MEDIACRAWLER_PATH / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        request = {"engine_path": str(MEDIACRAWLER_PATH), "platform": platform,
                   "keywords": keywords, "login_type": login_type, "max_notes": max_notes,
                   "output_path": str(output), "profile_root": str(PROFILE_ROOT),
                   "headless": CRAWLER_HEADLESS, "cdp": CRAWLER_ENABLE_CDP_MODE}
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
        with (output / "engine.log").open("w", encoding="utf-8") as log:
            proc = await asyncio.create_subprocess_exec(str(python), str(ROOT / "tools/engine_worker.py"),
                cwd=str(MEDIACRAWLER_PATH), env=env, stdin=asyncio.subprocess.PIPE, stdout=log, stderr=log)
            try:
                communication = asyncio.create_task(proc.communicate(json.dumps(request).encode("utf-8")))
                deadline = time.monotonic() + 1800
                previous = None
                from app.deep_sentiment.live_progress import live_counts, live_stage
                from app.web.services.crawl_worker import _emit
                progress_context = progress_context or {}
                while not communication.done():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise asyncio.TimeoutError()
                    await asyncio.wait({communication}, timeout=min(2, remaining))
                    notes, comments = await asyncio.to_thread(live_counts, output, platform)
                    stage = await asyncio.to_thread(live_stage, output, notes, comments)
                    current = (notes, comments, stage)
                    if current != previous:
                        _emit({"type": "stage", "stage": stage,
                               "message": f"{platform}：{stage}，已读取内容 {notes} 条、评论 {comments} 条；采集结束后统一入库"})
                        previous = current
                    _emit({"type": "progress", "platform": platform,
                           "notes": progress_context.get("notes_offset", 0) + notes,
                           "comments": progress_context.get("comments_offset", 0) + comments,
                           "keywords_total": progress_context.get("total_platforms", 1),
                           "keywords_done": len(progress_context.get("completed", [])),
                           "platforms_completed": progress_context.get("completed", [])})
                await communication
            except (asyncio.TimeoutError, asyncio.CancelledError):
                if proc.returncode is None:
                    if os.name == "nt":
                        await asyncio.to_thread(subprocess.run, ["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
                    else:
                        proc.terminate()
                    await proc.wait()
                await asyncio.gather(communication, return_exceptions=True)
                raise
        counts = await ingest_records(output, platform)
        result = {"platform": platform, "keywords_count": len(keywords), **counts,
                  "duration_seconds": round(time.monotonic() - started, 1), "output_directory": str(output),
                  "engine_revision": MANIFEST["revision"], "exit_code": proc.returncode,
                  "success": proc.returncode == 0 and counts["notes_count"] > 0}
        if not result["success"]:
            result["error"] = "采集进程失败，已保存可用数据；请查看本地 engine.log" if proc.returncode else "未采集到内容，请检查登录状态、关键词及平台访问限制"
            status_file = output / "engine-status.json"
            if status_file.exists():
                result.update(json.loads(status_file.read_text(encoding="utf-8")))
            elif "TargetClosedError" in (output / "engine.log").read_text(encoding="utf-8", errors="replace"):
                result.update(error_code="browser_closed", error="采集浏览器连接已关闭。扫码后请保持浏览器打开，等待采集完成后再关闭。")
            from app.web.services.crawl_worker import _emit
            _emit({"type": "log", "level": "error", "message": result["error"]})
        self.crawl_stats[platform] = result
        return result

    def run_crawler(self, platform, keywords, login_type=None, max_notes=None):
        return asyncio.run(self._run_crawler_async(platform, keywords, login_type or DEFAULT_LOGIN_TYPE, max_notes or DEFAULT_MAX_NOTES))

    async def run_multi_platform_crawl_by_keywords(self, keywords, platforms, login_type=None, max_notes_per_keyword=None):
        stats = {"total_keywords": len(keywords), "total_platforms": len(platforms),
                 "total_tasks": len(platforms), "successful_tasks": 0, "failed_tasks": 0,
                 "total_notes": 0, "total_comments": 0, "keyword_results": {}, "platform_summary": {}}
        for platform in platforms:
            from app.web.services.crawl_worker import _emit
            _emit({"type": "stage", "stage": "crawling", "message": f"正在采集 {platform}，需要登录时请在弹出的浏览器完成"})
            try:
                result = await self._run_crawler_async(platform, keywords, login_type or DEFAULT_LOGIN_TYPE, max_notes_per_keyword or DEFAULT_MAX_NOTES,
                    {"notes_offset": stats["total_notes"], "comments_offset": stats["total_comments"],
                     "total_platforms": len(platforms), "completed": list(stats["platform_summary"])})
            except Exception as exc:
                result = {"success": False, "platform": platform, "error": f"采集或入库失败：{type(exc).__name__}，请查看服务日志"}
            stats["successful_tasks" if result["success"] else "failed_tasks"] += 1
            stats["total_notes"] += result.get("notes_count", 0)
            stats["total_comments"] += result.get("comments_count", 0)
            stats["platform_summary"][platform] = result
            _emit({"type": "progress", "platform": platform, "keywords_total": len(platforms),
                   "keywords_done": len(stats["platform_summary"]), "notes": stats["total_notes"],
                   "comments": stats["total_comments"],
                   "platforms_completed": list(stats["platform_summary"])})
        return stats

    def get_crawl_statistics(self):
        return {"platforms_crawled": list(self.crawl_stats), "total_platforms": len(self.crawl_stats), "detailed_stats": self.crawl_stats}
