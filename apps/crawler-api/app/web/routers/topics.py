# -*- coding: utf-8 -*-
"""话题相关路由"""

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.db.repository.topic_repository import TopicRepository
from app.db.session import get_session
from app.web.schemas import TopicSummary, TopicDetail

router = APIRouter(prefix="/api/topics", tags=["topics"])


def _get_repo() -> TopicRepository:
    return TopicRepository(get_session)


@router.get("", response_model=list[TopicSummary], description="获取最近三天话题")
async def list_topics(days: int = Query(default=3, ge=1, le=90)):
    repo = _get_repo()
    topics = await repo.get_recent_topics(days)
    return [
        TopicSummary(
            extract_date=str(t["extract_date"]),
            keywords_count=len(t.get("keywords", [])),
            summary=t.get("summary") or t.get("topic_description"),
            keywords=t.get("keywords", []),
        )
        for t in topics
    ]


@router.get("/{target_date}", response_model=TopicDetail, description="")
async def get_topic(target_date: str):
    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")

    repo = _get_repo()
    topic = await repo.get_daily_topics(parsed_date)
    if not topic:
        raise HTTPException(status_code=404, detail="未找到该日期的话题数据")

    return TopicDetail(
        extract_date=str(topic["extract_date"]),
        keywords=topic.get("keywords", []),
        summary=topic.get("summary") or topic.get("topic_description"),
        created_at=str(topic.get("created_at", "")),
    )


@router.get("/{target_date}/keywords", description="获取指定日期的话题")
async def get_keywords(target_date: str):
    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")

    repo = _get_repo()
    topic = await repo.get_daily_topics(parsed_date)
    if not topic:
        return {"date": str(parsed_date), "keywords": [], "count": 0}

    keywords = topic.get("keywords", [])
    return {"date": str(parsed_date), "keywords": keywords, "count": len(keywords)}
