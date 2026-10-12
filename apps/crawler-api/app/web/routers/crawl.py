# -*- coding: utf-8 -*-
"""爬虫操作路由 — 数据库初始化、任务启动/停止/查询"""

import time as _time
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.config import (
    SUPPORTED_PLATFORMS, DEFAULT_MAX_KEYWORDS, DEFAULT_MAX_NOTES, DEFAULT_LOGIN_TYPE,
)
from app.db.session import create_db_engine, save_db_config, dispose_engine
from app.web.schemas import (
    TaskType,
    DbInitRequest,
    DbInitResponse,
    CrawlStartRequest,
    TaskCreatedResponse,
    TaskListResponse,
)
from app.web.services.task_manager import TaskManager

router = APIRouter(prefix="/api", tags=["crawl"])
_task_manager: TaskManager = None  # 由 main.py 在启动时注入


def init_task_manager():
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ====================== 数据库初始化 ======================

@router.post("/init-db", response_model=DbInitResponse)
async def init_database(req: DbInitRequest):
    start = _time.time()

    engine = create_db_engine(
        host=req.host, port=req.port, user=req.user,
        password=req.password, db_name=req.db_name, charset=req.charset,
    )

    tables_created = []

    try:
        from app.db.models import Base as CrawlerBase
        async with engine.begin() as conn:
            await conn.run_sync(CrawlerBase.metadata.create_all)
        tables_created.append("daily_news")
        tables_created.append("daily_topics")
        logger.info("[init-db] 爬虫业务表创建完成")
    except Exception as e:
        elapsed = round(_time.time() - start, 2)
        await engine.dispose()
        return DbInitResponse(
            success=False,
            message="爬虫业务表创建失败",
            tables_created=tables_created,
            elapsed_seconds=elapsed,
            error=str(e),
        )

    try:
        from app.db.content_schema import Base as MediaCrawlerBase
        async with engine.begin() as conn:
            await conn.run_sync(MediaCrawlerBase.metadata.create_all)
        tables_created.append("media_crawler_correlation_table")
        logger.info("[init-db] MediaCrawler 相关表创建完成")
    except ImportError as e:
        await engine.dispose()
        return DbInitResponse(success=False, message="内容表模型导入失败", tables_created=tables_created,
                              elapsed_seconds=round(_time.time() - start, 2), error="请检查旧表兼容模型安装路径")
    except Exception as e:
        await engine.dispose()
        return DbInitResponse(success=False, message="内容表创建失败", tables_created=tables_created,
                              elapsed_seconds=round(_time.time() - start, 2), error="请检查数据库权限及表结构")

    await engine.dispose()

    # 持久化数据库信息
    save_db_config(
        host=req.host, port=req.port, user=req.user,
        password=req.password, db_name=req.db_name, charset=req.charset,
    )
    await dispose_engine()

    elapsed = round(_time.time() - start, 2)

    return DbInitResponse(
        success=True,
        message=f"数据库初始化完成，共创建 {len(tables_created)} 类表",
        tables_created=tables_created,
        elapsed_seconds=elapsed,
    )


# ====================== 爬虫任务启动 ======================

def _resolve_request(req: CrawlStartRequest) -> dict:
    """解析请求参数，应用默认值。"""
    platforms = req.platforms if req.platforms else None
    if platforms is None:
        platforms = ["wb", "dy"]
    if any(p not in SUPPORTED_PLATFORMS for p in platforms):
        raise HTTPException(422, "包含不支持的平台")
    if req.login_type and req.login_type not in ("qrcode", "phone", "cookie"):
        raise HTTPException(422, "登录方式不支持")
    if req.target_date:
        try:
            date.fromisoformat(req.target_date)
        except ValueError:
            raise HTTPException(422, "日期格式不正确") from None

    return {
        "target_date": req.target_date or date.today().isoformat(),
        "platforms": platforms,
        "sources": req.sources,
        "max_keywords": req.max_keywords or DEFAULT_MAX_KEYWORDS,
        "max_notes": req.max_notes or DEFAULT_MAX_NOTES,
        "login_type": req.login_type or DEFAULT_LOGIN_TYPE,
        "keywords": list(dict.fromkeys(k.strip() for k in req.keywords if k.strip()))[:req.max_keywords or DEFAULT_MAX_KEYWORDS],
        "urls": req.urls,
        "topic": req.topic.strip(),
    }


@router.post("/crawl/broad_topic", response_model=TaskCreatedResponse)
async def start_broad_topic(req: CrawlStartRequest = CrawlStartRequest()):
    config = _resolve_request(req)
    config.pop("platforms", None)
    config.pop("login_type", None)
    config.pop("max_notes", None)

    try:
        task_id = _task_manager.start_task(TaskType.broad_topic, config)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return TaskCreatedResponse(
        task_id=task_id, status="pending", type=TaskType.broad_topic, created_at=_now_iso()
    )


@router.post("/crawl/deep_sentiment", response_model=TaskCreatedResponse)
async def start_deep_sentiment(req: CrawlStartRequest = CrawlStartRequest()):

    config = _resolve_request(req)
    config.pop("sources", None)

    try:
        task_id = _task_manager.start_task(TaskType.deep_sentiment, config)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return TaskCreatedResponse(
        task_id=task_id, status="pending", type=TaskType.deep_sentiment, created_at=_now_iso()
    )


@router.post("/crawl/pipeline", response_model=TaskCreatedResponse)
async def start_pipeline(req: Optional[CrawlStartRequest] = None):
    if req is None:
        req = CrawlStartRequest()
    config = _resolve_request(req)

    try:
        task_id = _task_manager.start_task(TaskType.pipeline, config)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return TaskCreatedResponse(
        task_id=task_id, status="pending", type=TaskType.pipeline, created_at=_now_iso()
    )


# ====================== 任务查询与停止 ======================

@router.get("/crawl/engine")
async def get_engine():
    from app.deep_sentiment.platform_crawler import engine_info
    return engine_info()

@router.post("/crawl/web_page", response_model=TaskCreatedResponse)
async def start_web_page(req: CrawlStartRequest):
    if not req.urls or not req.topic.strip():
        raise HTTPException(422, "请填写网址和关联话题")
    config = _resolve_request(req)
    try:
        task_id = _task_manager.start_task(TaskType.web_page, config)
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from None
    return TaskCreatedResponse(task_id=task_id, status="pending", type=TaskType.web_page, created_at=_now_iso())

@router.get("/crawl/documents")
async def list_documents():
    from app.web.services.web_collector import list_documents
    return await list_documents()

@router.post("/crawl/tasks/{task_id}/retry", response_model=TaskCreatedResponse)
async def retry_task(task_id: str):
    try:
        new_id = _task_manager.retry_task(task_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from None
    return TaskCreatedResponse(task_id=new_id, status="pending", type=_task_manager.get_task(new_id).type, created_at=_now_iso())

@router.get("/crawl/tasks", response_model=TaskListResponse)
async def list_tasks(limit: int = 20):
    return _task_manager.list_tasks(limit)


@router.get("/crawl/tasks/{task_id}")
async def get_task(task_id: str):
    task = _task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.post("/crawl/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    ok = _task_manager.stop_task(task_id)
    if not ok:
        raise HTTPException(status_code=400, detail="无法停止该任务（可能已结束或不存在）")
    return {"success": True, "message": "已发送停止信号"}
