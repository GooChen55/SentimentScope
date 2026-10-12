#!/usr/bin/env python3
"""
数据库初始化 — 创建爬虫业务表 + MediaCrawler 内容表。

使用方式:
    python -m crawler.app.db.init_db
    python crawler/app/db/init_db.py
"""

import asyncio
from urllib.parse import quote_plus

from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from app.db.models import Base as CrawlerBase


def _build_database_url() -> str:
    password = quote_plus(DB_PASSWORD)
    return f"mysql+aiomysql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"



async def main() -> None:
    database_url = _build_database_url()
    engine = create_async_engine(database_url, pool_pre_ping=True, pool_recycle=1800)

    # 1. 创建爬虫业务表（daily_news、daily_topics）
    async with engine.begin() as conn:
        await conn.run_sync(CrawlerBase.metadata.create_all)
    logger.info("[init_db] 爬虫业务表创建完成 (daily_news, daily_topics)")

    # 2. 使用保存的兼容表结构，避免导入旧爬虫执行模块。
    try:
        from app.db.content_schema import Base as MediaCrawlerBase
        async with engine.begin() as conn:
            await conn.run_sync(MediaCrawlerBase.metadata.create_all)
        logger.info("[init_db] MediaCrawler 内容表创建完成")
    except ImportError as e:
        logger.warning(f"[init_db] 无法导入 MediaCrawler 模型，跳过内容表创建: {e}")


    await engine.dispose()
    logger.info("[init_db] 数据库初始化完成")


if __name__ == "__main__":
    asyncio.run(main())
