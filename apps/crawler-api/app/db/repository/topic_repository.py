"""
话题数据仓库 — 每日话题分析的存储和查询。
"""

import json
from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.models import DailyNews, DailyTopic


class TopicRepository:
    """话题数据仓库"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    async def save_daily_topics(
            self, keywords: List[str], summary: str, extract_date: date = None
    ) -> bool:
        """保存每日话题分析"""
        if not extract_date:
            extract_date = date.today()

        current_timestamp = int(datetime.now().timestamp())
        keywords_json = json.dumps(keywords, ensure_ascii=False)
        topic_id = f"每日新闻分析_{extract_date.strftime('%Y%m%d')}"

        async with self._session_factory() as session:
            result = await session.execute(
                select(DailyTopic).where(
                    DailyTopic.extract_date == extract_date,
                    DailyTopic.topic_id == topic_id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.keywords = keywords_json
                existing.topic_description = summary
                existing.add_ts = current_timestamp
                existing.last_modify_ts = current_timestamp
                existing.topic_name = "每日新闻分析"
                logger.info(f"更新了 {extract_date} 的话题分析")
            else:
                topic = DailyTopic(
                    extract_date=extract_date,
                    topic_id=topic_id,
                    topic_name="每日新闻分析",
                    keywords=keywords_json,
                    topic_description=summary,
                    add_ts=current_timestamp,
                    last_modify_ts=current_timestamp,
                )
                session.add(topic)
                logger.info(f"保存了 {extract_date} 的话题分析")

            await session.commit()
            return True

    async def get_daily_topics(self, extract_date: date = None) -> Optional[Dict]:
        """获取每日话题分析"""
        if not extract_date:
            extract_date = date.today()

        async with self._session_factory() as session:
            result = await session.execute(
                select(DailyTopic).where(DailyTopic.extract_date == extract_date)
            )
            row = result.scalar_one_or_none()

        if row is None:
            return None

        return {
            "id": row.id,
            "topic_id": row.topic_id,
            "topic_name": row.topic_name,
            "topic_description": row.topic_description,
            "keywords": json.loads(row.keywords) if row.keywords else [],
            "extract_date": row.extract_date,
            "relevance_score": row.relevance_score,
            "news_count": row.news_count,
            "processing_status": row.processing_status,
            "add_ts": row.add_ts,
            "last_modify_ts": row.last_modify_ts,
        }

    async def get_recent_topics(self, days: int = 7) -> List[Dict]:
        """获取最近几天的话题分析"""
        start_date = date.today() - timedelta(days=days)

        async with self._session_factory() as session:
            result = await session.execute(
                select(DailyTopic)
                .where(DailyTopic.extract_date >= start_date)
                .order_by(DailyTopic.extract_date.desc())
            )
            rows = result.scalars().all()

        return [
            {
                "id": r.id,
                "topic_id": r.topic_id,
                "topic_name": r.topic_name,
                "topic_description": r.topic_description,
                "keywords": json.loads(r.keywords) if r.keywords else [],
                "extract_date": r.extract_date,
                "relevance_score": r.relevance_score,
                "news_count": r.news_count,
                "processing_status": r.processing_status,
                "add_ts": r.add_ts,
                "last_modify_ts": r.last_modify_ts,
                "summary": r.topic_description,
            }
            for r in rows
        ]

    async def get_summary_stats(self, days: int = 7) -> Dict:
        """获取统计摘要"""
        start_date = date.today() - timedelta(days=days)

        async with self._session_factory() as session:
            news_stats = await session.execute(
                select(
                    DailyNews.crawl_date,
                    func.count().label("news_count"),
                    func.count(func.distinct(DailyNews.source_platform)).label("platforms_count"),
                )
                .where(DailyNews.crawl_date >= start_date)
                .group_by(DailyNews.crawl_date)
                .order_by(DailyNews.crawl_date.desc())
            )
            news_rows = news_stats.all()

            topics_stats = await session.execute(
                select(
                    DailyTopic.extract_date,
                    DailyTopic.keywords,
                    func.char_length(DailyTopic.topic_description).label("summary_length"),
                )
                .where(DailyTopic.extract_date >= start_date)
                .order_by(DailyTopic.extract_date.desc())
            )
            topic_rows = topics_stats.all()

        return {"news_stats": news_rows, "topics_stats": topic_rows}


if __name__ == '__main__':
    start_date = date.today() - timedelta(days=7)

    print(start_date)
