# -*- coding: utf-8 -*-
"""
FastAPI Web 服务 — 爬虫前端 API 入口。

启动方式:
    uv run python -m app.web.main
    uv run uvicorn app.web.main:app --host 0.0.0.0 --port 8080
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import PROJECT_ROOT


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[web] 正在启动 Web 服务...")
    from app.web.routers.crawl import init_task_manager
    manager = init_task_manager()
    logger.info("[web] TaskManager 已初始化")
    yield
    await manager.shutdown()
    from app.db.session import dispose_engine
    await dispose_engine()
    logger.info("[web] Web 服务已关闭")


app = FastAPI(
    title="SentimentScope · 采集 API",
    description="舆情研判平台的社交内容与公开网页采集服务",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== REST 路由 ======================

from app.web.routers import crawl, topics, news, platforms, websocket

app.include_router(crawl.router)
app.include_router(topics.router)
app.include_router(news.router)
app.include_router(platforms.router)
app.include_router(websocket.router)


# ====================== 健康检查 ======================

@app.get("/api/health")
async def health():
    try:
        from sqlalchemy import text
        from app.db.session import get_session
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db_connected": db_ok}


@app.get("/")
async def root():
    return {
        "message": "SentimentScope 采集 API 已启动",
        "docs": "/docs",
        "frontend": "http://127.0.0.1:5173",
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8083"))
    logger.info(f"启动 Web 服务: http://{host}:{port}")
    uvicorn.run("app.web.main:app", host=host, port=9000, reload=True)
