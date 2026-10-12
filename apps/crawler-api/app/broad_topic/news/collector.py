"""
新闻收集器 — 数据处理和存储编排。
"""

from datetime import date, datetime
from typing import List, Dict, Optional, Any
from loguru import logger

from app.broad_topic.news.fetcher import SOURCE_NAMES, NewApiFetcher
from app.db.repository.news_repository import NewsRepository
from app.db.session import get_session


class NewsCollector:
    """新闻收集器 — 数据处理和存储编排"""

    def __init__(self):
        self._news_fetcher = NewApiFetcher()
        self._news_repository = NewsRepository(get_session)

    async def fetch_and_save_daily_news(self, sources: Optional[List[str]] = None) -> Dict:
        """收集并保存每日热点新闻"""
        if sources is None:
            sources = list(SOURCE_NAMES.keys())

        try:
            fetched_result = await self._news_fetcher.fetch_popular_news(sources)
            processed_result = self._process_news_results(fetched_result)

            if processed_result["news_item_list"]:
                saved_count = await self._news_repository.save_daily_news(
                    processed_result["news_item_list"], date.today()
                )
                processed_result["saved_count"] = saved_count

            logger.info(
                f"总新闻源: {processed_result['total_sources']}, "
                f"成功源数: {processed_result['successful_sources']}, "
                f"总新闻数: {processed_result['total_news']}, "
                f"已保存数: {processed_result['saved_count']}" if "saved_count" in processed_result else ""
            )
            return processed_result

        except Exception as e:
            logger.exception(f"收集新闻失败: {e}")
            return {"success": False, "error": str(e), "news_item_list": [], "total_news": 0}

    async def get_today_news(self) -> List[Dict[str, Any] | None]:
        """获取今天的新闻"""
        try:
            news_list = await self._news_repository.get_daily_news(date.today())
            return [
                {
                    "news_id": new.news_id,
                    "source_platform": new.source_platform,
                    "title": new.title,
                    "url": new.url,
                    "crawl_date": new.crawl_date,
                    "rank_position": new.rank_position,
                }
                for new in news_list
            ]
        except Exception as e:
            logger.exception(f"获取今日新闻失败: {e}")
            return []

    def _process_news_results(self, fetched_results: List[Dict]) -> Dict:
        """处理新闻获取结果"""
        news_item_list = []
        successful_sources = 0
        total_news = 0

        for result in fetched_results:
            source = result["source"]
            status = result["status"]
            if status == "success":
                successful_sources += 1
                data = result["data"]
                if "items" in data and isinstance(data["items"], list):
                    source_news_count = len(data["items"])
                    total_news += source_news_count
                    for i, news_item in enumerate(data["items"], 1):
                        processed = self._process_news_item(news_item, source, i)
                        if processed:
                            news_item_list.append(processed)

        return {
            "success": True,
            "news_item_list": news_item_list,
            "total_sources": len(fetched_results),
            "successful_sources": successful_sources,
            "total_news": total_news,
            "collection_time": datetime.now().isoformat(),
        }

    @staticmethod
    def _process_news_item(item: Dict[str, Any] | Any, source: str, rank: int) -> Optional[Dict[str, Any]]:
        try:
            if isinstance(item, dict):
                title = item.get("title", "无标题").strip()
                url = item.get("url", "")
                news_id = f"{source}_{item.get('id', f'rank_{rank}')}"
                return {"id": news_id, "title": title, "url": url, "source": source, "rank": rank}
            else:
                title = str(item)[:100] if len(str(item)) > 100 else str(item)
                return {"id": f"{source}_rank_{rank}", "title": title, "url": "", "source": source, "rank": rank}
        except Exception as e:
            logger.exception(f"处理新闻项失败: {e}")
            return None


async def main():
    collector = NewsCollector()
    res = await collector.fetch_and_save_daily_news()
    print(res)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
