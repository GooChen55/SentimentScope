# -*- coding: utf-8 -*-
"""
爬虫工作进程入口 — 在子进程中执行，通过 stdout 输出 JSON 进度事件。

用法: python crawl_worker.py '<json_config>'
"""

import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict


def _emit(event: Dict[str, Any]) -> None:
    """向 stdout 输出一行 JSON 事件（被父进程通过管道读取）"""
    sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _now_iso() -> str:
    return datetime.now().isoformat()


def run_worker(config: Dict[str, Any]) -> None:
    task_type = config["type"]
    target_date = config.get("target_date")
    platforms = config.get("platforms")
    sources = config.get("sources")
    max_keywords = config.get("max_keywords")
    max_notes = config.get("max_notes")
    login_type = config.get("login_type")

    if task_type == "web_page":
        import asyncio
        from app.web.services.web_collector import collect_pages
        result = asyncio.run(collect_pages(config["urls"], config["topic"]))
        _emit({"type": "result", "success": result["success"], "data": result,
               "error": result.get("error"), "timestamp": _now_iso()})
        return

    _emit({"type": "stage", "stage": "初始化", "message": "正在初始化爬虫环境...", "timestamp": _now_iso()})

    from app.pipeline import CrawlerPipeline
    import asyncio

    pipeline = CrawlerPipeline()

    if task_type == "broad_topic":
        _emit({"type": "stage", "stage": "收集热点新闻", "message": "正在收集热点新闻...", "timestamp": _now_iso()})

        async def _run():
            try:
                return await pipeline.run_broad_topic(news_sources=sources, max_keywords=max_keywords)
            finally:
                from app.db.session import dispose_engine
                await dispose_engine()

        result = asyncio.run(_run())

    elif task_type == "deep_sentiment":
        _emit({"type": "stage", "stage": "crawling", "message": "正在从数据库读取关键词并爬取...", "timestamp": _now_iso()})

        from datetime import date as date_type
        td = None
        if target_date:
            td = date_type.fromisoformat(target_date)

        async def _run():
            try:
                return await pipeline.run_deep_sentiment(td, platforms, max_keywords, max_notes, login_type, config.get("keywords"))
            finally:
                from app.db.session import dispose_engine
                await dispose_engine()

        result = asyncio.run(_run())

    elif task_type == "pipeline":
        from datetime import date as date_type
        td = None
        if target_date:
            td = date_type.fromisoformat(target_date)

        _emit({"type": "stage", "stage": "news_collection", "message": "【流水线】第一步：收集热点新闻...", "timestamp": _now_iso()})

        async def _run_broad():
            try:
                return await pipeline.run_broad_topic(news_sources=sources, max_keywords=max_keywords)
            finally:
                from app.db.session import dispose_engine
                await dispose_engine()

        topic_result = asyncio.run(_run_broad())

        if not topic_result.get("success"):
            result = {"success": False, "error": "话题提取失败", "topic_result": topic_result}
        else:
            _emit({"type": "stage", "stage": "crawling", "message": "【流水线】第二步：读取关键词并开始平台爬取...", "timestamp": _now_iso()})

            async def _run_deep():
                try:
                    return await pipeline.run_deep_sentiment(td, platforms, max_keywords, max_notes, login_type)
                finally:
                    from app.db.session import dispose_engine
                    await dispose_engine()

            crawl_result = asyncio.run(_run_deep())
            result = {
                "success": crawl_result.get("success", False),
                "date": td.isoformat() if td else None,
                "topic_result": topic_result,
                "crawl_result": crawl_result,
            }

    else:
        _emit({"type": "result", "success": False, "error": f"未知任务类型: {task_type}", "timestamp": _now_iso()})
        sys.exit(1)

    success = result.get("success", False)
    error = result.get("error") if not success else None

    _emit({
        "type": "result",
        "success": success,
        "data": result,
        "error": error,
        "timestamp": _now_iso(),
    })



if __name__ == "__main__":
    _emit({
        "type": "result",
        "success": False,
        "error": traceback.format_exc(),
        "timestamp": _now_iso(),
    })


    # if len(sys.argv) < 2:
    #     print(json.dumps({"type": "result", "success": False, "error": "缺少配置参数"}))
    #     sys.exit(1)
    # try:
    #     config = json.loads(sys.argv[1])
    #     run_worker(config)
    # except Exception:
    #     _emit({
    #         "type": "result",
    #         "success": False,
    #         "error": traceback.format_exc(),
    #         "timestamp": _now_iso(),
    #     })
    #     sys.exit(1)
