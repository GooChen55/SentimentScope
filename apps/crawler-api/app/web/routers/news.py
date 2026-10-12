# -*- coding: utf-8 -*-
"""新闻相关路由"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.broad_topic.news.fetcher import SOURCE_NAMES
from app.db.repository.news_repository import NewsRepository
from app.db.session import get_session
from app.web.schemas import NewsItem, NewsResponse, NewsSource

router = APIRouter(prefix="/api/news", tags=["news"])


def _get_repo() -> NewsRepository:
    return NewsRepository(get_session)


@router.get("/sources", response_model=list[NewsSource])
async def list_sources():
    return [NewsSource(value=k, label=v) for k, v in SOURCE_NAMES.items()]


@router.get("", response_model=NewsResponse)
async def list_news(
    target_date: Optional[str] = Query(default=None, description="日期 YYYY-MM-DD，默认今天"),
    source: Optional[str] = Query(default=None, description="按新闻源筛选"),
):
    if target_date is None:
        dt = date.today()
    else:
        try:
            dt = date.fromisoformat(target_date)
        except ValueError:
            dt = date.today()
    target_date = dt.isoformat()

    repo = _get_repo()
    news_list = await repo.get_daily_news(dt)

    if source:
        news_list = [n for n in news_list if n.source_platform == source]

    items = [
        NewsItem(
            news_id=n.news_id or "",
            source_platform=n.source_platform or "",
            title=n.title or "",
            url=n.url or "",
            rank_position=n.rank_position or 0,
            crawl_date=str(n.crawl_date or target_date),
        )
        for n in news_list
    ]

    return NewsResponse(date=target_date, total=len(items), news=items)
