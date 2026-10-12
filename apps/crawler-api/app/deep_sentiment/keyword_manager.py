"""
关键词管理器 — 从 BroadTopicExtraction 获取关键词并分配给爬虫使用。
"""

from datetime import date
from typing import List, Dict, Optional
from loguru import logger

from app.db.repository.topic_repository import TopicRepository
from app.db.session import get_session
from app.config import DEFAULT_MAX_KEYWORDS


class KeywordManager:
    """关键词管理器 — 从数据库读取话题关键词供爬虫使用"""

    def __init__(self):
        self._topic_repository = TopicRepository(get_session)

    async def get_latest_keywords(
        self, target_date: date = None, max_keywords: int = None,
    ) -> List[str]:
        """获取最新的爬取关键词"""
        if target_date is None:
            target_date = date.today()
        if max_keywords is None:
            max_keywords = DEFAULT_MAX_KEYWORDS

        try:
            topics_data = await self._topic_repository.get_daily_topics(target_date)

            if not topics_data:
                logger.warning(f"没有找到 {target_date} 的话题数据")
                return []

            keywords = topics_data.get("keywords", [])
            if not keywords:
                logger.warning(f"{target_date} 的话题数据中没有关键词")
                return []

            logger.info(f"从 {target_date} 获取到 {len(keywords)} 个关键词")
            return keywords[:max_keywords]

        except Exception as e:
            logger.exception(f"获取关键词失败: {e}")
            return []

    async def get_crawling_summary(self, target_date: date = None) -> Dict:
        """获取爬取摘要信息"""
        if target_date is None:
            target_date = date.today()

        try:
            topics_data = await self._topic_repository.get_daily_topics(target_date)

            if not topics_data:
                return {
                    "has_data": False,
                    "date": target_date.isoformat(),
                    "keywords_count": 0,
                    "summary": "",
                    "message": f"没有找到 {target_date} 的话题数据",
                }

            keywords = topics_data.get("keywords", [])
            summary = topics_data.get("summary", topics_data.get("topic_description", ""))

            return {
                "has_data": True,
                "date": target_date.isoformat(),
                "keywords_count": len(keywords),
                "summary": summary,
                "keywords": keywords,
            }

        except Exception as e:
            logger.exception(f"获取爬取摘要失败: {e}")
            return {"has_data": False, "error": str(e)}

    async def get_keywords_for_platform(
        self, platform: str, target_date: date = None, max_keywords: int = None,
    ) -> List[str]:
        """获取指定平台的关键词（当前所有平台共用同一套关键词）"""
        return await self.get_latest_keywords(target_date, max_keywords)
