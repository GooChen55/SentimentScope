"""
新闻数据仓库 — 每日热点新闻的存储和查询。
"""

from datetime import date, datetime
from typing import Callable, List, Dict, Optional, Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.models import DailyNews


class NewsRepository:
    """新闻数据仓库"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    async def save_daily_news(self,
                              news_data: List[Dict[str, Any]],
                              crawl_date: Optional[date] = None) -> int:
        """保存每日新闻数据，如果当天已有数据则覆盖"""

        if crawl_date is None:
            crawl_date = date.today()

        current_timestamp = int(datetime.now().timestamp())

        async with self._session_factory() as session:
            result = await session.execute(
                delete(DailyNews).where(DailyNews.crawl_date == crawl_date)
            )
            if result.rowcount > 0:
                logger.info(f"删除了当天已有的 {result.rowcount} 条新闻记录")

            saved_count = 0
            for news_item in news_data:
                try:
                    news_id = f"{news_item.get("id")}_{crawl_date.strftime('%Y%m%d')}"
                    title = (news_item.get("title") or "").strip()
                    if len(title) > 300:
                        title = title[:300]

                    news = DailyNews(
                        news_id=news_id,
                        source_platform=news_item.get("source", "unknown"),
                        title=title,
                        url=news_item.get("url", ""),
                        crawl_date=crawl_date,
                        rank_position=news_item.get("rank"),
                        add_ts=current_timestamp,
                        last_modify_ts=current_timestamp,
                    )
                    session.add(news)
                    saved_count += 1
                except Exception as e:
                    logger.exception(f"保存单条新闻失败: {e}")
                    continue

            await session.commit()
            logger.info(f"成功保存 {saved_count} 条新闻记录")
            return saved_count

    async def get_daily_news(self, crawl_date: date) -> List[DailyNews]:
        """获取每日新闻数据"""
        async with self._session_factory() as session:
            result = await session.execute(
                select(DailyNews)
                .where(DailyNews.crawl_date == crawl_date)
                .order_by(DailyNews.rank_position.asc())
            )
            return result.scalars().all()
